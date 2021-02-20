# Vantchko-Quotebot
A Twitch chat bot for quote tracking.

## Setup
### Python Setup
This project uses python 3 and requires the datetime and the irc modules. This can be installed using pip by using ```pip install -r requirements.txt ```.

### Twitch Setup
To setup the Twitch bot, you must first make a Twitch account for your bot to post from (unless you want it to post from your own account). While logged into the
account the bot will post from, obtain a Twitch tmi token. This token must be saved to a file called `token.env`.

In addition to setting up the Twitch token, you also must open the file ```bot.py``` and modify some variables found at the top of the file:
- `NAME` is the name of the account the bot will be posting from. This should match the name of the account you retrieved your token with.
- `OWNER` is the Twitch chat that the bot will run in.

### Google Sheets Setup
Firstly, go to https://developers.google.com/sheets/api/quickstart/python#step_1_turn_on_the and click the button labeled "Enable the Google Sheets API". Enter a project name, then select Desktop app from the dropdown menu. Press "DOWNLOAD CLIENT CONFIGURATION" and save the
resulting `credentials.json` file to the project directory.
Next, create a spreadsheet for the quotes to be placed in and generate a shared link where people with the link can view the spreadsheet. Then fill in the following variables in ```bot.py```:
- `SPREADSHEET_ID` is the id of the spreadsheet you made it can be found in the url as `docs.google.com/spreadsheets/d/<your_id_here>/edit`.
- `RANGE_NAME` should be in the form of `<sheet 1 name>!A:A`.
- `READ_LINK` should be the shareable viewing link you created above.

## Running
To run the bot, perform setup if you have not already. Once setup is completed run ```python bot.py```
