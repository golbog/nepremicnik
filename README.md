# Nepremicnik

Scrapper for nepremicnine.net

## Requirements
  - Python 3.9+.
  - Additional required packages are listed in `requirements.txt`.  
Install them with: `pip install -r requirements`.
  - Telegram bot. Check this [tutorial](https://docs.microsoft.com/en-us/azure/bot-service/bot-service-channel-connect-telegram?view=azure-bot-service-4.0) to create new one.

## How to use
1. First create `appdata.json`. Check `appdata_example.json` to see required fields. Fill them with appropriate values.
    1. `BOT.TOKEN` - your bot's hidden token
    2. `BOT.GROUPD` - groups where the bot is added, and you want it to send messages
    3. `URLS` - nepremicnine.net search URLs
2. Run the program with Python: `python app.py`.   
Check `python app.py -h` for additional arguments.  
It is recommended to set up OS specific service that will run this program in intervals.
