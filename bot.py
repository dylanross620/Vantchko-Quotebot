import json
import random

from sys import argv
from datetime import date

import os.path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

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
        if len(self.quote_list) == 0:
            return (-1, "There are no quotes to display")
        num = random.randrange(0, len(self.quote_list))
        return (num, self.get_quote(num))

    def quote_usage_count(self, num):
        return self.quote_list[num][1]

    def add_quote(self, quote, idx=-1):
        if idx < 0:
            self.quote_list.append([quote, 0])
        else:
            self.quote_list[idx][0] = quote

        self.save_quotes()

    def remove_quote(self, num):
        self.quote_list.pop(num)
        self.save_quotes()

    def quote_commands(self, cmd, args, user, is_admin):
        num_args = len(args)

        # Check if user is asking for a specific quote
        try:
            quote_num = int(cmd)

            if quote_num <= len(self.quote_list) and quote_num > 0:
                return f"{user} Quote #{quote_num}: {self.get_quote(quote_num-1)}"
            else:
                return f"{user} There is no quote #{quote_num}"
        except:
            pass

        # Check if asking to count quotes
        if cmd == 'count':
            if num_args >= 1:
                try:
                    quote_num = int(args[0])

                    if quote_num <= len(self.quote_list) and quote_num > 0:
                        num_times = self.quote_usage_count(quote_num-1)
                        return f"{user} Quote #{quote_num} has been used {num_times} time{'' if num_times == 1 else 's'}"
                except:
                    pass

            return f"{user} There are {len(self.quote_list)} quotes"

        # Check if asking for the quote list
        if cmd == 'list':
            return f"{user} The quote list can be found at {self.settings['share-link']}"

        if cmd == 'add':
            if num_args < 1:
                return f"{user} Not enough arguments provided"

            date_str = date.today().strftime('%m/%d/%y')

            quote_str = f"{' '.join(args)} [{date_str}] quoted by {user}"
            self.add_quote(quote_str)

            return f"{user} Quote #{len(self.quote_list)} successfully added: {quote_str}"
        elif cmd == 'remove':
            if num_args < 1:
                return f"{user} Not enough arguments provided"

            if not is_admin:
                return f"{user} Only moderators can remove quotes"
            else:
                try:
                    quote_num = int(args[0])

                    if quote_num < 1 or quote_num > len(self.quote_list):
                        return f"{user} Cannot remove quote #{quote_num}"
                    else:
                        self.remove_quote(quote_num-1)

                        return f"{user} Successfully removed quote #{quote_num}"

                except:
                    return f"{user} Quote to remove must be an integer"
        elif cmd == 'edit':
            if num_args < 1:
                return f"{user} Not enough arguments provided"

            if not is_admin:
                return f"{user} Only moderators can remove quotes"
            else:
                try:
                    quote_num = int(args[0])

                    if quote_num < 1 or quote_num > len(self.quote_list):
                        return f"{user} Cannot edit quote #{quote_num}"
                    else:
                        quote = self.get_quote(quote_num-1, False)
                        metadataIdx = quote.rindex('[')
                        edited = f"{' '.join(args[1:])} {quote[metadataIdx:]}"

                        self.add_quote(edited, quote_num-1)

                        return f"{user} Successfully edited quote #{quote_num}"
                except:
                    return f"{user} Quote to edit must be an integer"
        else:
            # Assume user wants a random quote. They're probably saying a message after asking for the quote
            num, quote = self.get_random_quote()
            return f"{user} Quote #{num}: {quote}"


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
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <bot type (twitch|youtube)>")
        return

    bot = QuoteBot(parse_settings())

    arg = argv[1].strip().lower()
    if arg == 'twitch': 
        from twitch import TwitchBot
        twitch_bot = TwitchBot(bot)
        twitch_bot.start()
    elif arg == 'youtube' or arg == 'yt':
        from youtube import YoutubeBot
        yt_bot = YoutubeBot(bot)
        yt_bot.start()
    else:
        print(f"Unknown bot type {argv[1].strip()}")

if __name__ == '__main__':
    start()
