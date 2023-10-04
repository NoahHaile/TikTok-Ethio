import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, InlineQueryHandler
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import asyncio

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

cursor.execute("""CREATE TABLE public.users (
    chat_id bigint NOT NULL,
    link character varying NOT NULL,
    shares integer DEFAULT 0 NOT NULL,
    last_shared timestamp with time zone DEFAULT now(),
    viewing bigint,
    shared_status boolean DEFAULT false NOT NULL
);""")

conn.commit()