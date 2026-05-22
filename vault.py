from flask import Flask, request
import psycopg2
import requests
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
app = Flask(__name__)

# ---------------- DATABASE ---------------- #

def db_connection():
    return psycopg2.connect(DATABASE_URL)


def db_creation():

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data (
        id SERIAL PRIMARY KEY ,
        gender TEXT,
        username TEXT,
        gmail TEXT,
        password TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


db_creation()

# ---------------- TELEGRAM ---------------- #

def reply_message(chat_id, text):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })


# ---------------- ROUTE ---------------- #

@app.route(f"/{TOKEN}", methods=["POST"])
def frontend():

    data = request.get_json()

    if not data:
        return "ok"

    message = data.get("message")

    if not message:
        return "ok"

    chat_id = message["chat"]["id"]

    text = message.get("text", "").strip()

    user = message.get("from", {})
    username = user.get("first_name", "User")

    # ---------------- START ---------------- #

    if text == "/start":

        reply = (
            f"👋 *Welcome {username}*\n\n"
            f"This is your private vault bot.\n\n"
            f"📌 Save account info quickly\n"
            f"📂 View saved accounts anytime\n"
            f"⚡ Fast & simple experience\n\n"
            f"*Commands*\n"
            f"`/help` → Usage guide\n"
            f"`/dashboard` → View saved accounts"
        )

        reply_message(chat_id, reply)

    # ---------------- HELP ---------------- #

    elif text == "/help":

        reply = (
            "🛠 *How To Use*\n\n"
            "*Save account format:*\n"
            "`Gender Username Gmail Password`\n\n"
            "*Example:*\n"
            "`Male John john@gmail.com 1234`\n\n"
            "*Commands*\n"
            "`/start` → Start bot\n"
            "`/help` → Help menu\n"
            "`/dashboard` → View saved accounts"
        )

        reply_message(chat_id, reply)

    # ---------------- DASHBOARD ---------------- #

    elif text == "/dashboard":

        conn = db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT gender, username, gmail, password, date
        FROM data
        ORDER BY id DESC
        """)

        rows = cursor.fetchall()

        conn.close()

        if not rows:

            reply = (
                "📭 *Vault Empty*\n\n"
                "No saved accounts found."
            )

            reply_message(chat_id, reply)

            return "ok"

        reply_message(
            chat_id,
            f"📂 *Dashboard*\n\n"
            f"Total Accounts: *{len(rows)}*"
        )

        for index, row in enumerate(rows, start=1):

            gender, user_name, gmail, password, date = row

            card = (
                f"━━━━━━━━━━━━━━\n"
                f"🔐 *Account #{index}*\n\n"
                f"👤 Username: `{user_name}`\n"
                f"📧 Gmail: `{gmail}`\n"
                f"🔑 Password: `{password}`\n"
                f"🧬 Gender: `{gender}`\n"
                f"📅 Saved: `{date}`\n"
                f"━━━━━━━━━━━━━━"
            )

            reply_message(chat_id, card)

    # ---------------- SAVE DATA ---------------- #

    else:

        parts = text.split()

        if len(parts) < 4:

            reply = (
                "❌ *Invalid Format*\n\n"
                "Use:\n"
                "`Gender Username Gmail Password`\n\n"
                "*Example:*\n"
                "`Male John john@gmail.com 1234`"
            )

            reply_message(chat_id, reply)

            return "ok"
        try:

            gender = parts[0]
            user_name = parts[1]
            gmail = parts[2]
            password = parts[3]

            conn = db_connection()
            cursor = conn.cursor()

            now = datetime.now().strftime("%Y-%m-%d")

            cursor.execute("""
            INSERT INTO data (
                gender,
                username,
                gmail,
                password,
                date
            )
            VALUES (%s, %s, %s, %s, %s)
            """, (
                gender,
                user_name,
                gmail,
                password,
                now
            ))

            conn.commit()
            conn.close()

            reply = (
                "✅ *Account Saved Successfully*\n\n"
                f"👤 Username: `{user_name}`\n"
                f"📧 Gmail: `{gmail}`\n"
                f"📅 Date: `{now}`\n\n"
                f"🔒 Stored securely in your vault."
            )

            reply_message(chat_id, reply)

        except IndexError:

            reply = (
                "⚠️ *Incomplete Information*\n\n"
                "Please use this format:\n\n"
                "`Gender Username Gmail Password`\n\n"
                "*Example*\n"
                "`Male John john@gmail.com 1234`"
            )

            reply_message(chat_id, reply)

        except psycopg2.Error:

            reply = (
                "🛑 *Database Error*\n\n"
                "Unable to save your account right now.\n"
                "Please try again later."
            )

            reply_message(chat_id, reply)

        except Exception as e:

            print(e)

            reply = (
                "❌ *Unexpected Error*\n\n"
                "Something went wrong while processing your request."
            )

            reply_message(chat_id, reply)

    return "ok"


# ---------------- RUN ---------------- #

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )