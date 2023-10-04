import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, InlineQueryHandler
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#postgres://tiktok_ethiopia_user:787ddC53ERWXkZdYjiiNHhQ5ACDVqri9@dpg-ckbvu76ct0pc738n81b0-a.oregon-postgres.render.com/tiktok_ethiopia
db_params = {
    'host': 'dpg-ckbvu76ct0pc738n81b0-a.oregon-postgres.render.com',
    'database': 'tiktok_ethiopia',
    'user': 'tiktok_ethiopia_user',
    'password': '787ddC53ERWXkZdYjiiNHhQ5ACDVqri9'
}
while True:
    try:
        conn = psycopg2.connect(**db_params, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print('Database connection was successful')
        break

    except Exception as error:
        print("Connection to database failed")
        print("Error: ", error)
        time.sleep(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send an initial message to prompt the user for a link
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome, please enter a link to your channel."
    )

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    # Check if the message looks like a link
    if is_valid_url(user_message):
        received_link = re.search(r'https?://\S+', user_message).group()
        cursor.execute("""INSERT INTO users (link, chat_id) VALUES (%s, %s)""", (received_link, update.effective_chat.id))
        
        conn.commit()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Thank you for providing the link: {received_link}"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, I don't think that is quite right. Please enter a valid link."
        )

def is_valid_url(text):
    # This regular expression pattern checks for a typical URL format
    url_pattern = r'(https?|ftp|file|mailto)://[\w~\/:%#\$&\?\(\)~\.=\+\-]+(\?[\w~\/:%#\$&\?\(\)~\.=\+\-]*)?(#[\w~\/:%#\$&\?\(\)~\.=\+\-]*)?'

    return re.search(url_pattern, text)

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("""SELECT chat_id, link from users where shared_status=false ORDER BY last_shared""")
    result = cursor.fetchone()
    if result is None:
        default_values = {
            'chat_id': 6081026054,
            'link': "https://www.youtube.com/watch?v=W9q-0tCfvKE"
        }
        result = default_values

    chat_id = result['chat_id']
    link = result['link']
    cursor.execute("""UPDATE users SET shared_status=true where chat_id=%s""", (chat_id,))
    cursor.execute("""UPDATE users SET viewing=%s where chat_id=%s""", (chat_id, update.effective_chat.id))
    conn.commit()


    await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Send the message /subscribed when your subscription is complete " + link
        )
    

async def subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("""SELECT viewing FROM users WHERE chat_id=%s""", (update.effective_chat.id,))

    result = cursor.fetchone()

    if result is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please press /subscribe first"
        )
        return

    cursor.execute("""
    UPDATE users 
    SET last_shared = CASE 
        WHEN shares = 0 THEN NOW() 
        ELSE last_shared 
    END,
    shares = shares + 1 
    WHERE chat_id = %s
""", (update.effective_chat.id,))
    
    cursor.execute("""UPDATE users SET shares = shares - 1, last_shared = NOW(), shared_status = false where chat_id = %s""", (result["viewing"],))
    conn.commit()
    await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Thank You for subscribing, now someone else will subscribe to you"
        )
    await context.bot.send_message(
            chat_id=result["viewing"],
            text="A new user should have subscribed to you, /report if they haven't"
        )


async def already_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("""SELECT viewing FROM users WHERE chat_id=%s""", (update.effective_chat.id,))
    result = cursor.fetchone()
    if result is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please press /subscribe first"
        )
        return
    
    subscribed_id = result["viewing"]
    cursor.execute("""UPDATE users SET shared_status = false where chat_id = %s""", (subscribed_id,))

    cursor.execute("""SELECT chat_id, link from users where shared_status=false ORDER BY last_shared""")
    result = cursor.fetchone()
    chat_id = result['chat_id']
    link = result['link']

    cursor.execute("""UPDATE users SET shared_status=true where chat_id=%s""", (chat_id,))
    cursor.execute("""UPDATE users SET viewing=%s where chat_id=%s""", (chat_id, update.effective_chat.id))
    
    
    conn.commit()
    await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry for the inconvinience, here is a new link " + link
        )
    
async def checkForAssholes():
    while True:
        await asyncio.sleep(6000)
        print("Asshole Damage cleared")
        cursor.execute("""UPDATE users
SET shared_status = false
WHERE last_shared IS NOT NULL
  AND EXTRACT(EPOCH FROM (NOW() - last_shared)) > 600;""" )
        conn.commit()
        
if __name__ == '__main__':
    application = ApplicationBuilder().token('6533909241:AAFSwMipYM1Fd6l9iS6A50J5dRhN-BrvjrM').build()

    
    loop = asyncio.get_event_loop()
    loop.create_task(checkForAssholes())
    start_handler = CommandHandler('start', start)
    subscribe_handler = CommandHandler('subscribe', subscribe)
    subscribed_handler = CommandHandler('subscribed', subscribed)
    already_subscribed_handler = CommandHandler('already_subscribed', already_subscribed)
    process_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), process_message)
    
    application.add_handler(subscribed_handler)
    application.add_handler(already_subscribed_handler)
    application.add_handler(start_handler)
    application.add_handler(subscribe_handler)
    application.add_handler(process_handler)

    
    
    application.run_polling()
    



#'6533909241:AAFSwMipYM1Fd6l9iS6A50J5dRhN-BrvjrM'


