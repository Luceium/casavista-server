from google.cloud import storage

def upload_file_to_firestore_storage(bucket_name, source_file_path, destination_blob_name):
    """
    Uploads a file to Google Cloud Storage and returns its public URL.

    Args:
        bucket_name (str): The name of the GCS bucket.
        source_file_path (str): The local path to the file to be uploaded.
        destination_blob_name (str): The desired path/name of the file in the bucket.

    Returns:
        str: The public URL of the uploaded file.
    """
    try:
        # Initialize a Cloud Storage client
        storage_client = storage.Client()
        
        # Get the bucket
        bucket = storage_client.bucket(bucket_name)
        
        # Upload the file
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)
        
        # Make the file publicly accessible
        blob.make_public()
        
        # Return the public URL
        return blob.public_url

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
