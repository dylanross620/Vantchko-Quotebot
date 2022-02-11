import json
import random
import irc.bot
import os.path

from bot import QuoteBot

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, bot):
        self.bot = bot

        self.parse_settings()

        token = self.settings['token']
        if token[:6] != 'oauth:':
            token = 'oauth:' + token
        channel = self.settings['channel']
        self.channel = '#' + channel

        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
        username = self.settings['bot-name']
        print('Connecting to ' + server + ' on port ' + str(port) + '...')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, token)], username, username)

    def parse_settings(self):
        # Attempt to get variables from 'settings_twitch.json' file
            if os.path.exists('settings_twitch.json'):
                # File exists, so load settings from it
                with open('settings_twitch.json', 'r') as f:
                    self.settings = json.load(f)

                print('Successfully loaded Twitch settings')
            else:
                # File doesn't exist, so prompt user for the settings and save them
                print('Twitch settings not found. Entering setup')

                token = input('Enter your Twitch TMI Token: ')
                name = input('Enter the bot\'s name: ')
                owner = input('Enter the channel name: ')

                self.settings = {'token': token,
                        'bot-name': name,
                        'channel': owner}
                with open('settings_twitch.json', 'w') as f:
                    json.dump(self.settings, f, indent=4)
                print('Successfully saved twitch settings to settings_twitch.json')

            self.settings['channel'] = self.settings['channel'].lower()

    def on_welcome(self, c, e):
        print('Joining ' + self.channel)

        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)
        self.send_message('Bot online.\a')
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
        message_words = e.arguments[0].split()

        if message_words[0].lower() == '!quote':
            if len(message_words) < 2:
                self.send_random_quote(tags['display-name'])
            else:
                self.quote_commands(e, message_words[1].lower(), message_words[2:], tags)
        
        elif message_words[0].lower() == '!roll' or message_words[0].lower() == '!r':
            if len(message_words) < 2:
                self.send_message(f"{tags['display-name']} Must specify what to roll")
            else:
                self.roll_dice(message_words[1], tags['display-name'])

    def send_random_quote(self, user):
        # Ensure that there is at least 1 quote to get
        num, quote = self.bot.get_random_quote()
        if num == -1:
            self.send_message(f"{user} {quote}")
        else:
            self.send_message(f"{user} Quote #{num+1}: {quote}")

    def quote_commands(self, e, cmd, args, tags):
        c = self.connection
        badges = tags['badges'].split(',')

        is_admin = False
        for b in badges:
            if 'moderator' in b or 'broadcaster' in b:
                is_admin = True
                break
        
        self.send_message(self.bot.quote_commands(cmd, args, tags['display-name'], is_admin))

    def roll_dice(self, command, user):
        command = command.strip().lower()
        self.send_message(f"{user} {self.bot.roll_dice(command)[0]}")
