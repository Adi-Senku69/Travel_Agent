from fastapi import FastAPI, UploadFile, File
import os

app = FastAPI()

UPLOAD_DIR = "/app/data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    if "employee" in file.filename.lower():
        upload_dir = os.path.join(UPLOAD_DIR, "employee_details")
    elif "organization" in file.filename.lower():
        upload_dir = os.path.join(UPLOAD_DIR, "organizational_details")
    else:
        upload_dir = os.path.join(UPLOAD_DIR, "travel_details")
    if not os.path.isdir(upload_dir):
        os.makedirs(upload_dir)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    with open("/app/data/summary/summary.txt", "w") as summary_file:
        pass
    return {"filename": file.filename, "message": "File uploaded successfully"}