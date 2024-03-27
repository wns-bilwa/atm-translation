import datetime
import logging
import time

from azure.storage.blob import (
    BlobClient,
    BlobSasPermissions,
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
)


def get_blob_content_properties(blob_container, blob_path):
    logging.info(f"Getting Content of {blob_path}")
    # Get blob properties
    blob_client = blob_container.get_blob_client(blob_path)

    # Retrieve content type from properties
    content_type = blob_client.get_blob_properties().content_settings.content_type
    return blob_client, content_type


def create_service_sas_blob(blob_client: BlobClient, account_key: str):
    # Create a SAS token that's valid for one day, as an example
    start_time = datetime.datetime.now(datetime.timezone.utc)
    expiry_time = start_time + datetime.timedelta(days=1)

    sas_token = generate_blob_sas(
        account_name=blob_client.account_name,
        container_name=blob_client.container_name,
        blob_name=blob_client.blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=expiry_time,
        start=start_time,
    )

    return sas_token


def check_translate_file_exists(
    blob_container, blob_path, retry_count=10, sleep_time=5
):
    for _ in range(retry_count):
        try:
            blob_client = blob_container.get_blob_client(blob_path)
            if blob_client.exists():
                return True
        except Exception as e:
            print(f"An error occurred: {e}")

        time.sleep(sleep_time)
    return False


def change_content_type(
    storage_account,
    storage_key,
    storage_container_source,
    storage_container_target,
    source_file_path,
    target_file_path,
):
    blobService = BlobServiceClient(
        account_url=f"https://{storage_account}.blob.core.windows.net",
        credential=storage_key,
    )
    blob_container_source = blobService.get_container_client(storage_container_source)
    blob_container_target = blobService.get_container_client(storage_container_target)

    original_file_path = source_file_path
    # original file content type
    logging.info(f"Getting Original Content Type of {original_file_path}")
    # source file content type
    _, original_file_content_type = get_blob_content_properties(
        blob_container=blob_container_source, blob_path=original_file_path
    )
    destination_path = target_file_path

    # target file content type
    _, destination_file_content_type = get_blob_content_properties(
        blob_container=blob_container_target, blob_path=destination_path
    )
    # create destination blob
    destination_blob_client = blob_container_target.get_blob_client(destination_path)
    # sas_token = create_service_sas_blob(source_file_blob, storage_key)
    # source_file_url = f"{source_file_blob.url}?{sas_token}"
    # if content of original different from intermediate then upload original content type

    if original_file_content_type != destination_file_content_type:
        logging.info("Updating Content Type")
        cnt_settings = ContentSettings(content_type=original_file_content_type)
        destination_blob_client.set_http_headers(content_settings=cnt_settings)
        # destination_blob_client.upload_blob_from_url(
        #     source_url=source_file_url, content_settings=cnt_settings
        # )
    # else:
        # destination_blob_client.set_http_headers(content_settings=cnt_settings)

        # destination_blob_client.upload_blob_from_url(
        #     source_url=source_file_url,
        # )
    logging.info(f"Translated file Content Type Change Done, FileName: {destination_path}")

    if destination_blob_client.exists():
        return True
    else:
        return False