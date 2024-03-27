#  import libraries
from azure.core.credentials import AzureKeyCredential
from datetime import datetime, timedelta
from azure.storage.blob import BlobSasPermissions, generate_container_sas
from azure.ai.translation.document import DocumentTranslationClient


def get_blob_sas(storage_account, storage_container_source, storage_creds, write_perm):
    """Function to generate sas key."""
    sas_blob = generate_container_sas(
        account_name=storage_account,
        container_name=storage_container_source,
        account_key=storage_creds,
        permission=BlobSasPermissions(read=True, write=write_perm),
        expiry=datetime.utcnow() + timedelta(minutes=30),
    )
    return sas_blob


def translate_doc(
    filename,
    storage_account,
    storage_container_source,
    storage_container_target,
    storage_creds,
    translate_account,
    translate_key,
):
    blob_source = get_blob_sas(
        storage_account, storage_container_source, storage_creds, False
    )
    blob_target = get_blob_sas(
        storage_account, storage_container_target, storage_creds, True
    )
    source_sas_url = f"https://{storage_account}.blob.core.windows.net/{storage_container_source}/{filename}?{blob_source}"
    target_sas_url = f"https://{storage_account}.blob.core.windows.net/{storage_container_target}/{filename}?{blob_target}"
    translateUrl = f"https://{translate_account}.cognitiveservices.azure.com"

    # initialize a new instance of the DocumentTranslationClient object to interact with the Document Translation feature
    client = DocumentTranslationClient(translateUrl, AzureKeyCredential(translate_key))

    # include source and target locations and target language code for the begin translation operation
    poller = client.begin_translation(
        source_sas_url, target_sas_url, "en", storage_type="file"
    )
    result = poller.result()
    final_result=list(result)

    if final_result[0].status == "Succeeded":
        return filename
