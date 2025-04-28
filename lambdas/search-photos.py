import json
import boto3
import base64
import requests
from requests.auth import HTTPBasicAuth

# OpenSearch setup
username = 'yashavika'
password = '@Alipore1908'
basicauth = HTTPBasicAuth(username, password)

opensearch_host = 'search-photos-2zcv2zir5roxmzmvvt7ezajhyi.us-east-1.es.amazonaws.com'
index = 'photos'

# Lex setup
bot_id = 'W9X7TFEIB7'
bot_alias_id = '3UMIP5FI7X'
locale_id = 'en_US'

lex_client = boto3.client('lexv2-runtime')
s3_client = boto3.client('s3')

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'PUT, GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, sessionId, x-api-key, x-amz-meta-customLabels, X-Amz-Date, X-Amz-Security-Token'
}

def lambda_handler(event, context):
    print("Search API Event:", json.dumps(event))

    query = event.get("queryStringParameters", {}).get("q", "")
    if not query:
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'message': 'No query provided'})
        }

    try:
        # Call Lex to interpret the query
        lex_response = lex_client.recognize_text(
            botId=bot_id,
            botAliasId=bot_alias_id,
            localeId=locale_id,
            sessionId="search-session",
            text=query
        )

        slots = lex_response.get("interpretations", [])[0].get("intent", {}).get("slots", {})
        keywords = []
        for slot in slots.values():
            if slot and "value" in slot:
                interpreted = slot["value"].get("interpretedValue", "")
                if interpreted:
                    keywords.extend([kw.strip().lower() for kw in interpreted.split(",") if kw.strip()])

        if not keywords:
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'No keywords extracted'})
            }

        # Build OpenSearch query
        must_clauses = [{"match": {"labels": keyword}} for keyword in keywords]
        search_query = {
            "query": {
                "bool": {
                    "must": must_clauses
                }
            }
        }

        # Search OpenSearch
        url = f"https://{opensearch_host}/{index}/_search"
        headers = {"Content-Type": "application/json"}

        response = requests.get(url, auth=basicauth, headers=headers, data=json.dumps(search_query))
        response.raise_for_status()
        search_results = response.json()

        hits = search_results['hits']['hits']
        if not hits:
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'No matching photos found'})
            }

        # Get top item
        top_photo = hits[0]['_source']
        bucket = top_photo.get('bucket')
        object_key = top_photo.get('objectKey')

        if not bucket or not object_key:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Missing bucket or object key in OpenSearch data'})
            }

        # Fetch image from S3
        s3_object = s3_client.get_object(Bucket=bucket, Key=object_key)
        image_content = s3_object['Body'].read()
        content_type = s3_object['ContentType']

        # Encode image as Base64
        encoded_image = base64.b64encode(image_content).decode('utf-8')

        result = {
            'filename': object_key,
            'bucket': bucket,
            'content_type': content_type,
            'image_data_base64': encoded_image
        }

        

        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps(result)
        }

    except Exception as e:
        print("Error:", str(e))
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'error': 'Search failed', 'details': str(e)})
        }
