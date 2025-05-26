import telebot
import sqlite3
import qrcode
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Создаем таблицу пользователей (если нет)
def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE,
                name TEXT,
                surname TEXT,
                middle_name TEXT,
                passport TEXT UNIQUE
            )
        ''')

init_db()

user_states = {}
user_data = {}


@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Регистрация", "Авторизация☀", "Генерация QR-Code")
    bot.send_message(message.chat.id, "Привет! Выбери действие:", reply_markup=markup)


@bot.message_handler(regexp='^Регистрация$')
def registration_start(message):
    bot.send_message(message.chat.id, "Введите имя:")
    user_states[message.chat.id] = 'awaiting_name'


@bot.message_handler(regexp='^Авторизация☀$')
def authorization_start(message):
    bot.send_message(message.chat.id, "Введите паспортные данные для авторизации:")
    user_states[message.chat.id] = 'awaiting_passport_auth'


@bot.message_handler(regexp='^Генерация QR-Code$')
def generate_qr(message):
    chat_id = message.chat.id
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, surname, middle_name, passport FROM users WHERE chat_id=?", (chat_id,))
        user = cur.fetchone()
    if user:
        name, surname, middle_name, passport = user
        qr_text = f"{name} {surname} {middle_name} | {passport}"
        img = qrcode.make(qr_text)
        bio = BytesIO()
        bio.name = 'qr.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        bot.send_photo(chat_id, photo=bio, caption="Ваш QR-код:")
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь!")



@bot.message_handler(func=lambda msg: True)
def message_handler(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    if state == 'awaiting_name':
        user_data[chat_id] = {'name': message.text}
        bot.send_message(chat_id, "Введите фамилию:")
        user_states[chat_id] = 'awaiting_surname'

    elif state == 'awaiting_surname':
        user_data[chat_id]['surname'] = message.text
        bot.send_message(chat_id, "Введите отчество:")
        user_states[chat_id] = 'awaiting_middle_name'

    elif state == 'awaiting_middle_name':
        user_data[chat_id]['middle_name'] = message.text
        bot.send_message(chat_id, "Введите паспортные данные:")
        user_states[chat_id] = 'awaiting_passport'

    elif state == 'awaiting_passport':
        user_data[chat_id]['passport'] = message.text
        data = user_data[chat_id]
        with sqlite3.connect("users.db") as conn:
            conn.execute('''
                INSERT OR REPLACE INTO users (chat_id, name, surname, middle_name, passport)
                VALUES (?, ?, ?, ?, ?)
            ''', (chat_id, data['name'], data['surname'], data['middle_name'], data['passport']))
        bot.send_message(chat_id, "Регистрация завершена! Вы можете сгенерировать QR-код.")
        user_states.pop(chat_id)
        user_data.pop(chat_id)

    elif state == 'awaiting_passport_auth':
        passport_input = message.text
        with sqlite3.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT name, surname, middle_name, passport FROM users WHERE passport=?", (passport_input,))
            user = cur.fetchone()
        if user:
            name, surname, middle_name, passport = user
            qr_text = f"{name} {surname} {middle_name} | {passport}"
            img = qrcode.make(qr_text)
            bio = BytesIO()
            bio.name = 'qr.png'
            img.save(bio, 'PNG')
            bio.seek(0)
            bot.send_photo(chat_id, photo=bio, caption=f"Авторизация успешна!\n\n{name} {surname} {middle_name}\nПаспорт: {passport}")
        else:
            bot.send_message(chat_id, "Пользователь не найден. Попробуйте еще раз.")
        user_states.pop(chat_id, None)

    else:
        bot.send_message(chat_id, "Введите /start чтобы начать.")

bot.infinity_polling()
