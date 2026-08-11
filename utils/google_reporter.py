import os
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
import traceback

class GoogleReporter:
    def __init__(self, credentials_path: str, sheet_id: str, drive_folder_id: str):
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.drive_folder_id = drive_folder_id
        
        # Scopes required for both Drive and Sheets
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            creds = None
            token_path = 'token.json'
            
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first time.
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, self.scopes)
                
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.scopes)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.credentials = creds
            self.gc = gspread.authorize(self.credentials)
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            self.initialized = True
        except Exception as e:
            print(f"\n[GoogleReporter] Initialization failed: {e}")
            self.initialized = False
        
    def append_row(self, test_name: str, status: str, duration: str, error_msg: str = "", screenshot_link: str = ""):
        if not self.initialized:
            return
            
        try:
            sheet = self.gc.open_by_key(self.sheet_id).sheet1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp, test_name, status, duration, error_msg, screenshot_link]
            sheet.append_row(row, table_range="A1", insert_data_option="INSERT_ROWS", value_input_option="USER_ENTERED")
            print(f"\n[GoogleReporter] Appended result for {test_name}")
        except Exception as e:
            print(f"\n[GoogleReporter] Failed to append to sheet: {e}")
            traceback.print_exc()

    def upload_screenshot(self, file_path: str) -> str:
        if not self.initialized or not os.path.exists(file_path):
            return ""
            
        try:
            file_name = os.path.basename(file_path)
            file_metadata = {
                'name': file_name,
                'parents': [self.drive_folder_id]
            }
            media = MediaFileUpload(file_path, mimetype='image/png')
            
            # Upload file
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            # Make the file readable by anyone with the link
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.drive_service.permissions().create(
                fileId=file.get('id'),
                body=permission
            ).execute()
            
            print(f"\n[GoogleReporter] Uploaded {file_name} to Drive")
            return file.get('webViewLink')
        except Exception as e:
            print(f"\n[GoogleReporter] Failed to upload to drive: {e}")
            traceback.print_exc()
            return ""
