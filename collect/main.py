import re
import json
import base64
from google.cloud import firestore

KEY_PATTERN = [
    "nik", "nama", "tempat/tgl lahir", "jenis kelamin", "gol. darah",
    "alamat", "rt/rw", "kel/desa", "kecamatan", "agama",
    "status perkawinan", "pekerjaan", "kewarganegaraan", "berlaku hingga"
]

PUNC_PATTERN = [
    ";", ":"
]

STOP_CONDITION = [
    "LAKI-LAKI", "PEREMPUAN"
]

def validate_message(message, param):
    """ Helper function that validate message """

    value = message.get(param)

    if not value:
        raise ValueError(
            f"{param} is not provided. \
                Make sure you have property {param} in the request"
        )

    return value

def collect_details(text):
    """ Helper function that collect details from extracted text """

    key = [
        "province", "district", "id_number", 
        "name", "place_date_of_birth", "gender"
    ]
    value = []
    text = text.split("\n")

    for i in text:
        i = re.sub("|".join(KEY_PATTERN), "", i, flags=re.IGNORECASE)
        i = re.sub("|".join(PUNC_PATTERN), "", i).strip()

        if i != "":
            value.append(i)

        # Collect details only up to gender
        if i in STOP_CONDITION:
            break

    # Concatenate names if the values consist of two lines
    if len(value) == 7:
        value[3] = f"{value[3]} {value[4]}"
        value.pop(4)

    details = dict(zip(key, value))

    # Print message to logs
    print(f"Collect details {details} from extracted text")

    return details 

def save_details(details):
    """" Helper function that save details to Cloud Firestore """

    db = firestore.Client()
    doc_ref = db.collection('identity_card').document()
    doc_ref.set(details)

    # Print message to logs
    print(f"Saving details to document {doc_ref.id} in identity card collection")

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
    text = validate_message(message, "text")

    # Collect details from text
    details = collect_details(text)

    # Save details to Cloud Firestore
    save_details(details)

    # Print message to logs
    print("Cloud Functions (Cloud Pub/Sub Triggers) done!")
