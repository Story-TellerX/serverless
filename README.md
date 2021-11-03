<!--
title: 'Python Flask API backed by DynamoDB on AWS based on Serverless Framework'
description: 'This template demonstrates how to develop and deploy a simple Python Flask API service backed by DynamoDB running on AWS Lambda using the traditional Serverless Framework.'
layout: Doc
framework: v2
platform: AWS
language: Python
priority: 2
authorLink: 'https://github.com/serverless'
authorName: 'Serverless, inc.'
authorAvatar: 'https://avatars1.githubusercontent.com/u/13742415?s=200&v=4'
-->

# Serverless Framework Python Flask API service backed by DynamoDB on AWS

This project build on the template using the traditional Serverless Framework.

## Usage

### Prerequisites

In order to package your dependencies locally with `serverless-python-requirements`, you need to have `Python3.8` installed locally. You can create and activate a dedicated virtual environment with the following command:

```bash
python3.8 -m venv [env folder name]
source ./[env folder name]/bin/activate
cd path/to/your/project
curl -o- -L https://slss.io/install | bash
```

### Deployment

This example is made to work with the Serverless Framework dashboard, which includes advanced features such as CI/CD, monitoring, metrics, etc.

In order to deploy with dashboard, you need to first login with:

```
serverless login
```

install dependencies with:

```
npm install
```

and then perform deployment with:

```
serverless deploy
```

After running deploy, you should see output similar to:

```bash
Serverless: Using Python specified in "runtime": python3.8
Serverless: Packaging Python WSGI handler...
Serverless: Generated requirements from /home/xxx/xxx/xxx/examples/aws-python-flask-dynamodb-api/requirements.txt in /home/xxx/xxx/xxx/examples/aws-python-flask-dynamodb-api/.serverless/requirements.txt...
Serverless: Using static cache of requirements found at /home/xxx/.cache/serverless-python-requirements/62f10436f9a1bb8040df30ef2db5736c8015b18256bf0b6f1b0cbb2640030244_slspyc ...
Serverless: Packaging service...
Serverless: Excluding development dependencies...
Serverless: Injecting required Python packages to package...
Serverless: Creating Stack...
Serverless: Checking Stack create progress...
........
Serverless: Stack create finished...
Serverless: Uploading CloudFormation file to S3...
Serverless: Uploading artifacts...
Serverless: Uploading service aws-python-flask-dynamodb-api.zip file to S3 (1.3 MB)...
Serverless: Validating template...
Serverless: Updating Stack...
Serverless: Checking Stack update progress...
.................................
Serverless: Stack update finished...
Service Information
service: aws-python-flask-dynamodb-api
stage: dev
region: us-east-1
stack: aws-python-flask-dynamodb-api-dev
resources: 12
api keys:
  None
endpoints:
  ANY - https://xxxxxxx.execute-api.us-east-1.amazonaws.com/dev/
  ANY - https://xxxxxxx.execute-api.us-east-1.amazonaws.com/dev/{proxy+}
functions:
  api: aws-python-flask-dynamodb-api-dev-api
layers:
  None
```

_Note_: In current form, after deployment, your API is public and can be invoked by anyone. For production deployments, you might want to configure an authorizer. For details on how to do that, refer to [http event docs](https://www.serverless.com/framework/docs/providers/aws/events/apigateway/).
