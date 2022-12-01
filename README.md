# Vantchko-Quotebot

A Twitch/Youtube chat bot for quote tracking.

## Setup
### Python Setup

This project uses python 3 and requires the datetime and the irc modules. This can be installed using pip by using ```pip install -r requirements.txt ```.

### Twitch Setup

To setup the Twitch bot, you must first make a Twitch account for your bot to post from (unless you want it to post from your own account). While logged into the
account the bot will post from, obtain a Twitch tmi token.

### Youtube Setup

To setup the Youtube bot, first make a youtube account/channel for the bot to post to and confirm that you can chat as that user within your livestream. Follow the instructions to create credentials for OAuth 2.0 from [the Youtube API Documentation](https://developers.google.com/youtube/v3/live/registering_an_application). Download and save the client configuration file as `credentials_youtube.json`.

If you don't run the YouTube bot for a while, you may run into an authorization error. To fix it, delete the `token_youtube.json` file and run the bot again.

### Google Sheets Setup

Firstly, go to https://developers.google.com/sheets/api/quickstart/python#step_1_turn_on_the and click the button labeled "Enable the Google Sheets API". Enter a project name, then select Desktop app from the dropdown menu. Press "DOWNLOAD CLIENT CONFIGURATION" and save the
resulting `credentials.json` file to the project directory.
Next, create a spreadsheet for the quotes to be placed in and generate a shared link where people with the link can view the spreadsheet.

If you don't run the bot for a while, you may run into an authorization error. To fix it, delete the `token.json` file and run the bot again.

## Running

To run the bot, perform setup if you have not already. Once setup is completed run ```python bot.py <youtube|twitch>```

The first time you run the bot, you will be prompted for several variables:
- First you will be prompted for the id of the Google Sheet to be used for the quotes. This can be obtained from the URL of the sheet, in the format `docs.google.com/spreadsheets/d/<your_id_here>/edit`.
- Second you will be prompted for the range of the spreadsheet that is to be used for quotes in the format `<sheet_name>!<range>`. For example, if the primary sheet within the spreadsheet file is name `Quotes` and you would like quotes to fill the first column, the range should be `Quotes!A:A`.
- Third you will be prompted for the shared link generated in the Google Sheets setup.

The first time you run the Twitch bot specifically, you will be prompted for several variables:
- First you will be asked for your token, which is the TMI token obtained during twitch setup.
- Second you will be prompted for the name of the account that the bot will be posting from. This account must be the account used to obtain the TMI token.
- Third you will be prompted for your channel name.

To change any of these settings, you can modify the `settings.json` file manually or delete it in order to redo the prompts

Every time you run the youtube bot, you will be prompted for the stream ID. To get this, open the stream in a web browser and copy the ID from the URL bar (it will be a sequence of letters and numbers after the `=` in `https://youtube.com/watch?v=<YOUR ID HERE>`)
