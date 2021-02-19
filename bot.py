import irc.bot
import json
from datetime import date
import random

NAME = 'VantchkoBot'
OWNER = 'Vantchko'

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, token, channel, quote_list):
        self.quote_list = quote_list
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
                self.send_message(f"Quote #{target_idx+1}: {self.quote_list[target_idx]}")
            else:
                self.do_command(e, message_words[1].lower(), message_words[2:], tags)

    def save_quotes(self):
        with open('quotes.json', 'w') as f:
            f.write(json.dumps({'quotes': self.quote_list}))

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
                self.send_message(f"Quote #{quote_num}: {self.quote_list[quote_num-1]}")
            else:
                self.send_message(f"There is no quote #{quote_num}")

            return
        except:
            pass

        # All future commands require at least 1 argument, so ensure it is there
        if len(args) < 1:
            self.send_message('Not enough arguments provided')
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
                self.send_message('Only moderators can remove quotes')
            else:
                try:
                    quote_num = int(args[0])

                    if quote_num < 1 or quote_num > len(self.quote_list):
                        self.send_message(f"Cannot remove quote #{quote_num}")
                    else:
                        self.quote_list.pop(quote_num-1)
                        # Update file
                        self.save_quotes()

                        self.send_message(f"Successfully removed quote #{quote_num}")

                except:
                    self.send_message('Quote to remove must be an integer')

def start():
    # Try to load token and client_id from 'token.env' file
    token = None
    with open('token.env', 'r') as f:
        token = f.readline().strip()
    assert token is not None, 'Error loading twitch token and client id from twitch_token.env'

    # Try to load existing quotes list from 'quotes.json' file
    quote_list = []
    try:
        with open('quotes.json', 'r') as f:
            json_str = f.readline().strip()
            quote_list = json.loads(json_str)['quotes']
    except:
        pass
    
    if len(quote_list) == 0:
        print('Unable to load quotes, initializing new list')
    else:
        print('Successfully loaded quotes list')

    username = NAME
    channel = OWNER.lower()

    bot = TwitchBot(username, token, channel, quote_list)
    bot.start()

if __name__ == '__main__':
    start()
