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


# Function based on event
def hello(event, context):
    body = {
        "message": "All works!",
        "input": event,
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response


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
        }
    )

    # Generate the presigned URL
    upload_url_raw = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': bucket,
            'Key': blob_id
        },
        ExpiresIn=3600,
        HttpMethod='PUT'
    )

    return jsonify({
        'blob_id': blob_id,
        'callback_url': callback_url,
        'upload_url': upload_url_raw
    })


def rekognition_and_callback(event, context):

    files_uploaded = event['Records']
    for file in files_uploaded:
        file_in_storage = file["s3"]
        file_object = file_in_storage["object"]
        file_name = file_object["key"]

        rekognition_client = boto3.client('rekognition')
        response = rekognition_client.detect_labels(Image={'S3Object': {'Bucket': bucket, 'Name': file_name}},
                                                    MaxLabels=5)

        image_labels = []

        for label in response['Labels']:
            image_labels.append("Label: " + label['Name'])
            image_labels.append("Confidence: " + str(label['Confidence']))
            for parent in label['Parents']:
                image_labels.append("   " + parent['Name'])

        try:
            response = client.get_item(
                TableName=BLOBS_TABLE,
                Key={
                    'blob_id': {'S': file_name}
                }
            )
            item = response.get('Item')
            callback_url = item.get('callback_url')
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            response = client.put_item(
                TableName=BLOBS_TABLE,
                Item={
                    'blob_id': {'S': file_name},
                    'callback_url': {'S': callback_url},
                    'labels': image_labels
                }
            )

            data = {
                'blob_id': file_name,
                'labels': image_labels
            }

            return requests.post(callback_url, data=json.dumps(data))


@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)
