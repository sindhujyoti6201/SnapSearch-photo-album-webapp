import json
import boto3
import datetime
import requests
import urllib.parse

# Initialize AWS clients
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

print("DEPLOYING LAMBDA VIA CODEBUILD")
# OpenSearch Configuration
OPENSEARCH_ENDPOINT = "https://search-photos-2zcv2zir5roxmzmvvt7ezajhyi.us-east-1.es.amazonaws.com/photos/_doc"
OPENSEARCH_USERNAME = "yashavika"
OPENSEARCH_PASSWORD = "@Alipore1908"

def lambda_handler(event, context):
    print("Received Event:", json.dumps(event))

    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])

        print(f"\nProcessing file: s3://{bucket}/{key}")

        try:
            # Step 1: Get S3 Object Metadata
            s3_metadata = s3.head_object(Bucket=bucket, Key=key)
            content_type = s3_metadata.get('ContentType', '')

            print(f"Content-Type: {content_type}")

            # Step 2: Validate Content-Type
            if content_type not in ['image/jpeg', 'image/png']:
                print(f"[WARNING] Skipping unsupported Content-Type: {content_type} for file: {key}")
                continue

            # Step 3: Validate File Extension (Optional but extra safe)
            if not key.lower().endswith(('.jpg', '.jpeg', '.png')):
                print(f"[WARNING] Unsupported file extension for file: {key}")
                continue

            # Step 4: Call Rekognition
            rekog_response = rekognition.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                MaxLabels=10
            )

            detected_labels = [label['Name'] for label in rekog_response.get('Labels', [])]
            print(f"Detected Labels: {detected_labels}")

            # Step 5: Get custom metadata labels (if any)
            custom_labels = s3_metadata.get('Metadata', {}).get('customlabels', "")
            custom_labels_array = [lbl.strip() for lbl in custom_labels.split(',')] if custom_labels else []
            print(f"Custom Labels: {custom_labels_array}")

            # Step 6: Combine labels and remove duplicates
            all_labels = list(set(detected_labels + custom_labels_array))

            # Step 7: Prepare document for OpenSearch
            doc = {
                "objectKey": key,
                "bucket": bucket,
                "createdTimestamp": datetime.datetime.utcnow().isoformat(),
                "labels": all_labels
            }

            print(f"Indexing Document to OpenSearch:\n{json.dumps(doc)}")

            # Step 8: Send to OpenSearch
            headers = { "Content-Type": "application/json" }
            response = requests.post(
                OPENSEARCH_ENDPOINT,
                headers=headers,
                data=json.dumps(doc),
                auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD)
            )

            print(f"OpenSearch Response: {response.status_code} - {response.text}")

        except rekognition.exceptions.InvalidImageFormatException as e:
            print(f"[ERROR] Rekognition InvalidImageFormatException for {key}: {str(e)}")
        except Exception as e:
            print(f"[ERROR] Unexpected error processing {key}: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps('Lambda execution completed.')
    }
