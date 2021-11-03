import os
import uuid

import boto3

from flask import Flask, jsonify, request, make_response

app = Flask(__name__)

BLOBS_TABLE = os.environ['BLOBS_TABLE']
client = boto3.client('dynamodb')


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

    labels_data = [
        {
            "label": "string",
            "confidence": 0,
            "parents": [
                "string"
            ]
        }
    ]

    return jsonify({
        'blob_id': item.get('blob_id').get('S'),
        'labels': labels_data
    })


@app.route("/blobs", methods=["POST"])
def create_blob():
    callback_url = request.json.get('callback_url')
    if not callback_url:  # Check for url
        return jsonify({'error': 'Invalid callback url supplied'}), 400

    blob_id = str(uuid.uuid4())  # Creation of uuid for blob_id
    BASE_DOMAIN = 'https://0ruf9yg4je.execute-api.us-east-2.amazonaws.com/dev/'
    upload_url = f'{BASE_DOMAIN} + {blob_id}'

    client.put_item(
        TableName=BLOBS_TABLE,
        Item={
            'blob_id': {'S': blob_id},
            'callback_url': {'S': callback_url},
            'upload_url': {'S': upload_url}
        }
    )

    return jsonify({
        'blob_id': blob_id,
        'callback_url':  callback_url,
        'upload_url': upload_url
    })


@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)
