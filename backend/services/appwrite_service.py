import uuid
from flask import current_app
from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.input_file import InputFile
from services.errors import ApiError

def get_appwrite_client():
    client = Client()
    client.set_endpoint(current_app.config["APPWRITE_ENDPOINT"])
    client.set_project(current_app.config["APPWRITE_PROJECT_ID"])
    client.set_key(current_app.config["APPWRITE_API_KEY"])
    return client

def upload_image_to_appwrite(file):
    """
    Uploads a Flask FileStorage object to Appwrite storage and returns the file View URL.
    """
    if not current_app.config.get("APPWRITE_PROJECT_ID") or not current_app.config.get("APPWRITE_API_KEY") or not current_app.config.get("APPWRITE_BUCKET_ID"):
        raise ApiError("Appwrite configuration is missing on the server", status_code=500)

    try:
        client = get_appwrite_client()
        storage = Storage(client)
        bucket_id = current_app.config["APPWRITE_BUCKET_ID"]
        endpoint = current_app.config["APPWRITE_ENDPOINT"]
        project_id = current_app.config["APPWRITE_PROJECT_ID"]
        
        # Determine extension and generate a unique file ID
        ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else "png"
        file_id = f"{uuid.uuid4().hex}"
        
        # Read the file content
        file_content = file.read()
        file.seek(0)  # Reset pointer if it needs to be read again
        
        # Appwrite InputFile from bytes
        input_file = InputFile.from_bytes(file_content, filename=f"{file_id}.{ext}")

        # Upload file to Appwrite
        result = storage.create_file(
            bucket_id=bucket_id,
            file_id=file_id,
            file=input_file
        )
        
        # Construct the file view URL
        # Format: [ENDPOINT]/storage/buckets/[BUCKET_ID]/files/[FILE_ID]/view?project=[PROJECT_ID]
        view_url = f"{endpoint}/storage/buckets/{bucket_id}/files/{result['$id']}/view?project={project_id}"
        
        return view_url

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise ApiError(f"Failed to upload image to Appwrite: {str(e)}", status_code=500)
