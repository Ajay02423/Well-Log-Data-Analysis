import boto3
from app.core.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        endpoint_url="http://localhost:9000",
    )


def upload_file(file_obj, key: str):
    s3 = get_s3_client()
    s3.upload_fileobj(file_obj, settings.S3_BUCKET_NAME, key)
