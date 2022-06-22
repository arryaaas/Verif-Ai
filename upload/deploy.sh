gcloud functions deploy ocr-upload \
  --runtime python39 \
  --trigger-http \
  --entry-point parse_multipart \
  --allow-unauthenticated \
  --set-env-vars BUCKET_NAME=YOUR_BUCKET_NAME