import json

import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/youtube']

settings = None
sheet = None
quote_list = None

class QuoteBot:
    def __init__(self, settings):
        self.settings = settings
        self.load_quotes()

    def sheets_connect(self):
        # Load credentials
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save credentials
            with open('token.json', 'w') as f:
                f.write(creds.to_json())

        service = build('sheets', 'v4', credentials=creds)

        return service.spreadsheets()

    # Load the spreadsheet and any quotes stored in it. Returns both the spreadsheet and the quotes
    def load_quotes(self):
        self.sheet = self.sheets_connect() 

        # Try to load existing quotes list from sheet
        if len(self.settings['spreadsheet-id']) > 0:
            result = self.sheet.values().get(spreadsheetId=self.settings['spreadsheet-id'], range=self.settings['range-name']).execute()
            self.quote_list = [[res[0], int(res[1])] for res in result.get('values', [])]
        else:
            self.quote_list = []

    def save_quotes(self, recursed=False):
        try:
            # Clear sheet to remove old quotes that may have been removed
            self.sheet.values().clear(spreadsheetId=self.settings['spreadsheet-id'], range=self.settings['range-name']).execute()

            # Set the sheet to have the new values
            body = {'range':self.settings['range-name'],
                    'values':[[q[0], str(q[1])] for q in self.quote_list],
                    'majorDimension':'ROWS'}
            self.sheet.values().update(spreadsheetId=self.settings['spreadsheet-id'], range=self.settings['range-name'], body=body, valueInputOption='USER_ENTERED').execute()
        except Exception as e:
            if not recursed:
                print('Disconnected from sheets, refreshing')
                self.sheet = self.sheets_connect()
                self.save_quotes(True)
            else:
                raise e

    def get_quote(self, num, count=True):
        # Only count this as retrieving a quote (and update sheet correspondingly) if asked for by user
        if count:
            self.quote_list[num][1] += 1
            self.save_quotes()

        return self.quote_list[num][0]

    def quote_usage_count(self, num):
        return self.quote_list[num][1]

    def quote_count(self):
        return len(self.quote_list)

    def get_share_link(self):
        return self.settings['share-link']

    def add_quote(self, quote, idx=-1):
        if idx < 0:
            self.quote_list.append([quote, 0])
        else:
            self.quote_list[idx][0] = quote

        self.save_quotes()

    def remove_quote(self, num):
        self.quote_list.pop(num)
        self.save_quotes()

def parse_settings():
    # Attempt to get variables from 'settings.json' file
    if os.path.exists('settings.json'):
        # File exists, so load settings from it
        with open('settings.json', 'r') as f:
            settings = json.load(f)

        print('Successfully loaded settings')
    else:
        # File doesn't exist, so prompt user for the settings and save them
        print('Settings not found. Entering setup')

        token = input('Enter your Twitch TMI Token: ')
        name = input('Enter the bot\'s name: ')
        owner = input('Enter the channel name: ')
        spreadsheet_id = input('Enter the ID of the quote spreadsheet: ')
        range_name = input('Enter the range of the sheet for quotes to enter: ')
        read_link = input('Enter the viewing link for the quote sheet: ')

        settings = {'token': token,
                'bot-name': name,
                'channel': owner,
                'spreadsheet-id': spreadsheet_id,
                'range-name': range_name,
                'share-link': read_link}
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        print('Successfully saved settings to settings.json')

    settings['channel'] = settings['channel'].lower()

    return settings

def start():
    settings = parse_settings()

    from twitch import TwitchBot
    bot = TwitchBot(settings)
    bot.start()

if __name__ == '__main__':
    start()
