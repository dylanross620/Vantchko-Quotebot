# Vantchko-Quotebot
A Twitch chat bot for quote tracking.

## Setup
### Python Setup
This project uses python 3 and requires the datetime and the irc modules. This can be installed using pip by using ```pip install -r requirements.txt ```.

### Twitch Setup
To setup the Twitch bot, you must first make a Twitch account for your bot to post from (unless you want it to post from your own account). While logged into the
account the bot will post from, obtain a Twitch tmi token.

### Google Sheets Setup
Firstly, go to https://developers.google.com/sheets/api/quickstart/python#step_1_turn_on_the and click the button labeled "Enable the Google Sheets API". Enter a project name, then select Desktop app from the dropdown menu. Press "DOWNLOAD CLIENT CONFIGURATION" and save the
resulting `credentials.json` file to the project directory.
Next, create a spreadsheet for the quotes to be placed in and generate a shared link where people with the link can view the spreadsheet.

## Running
To run the bot, perform setup if you have not already. Once setup is completed run ```python bot.py```

The first time you run the bot, you will be prompted for several variables:
- First you will be asked for your token, which is the TMI token obtained during twitch setup.
- Second you will be prompted for the name of the account that the bot will be posting from. This account must be the account used to obtain the TMI token.
- Third you will be prompted for your channel name.
- Fourth you will be prompted for the id of the Google Sheet to be used for the quotes. This can be obtained from the URL of the sheet, in the format `docs.google.com/spreadsheets/d/<your_id_here>/edit`.
- Fifth you will be prompted for the range of the spreadsheet that is to be used for quotes in the format `<sheet_name>!<range>`. For example, if the primary sheet within the spreadsheet file is name `Quotes` and you would like quotes to fill the first column, the range should be `Quotes!A:A`.
- Sixth you will be prompted for the shared link generated in the Google Sheets setup.

To change any of these settings, you can modify the `settings.json` file manually or delete it in order to redo the prompts
