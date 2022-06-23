gcloud functions deploy ocr-extract \
  --runtime python39 \
  --trigger-resource YOUR_TRIGGER_BUCKET_NAME \
  --trigger-event google.storage.object.finalize \
  --entry-point process_image \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT=YOUR_GCP_PROJECT_ID,EXTRACT_TOPIC=YOUR_EXTRACT_TOPIC_NAME
