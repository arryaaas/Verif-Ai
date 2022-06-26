import re
import json
import base64
from google.cloud import firestore

PATTERN = "nik|nama|tempat|tanggal|tgl|lahir|jenis|kelamin|gol|darah"

def validate_message(message, param):
    """ Helper function that validate message """

    value = message.get(param)

    if not value:
        raise ValueError(
            f"{param} is not provided. \
                Make sure you have property {param} in the request"
        )

    return value

def collect_details(text_annotations_group):
    """ Helper function that collect details from text annotations group """

    key = [
        "province", "district", "id_number", 
        "name", "place_date_of_birth", "gender"
    ]
    value = []

    for group in text_annotations_group[:6]:
        text = map(lambda z: z["description"], group)
        text = " ".join(text)
        text = re.sub(PATTERN, "", text, flags=re.IGNORECASE)
        text = text.replace(":", "").replace("/", "").replace(".", "") \
                .replace(" , ", ", ").replace(" - ", "-").strip()
        value.append(text)

    details = dict(zip(key, value))

    # Print message to logs
    print("Collect details from text annotations group")
    print(details)

    return details 

def save_details(details):
    """" Helper function that save details to Cloud Firestore """

    db = firestore.Client()
    doc_ref = db.collection("identity_card").document()
    doc_ref.set(details)

    # Print message to logs
    print(f"Save details to document {doc_ref.id} in identity card collection")

# Entry point function
def process_message(event, context):
    """ Background Cloud Function to be triggered by Pub/Sub """

    # Print message to logs
    print(f"This Function was triggered by {context.event_type} event")

    if event.get("data"):
        message_data = base64.b64decode(event["data"]).decode("utf-8")
        message = json.loads(message_data)
    else:
        raise ValueError("Data sector is missing in the Pub/Sub message")

    # Check if message contains data like text
    text_annotations_group = validate_message(message, "text_annotations_group")

    # Collect details from text
    details = collect_details(text_annotations_group)

    # Save details to Cloud Firestore
    save_details(details)

    # Print message to logs
    print("Cloud Functions (Cloud Pub/Sub Triggers) done!")
