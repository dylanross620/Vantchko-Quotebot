import random
import irc.bot
from datetime import date

from bot import QuoteBot

class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, settings):
        self.settings = settings

        self.bot = QuoteBot(settings)

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
        if self.bot.quote_count() == 0:
            self.send_message(f"{user} There are no quotes to display")
        else:
            # Get a random quote
            target_idx = random.randrange(0, self.bot.quote_count())
            self.send_message(f"{user} Quote #{target_idx+1}: {self.bot.get_quote(target_idx)}")

    def quote_commands(self, e, cmd, args, tags):
        c = self.connection
        badges = tags['badges'].split(',')
        num_args = len(args)

        is_admin = False
        for b in badges:
            if 'moderator' in b or 'broadcaster' in b:
                is_admin = True
                break

        # Check if user is asking for a specific quote
        try:
            quote_num = int(cmd)

            if quote_num <= self.bot.quote_count() and quote_num > 0:
                self.send_message(f"{tags['display-name']} Quote #{quote_num}: {self.bot.get_quote(quote_num-1)}")
            else:
                self.send_message(f"{tags['display-name']} There is no quote #{quote_num}")

            return
        except:
            pass

        # Check if asking to count quotes
        if cmd == 'count':
            if num_args >= 1:
                try:
                    quote_num = int(args[0])

                    if quote_num <= self.bot.quote_count() and quote_num > 0:
                        num_times = self.bot.quote_usage_count(quote_num-1)
                        self.send_message(f"{tags['display-name']} Quote #{quote_num} has been used {num_times} time{'' if num_times == 1 else 's'}")
                        return
                except:
                    pass

            self.send_message(f"{tags['display-name']} There are {self.bot.quote_count()} quotes")
            return

        # Check if asking for the quote list
        if cmd == 'list':
            self.send_message(f"{tags['display-name']} The quote list can be found at {self.bot.get_share_link()}")
            return

        if cmd == 'add':
            if num_args < 1:
                self.send_message(f'{tags["display-name"]} Not enough arguments provided')
                return

            date_str = date.today().strftime('%m/%d/%y')
            quoter = tags['display-name']

            quote_str = f"{' '.join(args)} [{date_str}] quoted by {quoter}"
            self.bot.add_quote(quote_str)

            self.send_message(f"Quote #{self.bot.quote_count()} successfully added: {quote_str}")
        elif cmd == 'remove':
            if num_args < 1:
                self.send_message(f'{tags["display-name"]} Not enough arguments provided')
                return

            if not is_admin:
                self.send_message(f'{tags["display-name"]} Only moderators can remove quotes')
            else:
                try:
                    quote_num = int(args[0])

                    if quote_num < 1 or quote_num > self.bot.quote_count():
                        self.send_message(f"{tags['display-name']} Cannot remove quote #{quote_num}")
                    else:
                        self.bot.remove_quote(quote_num-1)

                        self.send_message(f"{tags['display-name']} Successfully removed quote #{quote_num}")

                except:
                    self.send_message(f'{tags["display-name"]} Quote to remove must be an integer')
        elif cmd == 'edit':
            if num_args < 1:
                self.send_message(f'{tags["display-name"]} Not enough arguments provided')
                return

            if not is_admin:
                self.send_message(f"{tags['display-name']} Only moderators can remove quotes")
            else:
                try:
                    quote_num = int(args[0])

                    if quote_num < 1 or quote_num > self.bot.quote_count():
                        self.send_message(f"{tags['display-name']} Cannot edit quote #{quote_num}")
                    else:
                        quote = self.bot.get_quote(quote_num-1, False)
                        metadataIdx = quote.rindex('[')
                        edited = f"{' '.join(args[1:])} {quote[metadataIdx:]}"

                        self.bot.add_quote(edited, quote_num-1)

                        self.send_message(f"{tags['display-name']} Successfully edited quote #{quote_num}")
                except:
                    self.send_message(f"{tags['display-name']} Quote to edit must be an integer")
        else:
            # Assume user wants a random quote. They're probably saying a message after asking for the quote
            self.send_random_quote(tags['display-name'])

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

        # Easter egg to mess with Del
        if dice_type == 1:
            self.send_message(f"Nice try, Del Kappa")
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

#if __name__ == '__main__':
#    settings = self.bot.parse_settings()
#    sheet, quote_list = self.bot.load_quotes(settings)
#
#    twitch = TwitchBot(quote_list, sheet, settings)
#    twitch.start()
