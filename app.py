import json
import os
import uuid

import boto3
from botocore.exceptions import ClientError

from flask import Flask, jsonify, request, make_response
import requests

app = Flask(__name__)

BLOBS_TABLE = os.environ['BLOBS_TABLE']
client = boto3.client('dynamodb')
s3_client = boto3.client('s3')
bucket = os.environ['BUCKET']


@app.route("/")
def index():
    return "All works"


@app.route("/blobs/<string:blob_id>")
def get_blob(blob_id):
    response = client.get_item(
        TableName=BLOBS_TABLE,
        Key={
            'blob_id': {'S': blob_id}
        }
    )
    item = response.get('Item')
    if not item:
        return jsonify({'error': 'Blob not found'}), 404

    return jsonify({
        'blob_id': item.get('blob_id').get('S'),
        'labels': item.get('labels')
    })


@app.route("/blobs", methods=["POST"])
def create_blob():
    callback_url = request.json.get('callback_url')
    if not callback_url:  # Check for url
        return jsonify({'error': 'Invalid callback url supplied'}), 400

    blob_id = str(uuid.uuid4())  # Creation of uuid for blob_id

    client.put_item(
        TableName=BLOBS_TABLE,
        Item={
            'blob_id': {'S': blob_id},
            'callback_url': {'S': callback_url}
            # 'upload_url': {'S': upload_url['url']},
            # 'labels': {'S': imageLabels}
        }
    )

    # Generate the presigned URL
    upload_url_raw = s3_client.generate_presigned_post(
        Bucket=bucket,
        Key=blob_id,
        ExpiresIn=3600
    )

    # Getting data for create a upload url in response
    url_for_upload = upload_url_raw['url']
    get_key_data = upload_url_raw['fields']
    get_key = get_key_data['key']
    upload_url_full = f'{url_for_upload}{get_key}'

    return jsonify({
        'blob_id': blob_id,
        'callback_url': callback_url,
        'upload_url': upload_url_full
    })


def rekognition_and_callback(event, context):

    files_uploaded = event['Records']
    for file in files_uploaded:
        file_name = file["s3"]["object"]["key"]

        rekognition_client = boto3.client('rekognition')
        response = rekognition_client.detect_labels(Image={'S3Object': {'Bucket': bucket, 'Name': file_name}},
                                                    MaxLabels=5, MinConfidence=50)

        image_labels = []

        for label in response['Labels']:
            image_labels.append(label["Label"].lower())
            image_labels.append(label["Confidence"].lower())
            image_labels.append(label["Parents"].lower())

        table = client.Table('BLOBS_TABLE')
        try:
            response = table.get_item(Key={'blob_id': file_name})
            item = response.get('Item')
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            response = table.update_item(
                Key={
                    'blob_id': file_name
                },
                UpdateExpression="set info.labels=:l",
                ExpressionAttributeValues={
                    ':l': list(image_labels)
                },
                ReturnValues="UPDATED_NEW"
            )

            blob_id = item.get('blob_id')
            callback_url = item.get('callback_url')

            data = {
                'blob_id': blob_id,
                'labels': image_labels
            }

            return requests.post(callback_url, data=json.dumps(data))


@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)
