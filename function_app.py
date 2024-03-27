import os
import azure.functions as func
import json
import logging
from azure.storage.blob import BlobServiceClient
from shared_code import  util, packageTranslator



# Global environment variables
STORAGE_ACCOUNT = os.environ.get("storageAccount")
STORAGE_CONTAINER_SOURCE = os.environ.get("storageContainersource")
STORAGE_CONTAINER_TARGET = os.environ.get("storageContainertarget")
STORAGE_KEY = os.environ.get("storageKey")
TRANSLATE_ACCOUNT = os.environ.get("translateAccount")
TRANSLATE_KEY = os.environ.get("translateKey")

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="translate", methods=("POST",))
def translate(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    try:
        req_body = req.get_json()
    except Exception as e:
        logging.error("Error in fetching value : %s", e)
        return func.HttpResponse(body=f"Error in fetching value {e}", status_code=500)

    FILENAME = req_body.get("fileName")

    if not FILENAME:
        return func.HttpResponse(
            body="'fileName' is missing in the request body", status_code=400
        )
    if len(FILENAME) < 1:
        return func.HttpResponse(
            body="'fileName' is missing in the request body", status_code=400
        )
    logging.info(
        f"Python HTTP Doc processing trigger function processed a request."
    )

    response = json.dumps(alm_translate(FILENAME))
    return func.HttpResponse(response, headers={"Content-type": "application/json"})


def alm_translate(FILENAMELIST):
    blobService = BlobServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=STORAGE_KEY,
    )
    blobContainer = blobService.get_container_client(STORAGE_CONTAINER_SOURCE)
    finalJsonResponse = {
        "messageStatus": False,
        "translatefilenameList": [],
    }
    iflag: bool = True
    

    for FILENAME in FILENAMELIST:
        try:
            # INTERMEDIATE_FILENAME = f"Intermediate-{FILENAME}"

            fileResponse = {
                "originalFilename": FILENAME,
                "translatedFilename": "",
                "messageStatus": False,
                "error": "",
            }
            logging.info("Processing %s", FILENAME)
            blobClient = blobContainer.get_blob_client(FILENAME)
            if not blobClient.exists():
                fileResponse["error"] = (
                    f"File:{FILENAME} is not present in storage for translation"
                )
                logging.error(fileResponse["error"])
                finalJsonResponse["translatefilenameList"].append(fileResponse)
                iflag = False
                continue

            translateFilename = packageTranslator.translate_doc(
                FILENAME,
                STORAGE_ACCOUNT,
                STORAGE_CONTAINER_SOURCE,
                STORAGE_CONTAINER_TARGET,
                STORAGE_KEY,
                TRANSLATE_ACCOUNT,
                TRANSLATE_KEY,
            )

            # translate_file_status = util.check_translate_file_exists(
            #     blob_container=blobContainer,
            #     blob_path=TRANSLATE_FILE_PATH,
            #     retry_count=CHECK_RETRY_COUNT,
            #     sleep_time=CHECK_SLEEP_TIME,
            # )
            # file check true means it file exists
            # if not translate_file_status:
            #     raise Exception("File Translation failed after 10 retry")
        
            translate_file_status = util.change_content_type(
                STORAGE_ACCOUNT,
                STORAGE_KEY,
                STORAGE_CONTAINER_SOURCE,
                STORAGE_CONTAINER_TARGET,
                FILENAME,
                FILENAME
            )
            fileResponse["translatedFilename"] = FILENAME
            fileResponse["messageStatus"] = translate_file_status

        except Exception as e:
            fileResponse["error"] = (
                f"An error occurred while processing the file: {FILENAME}. Error: {str(e)}"
            )
            logging.error(fileResponse["error"])
            iflag = False

        finalJsonResponse["translatefilenameList"].append(fileResponse)

    if iflag is True:
        finalJsonResponse["messageStatus"] = True

    return finalJsonResponse