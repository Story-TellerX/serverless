import json
import mimetypes
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

    labels_raw = item.get('labels').get('S')
    labels_for_response = json.loads(labels_raw)

    return jsonify({
        'blob_id': item.get('blob_id').get('S'),
        'labels': labels_for_response
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
    files_uploaded = event['Records'][0]

    file_in_storage = files_uploaded["s3"]
    file_object = file_in_storage["object"]
    file_name = file_object["key"]

    s3_object = s3_client.get_object(Bucket=bucket, Key=file_name)
    header_for_content = s3_object['ContentType']
    extension = mimetypes.guess_extension(header_for_content, strict=False)

    filename_with_extension = f'{file_name}{extension}'

    copy_source = {'Bucket': bucket, 'Key': file_name}
    s3_client.copy_object(Bucket=bucket, CopySource=copy_source, Key=filename_with_extension)
    s3_client.delete_object(Bucket=bucket, Key=file_name)

    rekognition_client = boto3.client('rekognition')
    response = rekognition_client.detect_labels(Image={'S3Object': {'Bucket': bucket, 'Name': filename_with_extension}},
                                                MaxLabels=5)

    image_labels_dict = {}
    parent_list = []
    image_labels_list = []

    for label in response['Labels']:
        image_labels_dict["Label"] = label['Name']
        image_labels_dict["Confidence"] = label['Confidence']
        for parent in label['Parents']:
            parent_list.append(parent['Name'])
            image_labels_dict["Parent"] = parent_list
        image_labels_list.append(dict(image_labels_dict))

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
        image_labels_list_for_db = json.dumps(image_labels_list)
        response = client.put_item(
            TableName=BLOBS_TABLE,
            Item={
                'blob_id': {'S': file_name},
                'callback_url': callback_url,
                'labels': {'S': image_labels_list_for_db}
            }
        )

        data = {
            'blob_id': file_name,
            'labels': image_labels_list
        }

        return requests.post(callback_url, data=json.dumps(data))


@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)
