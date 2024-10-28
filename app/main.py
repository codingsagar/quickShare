from fastapi import FastAPI,UploadFile, HTTPException,Depends
from fastapi.responses import RedirectResponse
import boto3
from sqlmodel import Session,select
from botocore.exceptions import NoCredentialsError
import os
from dotenv import load_dotenv
from database import db_init,File,get_session
from contextlib import asynccontextmanager
from uuid import uuid4
from datetime import datetime,timedelta

load_dotenv()


@asynccontextmanager
async def lifespan(app:FastAPI):
    db_init()
    yield


app = FastAPI(lifespan=lifespan)


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
async def upload_file(file: UploadFile,
session: Session = Depends(get_session)):
    try:
        file_content = await file.read()

        extension = file.filename.split('.')[-1]

        unique_filename = f"{str(uuid4())}.{extension}"

        s3_client.put_object(
            Bucket=os.getenv("S3_BUCKET_NAME"),
            Key= unique_filename,
            Body=file_content,
            ContentType=file.content_type
        )

        presigned_url : str = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': f'{os.getenv("S3_BUCKET_NAME")}',
                'Key': f'{unique_filename}',
                'ResponseContentDisposition': f'attachment;filename={file.filename}'
            },
            ExpiresIn=630
        )

        download_id = str(uuid4())

        new_file = File(
            key= download_id,
            url= f"{presigned_url}",
            downloaded= False,
        )

        session.add(new_file)
        session.commit()
        session.refresh(new_file)

        return {"message": f"File '{file.filename}' uploaded successfully to S3.","url":f"http://127.0.0.1:8000/download/{download_id}"}

    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="AWS credentials are missing or incorrect.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{download_id}/")
async def download_file(download_id: str, db: Session = Depends(get_session)):

    statement = select(File).where(File.key == download_id)

    file_record = db.exec(statement).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    

    if datetime.now() > file_record.uploaded_at + timedelta(minutes=10.5):
        raise HTTPException(status_code=410, detail="File has expired")

    if file_record.downloaded:
        raise HTTPException(status_code=403, detail="File already downloaded")

    file_record.downloaded = True
    db.commit()

    return RedirectResponse(url=file_record.url)