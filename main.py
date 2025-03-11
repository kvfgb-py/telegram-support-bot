from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from translations import translations
import json
import uvloop

bot_token = ""
api_id = ""
api_hash = ""
admin = "" # Put your ID not username with @

Your_support_bot_name = "@" # Put your support bot name
your_bot_or_channel = "@" # Put your channel or bot username with @

uvloop.install()

app = Client("support_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Load translations
try:
    with open("user_languages.json", "r", encoding="utf-8") as file:
        user_preferences = json.load(file)
except FileNotFoundError:
    # If the file doesn't exist, start with an empty dictionary
    user_preferences = {}

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect("support_bot.db")
    conn.row_factory = sqlite3.Row
    return conn

# Function to create the table (run once to initialize the database)
def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
create_table()

# Start command
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = str(message.from_user.id)  # Save user ID as string for JSON compatibility
    user_language = user_preferences.get(user_id, "en")  # Default to English
    await message.reply_text(f"{translations[user_language]["welcome"]}".format(Your_support_bot_name=Your_support_bot_name ,
                                                                                your_bot_or_channel=your_bot_or_channel))

@app.on_message(filters.command("setlang"))
async def set_language(client, message):
    # Create buttons for language selection
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("English", callback_data="lang_en"), InlineKeyboardButton("فارسی", callback_data="lang_fa")]
    ])
    
    await message.reply_text("Please choose your language:", reply_markup=buttons)

# Callback handler for button clicks
@app.on_callback_query()
async def handle_language_selection(client, callback_query):
    user_id = str(callback_query.from_user.id)
    data = callback_query.data

    if data == "lang_en":
        # Set language to English
        user_preferences[user_id] = "en"
        response = translations["en"]["language_changed"]
    elif data == "lang_fa":
        # Set language to Persian (Farsi)
        user_preferences[user_id] = "fa"
        response = translations["fa"]["language_changed"]
    else:
        # Handle unexpected callback data
        await callback_query.answer("Invalid selection.")
        return

    # Save updated preferences to the JSON file
    with open("user_languages.json", "w", encoding="utf-8") as file:
        json.dump(user_preferences, file, ensure_ascii=False, indent=4)

    # Notify user of the language change
    await callback_query.answer(response)
    await callback_query.message.edit_text(response)

# Admin command to view all messages
@app.on_message(filters.private & filters.user(admin) & filters.command("view"))
async def view_messages(client, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_messages")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        response = "**User Messages:**\n\n"
        for row in rows:
            response += (
                f"ID: `{row['user_id']}`\n"
                f"Username: @{row['username']}\n" # If user has no username it shows @none
                f"Message: {row['message']}\n"
                f"Timestamp: {row['timestamp']}\n\n"
            )
        await message.reply_text(response)
    else:
        await message.reply_text("No messages from users.")

@app.on_message(filters.private & filters.command("reply"))
async def reply_to_user(client, message):
    try:
        user_id = str(message.from_user.id)  # Save user ID as string for JSON compatibility
        user_language = user_preferences.get(user_id, "en")  # Default to English
        int_user_id = message.from_user.id
        if int_user_id != admin:
            await message.reply_text(translations[user_language]["reply_message"])
            return
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            await message.reply_text("Usage: /reply <user_id> <message>")
            return

        user_id = int(args[1])  # Extract the user ID
        reply_message = args[2]  # Extract the reply message

        # Send the reply to the user
        await app.send_message(chat_id=user_id, text=reply_message)
        await message.reply_text(f"Message sent to user ID: {user_id}")

        # Delete the user's message from the database
        conn = get_db_connection()
        conn.execute("DELETE FROM user_messages WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

        await message.reply_text(f"Message from user ID {user_id} has been removed from the database.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")

# Save user messages to the database
@app.on_message(filters.private & ~filters.bot)
async def save_user_message(client, message):
    int_user_id = message.from_user.id
    if int_user_id == admin:
        await message.reply_text("You are admin. You can't send message to yourself.")
        return
    username = message.from_user.username or "No Username"
    text = message.text or "No Text"

    user_id = str(message.from_user.id)  # Save user ID as string for JSON compatibility
    user_language = user_preferences.get(user_id, "en")  # Default to English

    # Save the message to the database
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO user_messages (user_id, username, message) VALUES (?, ?, ?)",
        (user_id, username, text)
    )
    conn.commit()
    conn.close()

    await message.reply_text(translations[user_language]["user_messages"])

# Run the bot
app.run()
