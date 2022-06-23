gcloud functions deploy ocr-collect \
  --runtime python39 \
  --trigger-topic YOUR_EXTRACT_TOPIC_NAME \
  --entry-point process_message \
  --allow-unauthenticated 