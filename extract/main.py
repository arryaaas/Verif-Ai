import os
import json
from google.cloud import vision
from google.cloud import pubsub_v1

def validate_event_data(event, param):
    """ Helper function that validates event data """

    value = event.get(param)

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

    print(f"Published message to {topic_path}")

def detect_text(bucket, filename):
    """ Helper function that detects text in images using Google Vision API """

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

    print(f"Extracted text from image {filename}: \n{text}")

    message = {
        "text": text,
        "filename": filename,
    }

    publish_message(message)

def process_image(data, context):
    """ Reads an uploaded image file from Google Cloud Storage """

    # Shows the type of event that occurred
    print(f"Event type: {context.event_type}")

    # Check if there is a bucket and name in the event data
    bucket = validate_event_data(data, "bucket")
    name = validate_event_data(data, "name")

    # Detect text in image
    detect_text(bucket, name)

    print(f"File {name} processed")
