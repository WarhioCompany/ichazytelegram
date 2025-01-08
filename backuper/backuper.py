from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import time
from timer import Timer
import logging
from datetime import datetime

logger = logging.getLogger('logger.bot_logger')
timer = None


SERVICE_ACCOUNT = 'backuper/forward-lead-365711-0b30ae0a36de.json' # Please set the file of your credentials of service account.
UPLOAD_FILE = 'database/database.sqlite' # Please set the filename with the path you want to upload.
FOLDER_ID = '1_4tVqm1biCgHvvdNJuOH8JLLjEHLWQV4' # Please set the folder ID that you shared your folder with the service account.


SCOPES = ['https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT, SCOPES)
drive = build('drive', 'v3', credentials=credentials)


def backuper_start():
    global timer

    if not timer:
        timer = Timer(__backup_func, 24 * 60 * 60)
    else:
        print('backuper had already been started')


def __backup_func():
    FILENAME = datetime.now().strftime('%H:%M %d/%m/%y')
    metadata = {'name': FILENAME, "parents": [FOLDER_ID]}
    try:
        file = MediaFileUpload(UPLOAD_FILE, resumable=True)
        response = drive.files().create(body=metadata, media_body=file).execute()
        fileId = response.get('id')
        if fileId:
            logger.info('successfully backed up the database ' + fileId) # You can see the file ID of the uploaded file.
    except Exception as e:
        logger.error(f'something went wrong while trying to backup the database, error type {type(e)}. Trying again in one minute')
        time.sleep(60)