gcloud functions deploy ocr-upload \
  --runtime python39 \
  --trigger-resource YOUR_TRIGGER_BUCKET_NAME \
  --trigger-event google.storage.object.finalize \
  --entry-point parse_multipart \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT=YOUR_GCP_PROJECT_ID,EXTRACT_TOPIC=YOUR_EXTRACT_TOPIC_NAME