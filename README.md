# telegram-support-bot
A telegram support bot to message to the channel or group admin.  
  
commands:  
/start  
/setlang  # Default: Perian and English  
/view  # Just for admin to see users messages  
/reply <user_ID> <message_to_user> # Just for admin to reply users messages 
  
# Install requirements by this command
pip install -r requirements.txt

# Customize the bot
Put your Bot Token, API_ID, API_HASH and your telegram ID as admin (not username with @, it's a number) in main.py file:  
APT_ID = ""  
API_HASH = ""  
BOT_TOKEN = ""  
ADMIN_CHAT_ID = ""  