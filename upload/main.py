import os
import cv2
import uuid
import tempfile
import functions_framework
from google.cloud import storage
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    """  Helper function that check if an extension is valid """

    return "." in filename and \
        filename.split(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_path(filename):
    """ Helper function that computes the filepath to save files to """

    file_name = secure_filename(filename)
    return os.path.join(tempfile.gettempdir(), file_name)

def preprocessing(file_path):
    """ Helper function that performs image pre-processing """

    img = cv2.imread(file_path)

    grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(grayscale, 127, 255, cv2.THRESH_TRUNC)

    cv2.imwrite(file_path, thresh)

def upload_blob(file_path):
    """ Uploads a file to the bucket """

    bucket_name = os.environ["BUCKET_NAME"]
    destination_blob = str(uuid.uuid4())

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)

    blob.upload_from_filename(file_path)

    print("File {} uploaded to {}".format(file_path, destination_blob))

@functions_framework.http
def parse_multipart(request):
    """ Parses a 'multipart/form-data' upload request """

    # Check if the request method is not post
    if request.method != "POST":
        return "Method not allowed"

    # Check if the post request has the file part
    if "file" not in request.files:
        return "No file part"

    file = request.files.get("file")

    # If the user does not select a file or submits an 
    # empty file without a filename
    if file.filename == "":
        return "No selected file"

    # Check if an extension is valid
    if not (file and allowed_file(file.filename)):
        return "Not Acceptable"

    file_path = get_file_path(file.filename)

    # Save file locally
    file.save(file_path)

    # image pre-processing
    preprocessing(file_path)

    # Upload file to Google Cloud Storage bucket
    upload_blob(file_path)

    # Clear temporary directory
    os.remove(file_path)

    return "Done!"