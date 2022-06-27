import os
import json
from itertools import groupby
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
    topic_name = os.environ["RESULT_TOPIC"]

    message_data = json.dumps(message).encode("utf-8")

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)
    future = publisher.publish(topic_path, data=message_data)
    future.result()

    # Print message to logs
    print(f"Published message to {topic_path}")

def detect_text(bucket, filename):
    """ Helper function that detects text in images using Cloud Vision API """

    gcs_image_uri = f"gs://{bucket}/{filename}"

    image = vision.Image(
        source=vision.ImageSource(
            gcs_image_uri=gcs_image_uri
        )
    )

    vision_client = vision.ImageAnnotatorClient()
    text_detection_response = vision_client.text_detection(image=image)
    text_annotations = text_detection_response.text_annotations
    text_annotations.pop(0)

    text_annotations = list(
        map(
            lambda z: {
                "description": z.description,
                "vertex_x": z.bounding_poly.vertices[3].x,
                "vertex_y": int((z.bounding_poly.vertices[3].y) / 10)
            },
            text_annotations
        )
    )

    text_annotations = sorted(
        text_annotations, 
        key=lambda z: (z["vertex_y"], z["vertex_x"])
    )

    reference_vertex_y = 0
    for i in range(len(text_annotations)):
        vertices_y = [
            reference_vertex_y - 1,
            reference_vertex_y,
            reference_vertex_y + 1
        ]

        if text_annotations[i]["vertex_y"] not in vertices_y:
            reference_vertex_y = text_annotations[i]["vertex_y"]

        text_annotations[i]["vertex_y"] = reference_vertex_y

    text_annotations_group = []
    for key, value in groupby(text_annotations, key=lambda z: z["vertex_y"]):
        value = sorted(value, key=lambda z: z["vertex_x"])
        text_annotations_group.append((list(value)))

    for i in range(len(text_annotations_group)):
        if len(text_annotations_group[i]) == 1:
            text_annotations_group[i-1].append(text_annotations_group[i][0])

    text_annotations_group = list(
        filter(
            lambda z: len(z) != 1, text_annotations_group
        )
    )

    # Print message to logs
    print(f"Extracted text from image {filename}")
    print(text_annotations_group)

    return text_annotations_group

# Entry point function
def process_image(event, context):
    """ Background Cloud Function to be triggered by Cloud Storage """

    # Print message to logs
    print(f"This Function was triggered by {context.event_type} event")

    # Check if event contains data like bucket and name
    bucket = validate_message(event, "bucket")
    name = validate_message(event, "name")

    # Text detection using Cloud Vision API
    text_annotations_group = detect_text(bucket, name)

    message = {
        "text_annotations_group": text_annotations_group
    }

    # Publish message to Cloud Pub/Sub topics
    publish_message(message)

    # Print message to logs
    print("Cloud Functions (Cloud Storage Triggers) done!")
