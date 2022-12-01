import os.path

from time import sleep

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

class YoutubeBot:
    def __init__(self, bot):
        self.bot = bot
        self.youtube = self.youtube_connect()
        print('Successfully connected to Youtube')

        video_id = input('Enter Youtube stream id: ').strip()
        req = self.youtube.videos().list(part='liveStreamingDetails', id=video_id)
        resp = req.execute()

        self.stream_id = resp['items'][0]['liveStreamingDetails']['activeLiveChatId']
        self.next_page_token = None
        self.delay = 0

    def youtube_connect(self):
        # Load credentials
        creds = None
        if os.path.exists('token_youtube.json'):
            creds = Credentials.from_authorized_user_file('token_youtube.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials_youtube.json', SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials
            with open('token_youtube.json', 'w') as f:
                f.write(creds.to_json())

        service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)

        return service

    def send_message(self, message):
        body = {
            'snippet': {
                'liveChatId': self.stream_id,
                'type': 'textMessageEvent',
                'textMessageDetails': {
                    'messageText': message
                }
            }
        }

        self.youtube.liveChatMessages().insert(part='snippet', body=body).execute()

    def get_messages(self, skip=False):
        # Request messages that have been sent since the last check
        request = self.youtube.liveChatMessages().list(liveChatId=self.stream_id, part='snippet,authorDetails', pageToken=self.next_page_token)
        resp = request.execute()

        self.next_page_token = resp['nextPageToken']
        self.delay = float(float(resp['pollingIntervalMillis']) / 1000)

        # Option to get messages and not actually parse them at all. This is done in order to set `self.next_page_token` without taking up unnecessary time
        if skip:
            return

        messages = []
        for message in resp['items']:
            # Only track chat text messages
            if message['snippet']['type'] != 'textMessageEvent':
                continue
            
            is_admin = message['authorDetails']['isChatModerator'] or message['authorDetails']['isChatOwner']
            messages.append([message['snippet']['textMessageDetails']['messageText'], message['authorDetails']['displayName'], is_admin])

        return messages

    def start(self):
        # Read any existing messages so that the bot doesn't follow old commands
        self.get_messages(True)

        self.send_message('Bot online') 

        while True:
            for message, author, is_mod in self.get_messages():
                # If first word in message is '!quote', run it as a command
                message_words = message.split()

                if message_words[0].lower() == '!quote':
                    if len(message_words) < 2:
                        self.send_random_quote(author)
                    else:
                        self.send_message(self.bot.quote_commands(message_words[1], message_words[2:], author, is_mod))
                
                elif message_words[0].lower() == '!roll' or message_words[0].lower() == '!r':
                    if len(message_words) < 2:
                        self.send_message(f"{author} Must specify what to roll")
                    else:
                        self.roll_dice(message_words[1], author)

            sleep(self.delay)

    def send_random_quote(self, user):
        num, quote = self.bot.get_random_quote()
        if num == -1:
            self.send_message(f"{user} {quote}")
        else:
            self.send_message(f"{user} Quote #{num+1}: {quote}")

    def roll_dice(cmd, user):
        cmd = cmd.strip().lower()
        self.send_message(f"{user} {self.bot.roll_dice(cmd)[0]}")
