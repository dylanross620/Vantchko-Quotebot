import os.path

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

        self.stream_id = input('Enter Youtube stream id: ').strip()
        self.next_page_token = None

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

        return service.liveChatMessages()

    def send_message(self, message):
        body = {'snippet': {
            'liveChatId': self.stream_id,
            'type': 'textMessageEvent',
            'textMessageDetails': {
                'messageText': message
                }
            }}

        request = self.youtube.insert(part='snippet', body=body)
        resp = request.execute()
        print(type(resp))

    def get_messages(self):
        # Request messages that have been sent since the last check
        request = self.youtube.list(liveChatId=self.stream_id, part='snippet', pageToken=self.next_page_token)
        resp = request.execute()

        self.next_page_token = resp.nextPageToken

        messages = []
        for message in resp.items:
            # Only track chat text messages
            if message.snippet.type != 'textMessageEvent':
                continue
            
            messages.append([message.snippet.textMessageDetails.messageText, message.authorDetails.displayName, message.authorDetails.isChatModerator])

        return messages

    def start(self):
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

    def send_random_quote(self, user):
        # Ensure that there is at least 1 quote to get
        if self.bot.quote_count() == 0:
            self.send_message(f"{user} There are no quotes to display")
        else:
            # Get random quote
            num, quote = self.bot.get_random_quote()
            self.send_message(f"{user} Quote #{num+1}: {quote}")

    def roll_dice(cmd, user):
        cmd = cmd.strip().lower()
        self.send_message(f"{user} {self.bot.roll_dice(cmd)[0]}")
