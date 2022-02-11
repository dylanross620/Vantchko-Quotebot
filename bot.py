import json
import random

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

    def get_random_quote(self):
        num = random.randrange(0, len(self.quote_list))
        return (num, self.get_quote(num))

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

    def roll_dice(self, command):
        # Ensure dice type is specified
        try:
            dice_idx = command.index('d')
        except:
            return "Must specify the type of die to roll", False

        # Get the count of dice to be rolled
        try:
            dice_count = int(command[:dice_idx])
            if dice_count < 1:
                return "Dice count must be positive", False
        except:
            if dice_idx == 0:
                dice_count = 1 # Make specifying dice amount optional
            else:
                return "Dice count must be an integer", False

        # Check if a keep is specified
        try:
            keep_idx = command.index('k')
        except:
            keep_idx = len(command)

        # Get dice type
        try:
            dice_type = int(command[dice_idx+1:keep_idx])
            if dice_type < 1:
                return "Dice type must be positive", False
        except:
            return "Dice type must be an integer", False

        # Roll the dice
        rolls = [random.randrange(1, dice_type+1) for i in range(dice_count)]
        
        # If keep wasn't specified, just send message and return now
        if keep_idx == len(command):
            return f"You rolled {', '.join([str(r) for r in rolls])}", True

        # Keep was specified. Find out if we are keeping high or low. Default to low
        try:
            reverse = command[keep_idx+1] == 'h'
        except:
            reverse = False

        try:
            keep_amount = int(command[keep_idx+2:])
            if keep_amount < 1:
                return "Keep amount must be positive", False
        except:
            return "Keep amount must be an integer", False

        keeped = [str(r) for r in rolls if r in sorted(rolls, reverse=reverse)[:keep_amount]]
        return f"You rolled {', '.join(keeped[:keep_amount])}", True


def parse_settings():
    # Attempt to get variables from 'settings.json' file
    if os.path.exists('settings.json'):
        # File exists, so load settings from it
        with open('settings.json', 'r') as f:
            settings = json.load(f)

        print('Successfully loaded quote bot settings')
    else:
        # File doesn't exist, so prompt user for the settings and save them
        print('Settings not found. Entering setup')

        spreadsheet_id = input('Enter the ID of the quote spreadsheet: ')
        range_name = input('Enter the range of the sheet for quotes to enter: ')
        read_link = input('Enter the viewing link for the quote sheet: ')

        settings = {'spreadsheet-id': spreadsheet_id,
                'range-name': range_name,
                'share-link': read_link}
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        print('Successfully saved settings to settings.json')

    return settings

def start():
    bot = QuoteBot(parse_settings())

    from twitch import TwitchBot
    bot = TwitchBot(bot)
    bot.start()

if __name__ == '__main__':
    start()
