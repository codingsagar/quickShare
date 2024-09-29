from fastapi import FastAPI,UploadFile, HTTPException
import boto3
from botocore.exceptions import NoCredentialsError
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
    region_name=os.getenv("S3_REGION_NAME"),
)



@app.get("/")
def read_root():
    return {"success": True}


@app.post("/files/upload/")
async def upload_file(file: UploadFile):
    try:
        file_content = await file.read()

        s3_client.put_object(
            Bucket=os.getenv("S3_BUCKET_NAME"),
            Key=file.filename,
            Body=file_content,
            ContentType=file.content_type
        )

        return {"message": f"File '{file.filename}' uploaded successfully to S3."}

    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="AWS credentials are missing or incorrect.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
