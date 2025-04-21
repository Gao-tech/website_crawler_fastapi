# Indroduction

The application is deployed onto AWS CloudFormation. It only deployed BeautifulSoup (BS4 for static sites) endpoint.
</br>

1. Serverless Application Model (SAM)
2. Mangum library to route FastAPI endpoints
3. Lambda function and API Gateway

# Setup & Deployment

## Create S3 bucket if needed

```
aws s3api create-bucket \
--bucket web-crawler-bucket-12345674 \
--region eu-north-1 \
--create-bucket-configuration LocationConstraint=eu-north-1 || true
```

## Adjustment of samconfig.toml and template.yaml file

```
[default.deploy.parameters]
```

## SAM Build

## SAM Deployment

```
 sam deploy \
  --s3-bucket web-crawler-bucket-12345674
```

## Remove .aws-sam file and SAM Deployment

```
 sam deploy \
  --s3-bucket web-crawler-bucket-12345674
```

## Get the endpoint from AWS API Gateway

```
https://r7nznin876.execute-api.eu-north-1.amazonaws.com/Prod/pages
```

## Test the endpoint from AWS API GateWay

```
https://r7nznin876.execute-api.eu-north-1.amazonaws.com/Prod/pages?target=https://filip-ph-johansson.github.io
```
