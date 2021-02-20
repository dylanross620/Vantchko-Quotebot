import irc.bot
import json
from datetime import date
import random

import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

NAME = 'VantchkoBot'
OWNER = 'Vantchko'

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '116l4KSU_G22t_tKIw6AE62gLOgkVUaam1uSHval62kE'
RANGE_NAME = 'Quotes!A:A'
READ_LINK = 'https://docs.google.com/spreadsheets/d/116l4KSU_G22t_tKIw6AE62gLOgkVUaam1uSHval62kE/edit?usp=sharing'

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, token, channel, quote_list, sheet):
        self.quote_list = quote_list
        self.sheet = sheet

        if token[:6] != 'oauth:':
            token = 'oauth:' + token
        self.channel = '#' + channel

        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
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
        self.connection.privmsg(self.channel, message)

    def on_pubmsg(self, c, e):
        # Clean up tags before using them
        tags = {kvpair['key']: kvpair['value'] for kvpair in e.tags}
        if 'badges' not in tags or tags['badges'] is None:
            tags['badges'] = ''

        # If first word in message is '!quote', run it as a command
        message_words = e.arguments[0].split(' ')

        if message_words[0].lower() == '!quote':
            if len(message_words) < 2:
                # Get a random quote
                target_idx = random.randrange(0, len(self.quote_list))
                self.send_message(f"{tags['display-name']} Quote #{target_idx+1}: {self.quote_list[target_idx]}")
            else:
                self.do_command(e, message_words[1].lower(), message_words[2:], tags)

    def save_quotes(self):
        # Clear sheet to remove old quotes that may have been removed
        self.sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()

        # Set the sheet to have the new values
        body = {'range':RANGE_NAME,
                'values':[[q] for q in self.quote_list],
                'majorDimension':'ROWS'}
        self.sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME, body=body, valueInputOption='USER_ENTERED').execute()

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
            self.send_message(f"{tags['display-name']} The quote list can be found at {READ_LINK}")
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

def start():
    # Try to load token and client_id from 'token.env' file
    token = None
    if os.path.exists('token.env'):
        with open('token.env', 'r') as f:
            token = f.readline().strip()
    if not token:
        token = input('Please enter your Twitch TMI token: ')
        with open('token.env', 'w') as f:
            f.write(token)

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

    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()

    # Try to load existing quotes list from sheet
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    quote_list = [res[0] for res in result.get('values', [])]

    username = NAME
    channel = OWNER.lower()

    bot = TwitchBot(username, token, channel, quote_list, sheet)
    bot.start()

if __name__ == '__main__':
    start()
