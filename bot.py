import irc.bot
import json
from datetime import date
import random

import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, quote_list, sheet, settings):
        self.quote_list = quote_list
        self.sheet = sheet
        self.settings = settings

        token = settings['token']
        if token[:6] != 'oauth:':
            token = 'oauth:' + token
        channel = settings['channel']
        self.channel = '#' + channel

        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
        username = settings['bot-name']
        print('Connecting to ' + server + ' on port ' + str(port) + '...')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, token)], username, username)

    def on_welcome(self, c, e):
        print('Joining ' + self.channel)

        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)
        self.send_message('Bot online.')
        print('Twitch bot initialized')

    def send_message(self, message):
        # Make sure message length doesn't exceed twitch IRC limit
        self.connection.privmsg(self.channel, message[:256])

    def on_pubmsg(self, c, e):
        # Clean up tags before using them
        tags = {kvpair['key']: kvpair['value'] for kvpair in e.tags}
        if 'badges' not in tags or tags['badges'] is None:
            tags['badges'] = ''

        # If first word in message is '!quote', run it as a command
        message_words = e.arguments[0].split(' ')

        if message_words[0].lower() == '!quote':
            if len(message_words) < 2:
                # Ensure that there is at least 1 quote to get
                if len(self.quote_list) == 0:
                    self.send_message(f"{tags['display-name']} There are no quotes to display")
                else:
                    # Get a random quote
                    target_idx = random.randrange(0, len(self.quote_list))
                    self.send_message(f"{tags['display-name']} Quote #{target_idx+1}: {self.quote_list[target_idx]}")
            else:
                self.do_command(e, message_words[1].lower(), message_words[2:], tags)
        
        elif message_words[0].lower() == '!roll' or message_words[0].lower() == '!r':
            if len(message_words) < 2:
                self.send_message(f"{tags['display-name']} Must specify what to roll")
            else:
                self.roll_dice(message_words[1], tags['display-name'])

    def save_quotes(self):
        # Clear sheet to remove old quotes that may have been removed
        self.sheet.values().clear(spreadsheetId=self.settings['spreadsheet-id'], range=self.settings['range-name']).execute()

        # Set the sheet to have the new values
        body = {'range':self.settings['range-name'],
                'values':[[q] for q in self.quote_list],
                'majorDimension':'ROWS'}
        self.sheet.values().update(spreadsheetId=self.settings['spreadsheet-id'], range=self.settings['range-name'], body=body, valueInputOption='USER_ENTERED').execute()

    def do_command(self, e, cmd, args, tags):
        c = self.connection
        badges = tags['badges'].split(',')

        is_admin = False
        for b in badges:
            if 'moderator' in b or 'broadcaster' in b:
                is_admin = True
                break

        # Check if user is asking for a specific quote
        try:
            quote_num = int(cmd)

            if quote_num <= len(self.quote_list) and quote_num > 0:
                self.send_message(f"{tags['display-name']} Quote #{quote_num}: {self.quote_list[quote_num-1]}")
            else:
                self.send_message(f"{tags['display-name']} There is no quote #{quote_num}")

            return
        except:
            pass

        # Check if asking to count quotes
        if cmd == 'count':
            self.send_message(f"{tags['display-name']} There are {len(self.quote_list)} quotes")
            return
        if cmd == 'list':
            self.send_message(f"{tags['display-name']} The quote list can be found at {self.settings['share-link']}")
            return

        # All future commands require at least 1 argument, so ensure it is there
        if len(args) < 1:
            self.send_message(f'{tags["display-name"]} Not enough arguments provided')
            return

        if cmd == 'add':
            date_str = date.today().strftime('%m/%d/%y')
            quoter = tags['display-name']

            quote_str = f"{' '.join(args)} [{date_str}] quoted by {quoter}"
            self.quote_list.append(quote_str)
            self.save_quotes()

            self.send_message(f"Quote #{len(self.quote_list)} successfully added: {quote_str}")
        elif cmd == 'remove':
            if not is_admin:
                self.send_message(f'{tags["display-name"]} Only moderators can remove quotes')
            else:
                try:
                    quote_num = int(args[0])

                    if quote_num < 1 or quote_num > len(self.quote_list):
                        self.send_message(f"{tags['display-name']} Cannot remove quote #{quote_num}")
                    else:
                        self.quote_list.pop(quote_num-1)
                        # Update file
                        self.save_quotes()

                        self.send_message(f"{tags['display-name']} Successfully removed quote #{quote_num}")

                except:
                    self.send_message(f'{tags["display-name"]} Quote to remove must be an integer')
        elif cmd == 'edit':
            if not is_admin:
                self.send_message(f"{tags['display-name']} Only moderators can remove quotes")
            else:
                try:
                    quote_num = int(args[0])

                    if quote_num < 1 or quote_num > len(self.quote_list):
                        self.send_message(f"{tags['display-name']} Cannot edit quote #{quote_num}")
                    else:
                        quote = self.quote_list[quote_num-1]
                        metadataIdx = quote.rindex('[')
                        edited = f"{' '.join(args[1:])} {quote[metadataIdx:]}"

                        self.quote_list[quote_num-1] = edited
                        self.save_quotes()

                        self.send_message(f"{tags['display-name']} Successfully edited quote #{quote_num}")
                except:
                    self.send_message(f"{tags['display-name']} Quote to edit must be an integer")

    def roll_dice(self, command, user):
        command = command.strip().lower()

        # Ensure dice type is specified
        try:
            dice_idx = command.index('d')
        except:
            self.send_message(f"{user} Must specify the type of die to roll")
            return

        # Get the count of dice to be rolled
        try:
            dice_count = int(command[:dice_idx])
            if dice_count < 1:
                self.send_message(f"{user} Dice count must be positive")
                return
        except:
            if dice_idx == 0:
                dice_count = 1 # Make specifying dice amount optional
            else:
                self.send_message(f"{user} Dice count must be an integer")
                return

        # Check if a keep is specified
        try:
            keep_idx = command.index('k')
        except:
            keep_idx = len(command)

        # Get dice type
        try:
            dice_type = int(command[dice_idx+1:keep_idx])
            if dice_type < 1:
                self.send_message(f"{user} Dice type must be positive")
                return
        except:
            self.send_message(f"{user} Dice type must be an integer")
            return

        # Roll the dice
        rolls = [random.randrange(1, dice_type+1) for i in range(dice_count)]
        
        # If keep wasn't specified, just send message and return now
        if keep_idx == len(command):
            self.send_message(f"{user} You rolled {', '.join([str(r) for r in rolls])}")
            return

        # Keep was specified. Find out if we are keeping high or low. Default to low
        try:
            reverse = command[keep_idx+1] == 'h'
        except:
            reverse = False

        try:
            keep_amount = int(command[keep_idx+2:])
            if keep_amount < 1:
                self.send_message(f"{user} Keep amount must be positive")
                return
        except:
            self.send_message(f"{user} Keep amount must be an integer")
            return

        keeped = [str(r) for r in rolls if r in sorted(rolls, reverse=reverse)[:keep_amount]]
        self.send_message(f"{user} You rolled {', '.join(keeped[:keep_amount])}")

def start():
    # Try to connect to the Google Sheets API
    # load credentials
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

    # Attempt to get variables from 'settings.json' file
    settings = None
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

    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()

    # Try to load existing quotes list from sheet
    result = sheet.values().get(spreadsheetId=settings['spreadsheet-id'], range=settings['range-name']).execute()
    quote_list = [res[0] for res in result.get('values', [])]

    bot = TwitchBot(quote_list, sheet, settings)
    bot.start()

if __name__ == '__main__':
    start()
