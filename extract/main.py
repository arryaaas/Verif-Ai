import os
import json
from google.cloud import vision
from google.cloud import pubsub_v1

def validate_message(message, param):
    """ Helper function that validates messages """

    value = message.get(param)

    if not value:
        raise ValueError(
            f"{param} is not provided. \
                Make sure you have property {param} in the request"
        )

    return value

def publish_message(message):
    """ Helper function that publishes extraction results to Pub/Sub topics """

    project_id = os.environ["GCP_PROJECT"]
    topic_name = os.environ["EXTRACT_TOPIC"]

    message_data = json.dumps(message).encode("utf-8")

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)
    future = publisher.publish(topic_path, data=message_data)
    future.result()

    # Print message to logs
    print(f"Published message to {topic_path}")

def detect_text(bucket, filename):
    """ Helper function that detects text in images using Cloud Vision API """

    print(f"Looking for text in image {filename}")

    gcs_image_uri = f"gs://{bucket}/{filename}"

    image = vision.Image(
        source=vision.ImageSource(
            gcs_image_uri=gcs_image_uri
        )
    )

    vision_client = vision.ImageAnnotatorClient()
    text_detection_response = vision_client.text_detection(image=image)
    annotations = text_detection_response.text_annotations

    if len(annotations) > 0:
        text = annotations[0].description
    else:
        text = ""

    # Print message to logs
    print(f"Extracted text {text} from image {filename}")

    return text

# Entry point function
def process_image(event, context):
    """ Background Cloud Function to be triggered by Cloud Storage """

    # Print message to logs
    print(f"This Function was triggered by {context.event_type} event")

    # Check if event contains data like bucket and name
    bucket = validate_message(event, "bucket")
    name = validate_message(event, "name")

    # Text detection using Cloud Vision API
    text = detect_text(bucket, name)

    message = {
        "text": text
    }

    # Publish message to Cloud Pub/Sub topics
    publish_message(message)

    # Print message to logs
    print("Cloud Functions (Cloud Storage Triggers) done!")
