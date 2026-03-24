from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import smtplib
from email.mime.text import MIMEText
import imaplib
import email
import threading
import asyncio
import time
import uuid
import os

# ===== CONFIG (AMBIL DARI RAILWAY VARIABLES) =====
TOKEN = os.getenv("TOKEN")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TUJUAN = "support@support.whatsapp.com"

print("TOKEN =", TOKEN)
print("EMAIL =", EMAIL)
print("PASSWORD =", PASSWORD)

# ===== DATABASE =====
requests_db = {}

# ===== KIRIM EMAIL =====
def kirim_email(no_hp, request_id):
    isi = f"Halo WhatsApp Support\nNomor: {no_hp}\nNOMOR: {request_id}"

    msg = MIMEText(isi)
    msg['Subject'] = f"WA {request_id}"
    msg['From'] = EMAIL
    msg['To'] = TUJUAN

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.send_message(msg)
    server.quit()

# ===== KIRIM NOTIF TELEGRAM =====
async def kirim_notif(app, chat_id, req_id):
    await app.bot.send_message(
        chat_id,
        f"📩 BALASAN MASUK!\nNOMOR: {req_id}"
    )

# ===== CEK EMAIL BACKGROUND =====
def cek_email_background(app):
    processed = set()

    while True:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(EMAIL, PASSWORD)
            mail.select("inbox")

            status, messages = mail.search(None, "ALL")

            for num in messages[0].split():
                if num in processed:
                    continue

                res, msg_data = mail.fetch(num, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                pengirim = msg.get("From", "").lower()
                subject = msg.get("Subject", "")

                print("EMAIL:", pengirim, subject)

                if "support.whatsapp.com" in pengirim:
                    for req_id in requests_db:
                        if requests_db[req_id]["status"] == "waiting":

                            chat_id = requests_db[req_id]["chat_id"]

                            asyncio.run(
                                kirim_notif(app, chat_id, req_id)
                            )

                            requests_db[req_id]["status"] = "done"
                            break

                processed.add(num)

            mail.logout()

        except Exception as e:
            print("ERROR:", e)

        time.sleep(15)

# ===== COMMAND START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot siap 🚀\nGunakan /wa 628xxxx")

# ===== COMMAND WA =====
async def wa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Masukkan nomor!")
        return

    nomor = context.args[0]

    # 🔥 ID DIGANTI JADI NOMOR
    request_id = nomor

    requests_db[request_id] = {
        "chat_id": update.effective_chat.id,
        "status": "waiting"
    }

    kirim_email(nomor, request_id)

    await update.message.reply_text(
        f"✅ Email terkirim\nNOMOR: {request_id}\nMenunggu balasan..."
    )

# ===== MAIN =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("wa", wa))

# BACKGROUND THREAD
threading.Thread(target=cek_email_background, args=(app,), daemon=True).start()

print("BOT JALAN...")
app.run_polling()
