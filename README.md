# Vantchko-Quotebot
A Twitch chat bot for quote tracking.

## Setup
### Python Setup
This project uses python 3 and requires the datetime and the irc modules. This can be installed using pip by using ```pip install -r requirements.txt ```.

### Twitch Setup
To setup the Twitch bot, you must first make a Twitch account for your bot to post from (unless you want it to post from your own account). While logged into the
account the bot will post from, obtain a Twitch tmi token. This token must be saved to a file called `token.env`.

In addition to setting up the Twitch token, you also must open the file ```twitch_bot.py``` and modify some variables found at the top of the file:
- `NAME` is the name of the account the bot will be posting from. This should match the name of the account you retrieved your token with.
- `OWNER` is the Twitch chat that the bot will run in.

## Running
To run the bot, perform setup if you have not already. Once setup is completed run ```python bot.py```
