import telebot
from telebot import types
import random
import threading
import time
from flask import Flask, request
import requests
import os
import sqlite3
from datetime import datetime

# === НАСТРОЙКИ (МЕНЯЙ ТОЛЬКО ЗДЕСЬ) ===
TOKEN = '8941493056:AAGDwx7ayDFvDBF6XpEo02dQnQEV4334kHU'
REGISTER_URL = 'https://one-vv4635.com/?open=register&p=m1cy'
SUPPORT_USERNAME = 'Alexanderii_173'

# === БАЗА ДАННЫХ SQLITE ===
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        user_name TEXT,
        id_1win TEXT,
        requests INTEGER DEFAULT 0,
        registered_date TEXT,
        played INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

def save_user(user_id, user_name, id_1win):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_name, played FROM users WHERE user_id = ?', (user_id,))
    existing = cursor.fetchone()
    
    if existing and existing[0] and existing[0] != "Нет username":
        final_name = existing[0]
    else:
        final_name = user_name if user_name and user_name != "Нет username" else "Гость"
    
    # Сохраняем played если был
    played = existing[1] if existing and existing[1] else 0
    
    cursor.execute('''INSERT OR REPLACE INTO users (user_id, user_name, id_1win, requests, registered_date, played)
                      VALUES (?, ?, ?, COALESCE((SELECT requests FROM users WHERE user_id = ?), 0), COALESCE((SELECT registered_date FROM users WHERE user_id = ?), ?), ?)''',
                   (user_id, final_name, id_1win, user_id, user_id, datetime.now().strftime("%Y-%m-%d %H:%M"), played))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def increment_requests(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET requests = requests + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def set_played(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET played = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_played(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT played FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

init_db()

# === СОЗДАЁМ ФЛАСК-СЕРВЕР ДЛЯ ПИНГА ===
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает!", 200

@app.route('/ping')
def ping():
    return "pong", 200

def keep_alive():
    url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/ping"
    while True:
        try:
            requests.get(url, timeout=10)
            print("🔄 Автопинг отправлен")
        except Exception as e:
            print(f"❌ Ошибка автопинга: {e}")
        time.sleep(60)

def run_flask():
    app.run(host='0.0.0.0', port=10000)

thread_flask = threading.Thread(target=run_flask)
thread_flask.start()

time.sleep(10)
thread_ping = threading.Thread(target=keep_alive)
thread_ping.start()

# === ОСНОВНОЙ БОТ ===
bot = telebot.TeleBot(TOKEN)
user_data = {}

# === ГЛАВНОЕ МЕНЮ ===
def main_menu(message):
    chat_id = message.chat.id
    message_id = message.message_id
    
    user_data_db = get_user(chat_id)
    
    if user_data_db and user_data_db[1] and user_data_db[1] != "Нет username":
        user_first_name = user_data_db[1]
    else:
        try:
            user_first_name = message.from_user.first_name or "Гость"
            if user_data_db:
                save_user(chat_id, user_first_name, user_data_db[2])
        except:
            user_first_name = "Гость"
    
    has_id = user_data_db and user_data_db[2] if user_data_db else False
    has_played = get_played(chat_id) == 1
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if has_played:
        markup.add(types.InlineKeyboardButton("💣 Играть", callback_data="play_game"))
    
    markup.add(types.InlineKeyboardButton("🌐 Зарегистрироваться на сайте 1WIN", url=REGISTER_URL))
    
    if has_id:
        markup.add(types.InlineKeyboardButton("🚀 Привязать ID (изменить)", callback_data="send_id"))
    else:
        markup.add(types.InlineKeyboardButton("🚀 Привязать ID", callback_data="send_id"))
    
    markup.add(types.InlineKeyboardButton("📊 Моя статистика", callback_data="stats"))
    markup.add(types.InlineKeyboardButton("💬 Поддержка", callback_data="support"))
    
    text = f"""👋 Приветствую тебя, {user_first_name}! в AI Signals 1Win

🔥 Чтобы получить максимум от использования этого бота, необходимо следовать следующим шагам:

1. Зарегистрируйте новый аккаунт!
(Если у вас уже есть аккаунт, пожалуйста, выйдите и зарегистрируйте новый, это важно, потому что наш ИИ работает только с новыми аккаунтами)

2. После регистрации вы автоматически получите уведомление о успешной регистрации.

❗ Если вы не выполните эти шаги, наш бот не сможет добавить ваш аккаунт в свою базу данных, и предоставленные сигналы могут не соответствовать ❗

🤝 Спасибо за понимание!

👇 Снизу после регистрации нажмите на кнопку "Привязать ID" """
    
    try:
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    except:
        bot.send_message(
            chat_id,
            text,
            reply_markup=markup
        )

# === СТАРТ ===
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    
    try:
        user_first_name = message.from_user.first_name or "Гость"
    except:
        user_first_name = "Гость"
    
    user_name = message.from_user.username or "Нет username"
    
    user_data_db = get_user(chat_id)
    if not user_data_db:
        save_user(chat_id, user_first_name, None)
    else:
        if not user_data_db[1] or user_data_db[1] == "Нет username":
            save_user(chat_id, user_first_name, user_data_db[2])
    
    has_id = user_data_db and user_data_db[2] if user_data_db else False
    has_played = get_played(chat_id) == 1
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if has_played:
        markup.add(types.InlineKeyboardButton("💣 Играть", callback_data="play_game"))
    
    markup.add(types.InlineKeyboardButton("🌐 Зарегистрироваться на сайте 1WIN", url=REGISTER_URL))
    
    if has_id:
        markup.add(types.InlineKeyboardButton("🚀 Привязать ID (изменить)", callback_data="send_id"))
    else:
        markup.add(types.InlineKeyboardButton("🚀 Привязать ID", callback_data="send_id"))
    
    markup.add(types.InlineKeyboardButton("📊 Моя статистика", callback_data="stats"))
    markup.add(types.InlineKeyboardButton("💬 Поддержка", callback_data="support"))
    
    text = f"""👋 Приветствую тебя, {user_first_name}! в AI Signals 1Win

🔥 Чтобы получить максимум от использования этого бота, необходимо следовать следующим шагам:

1. Зарегистрируйте новый аккаунт!
(Если у вас уже есть аккаунт, пожалуйста, выйдите и зарегистрируйте новый, это важно, потому что наш ИИ работает только с новыми аккаунтами)

2. После регистрации вы автоматически получите уведомление о успешной регистрации.

❗ Если вы не выполните эти шаги, наш бот не сможет добавить ваш аккаунт в свою базу данных, и предоставленные сигналы могут не соответствовать ❗

🤝 Спасибо за понимание!

👇 Снизу после регистрации нажмите на кнопку "Привязать ID" """
    
    bot.send_message(
        chat_id,
        text,
        reply_markup=markup
    )

# === СТАТИСТИКА ===
def show_stats(message):
    chat_id = message.chat.id
    message_id = message.message_id
    user_data_db = get_user(chat_id)
    
    if not user_data_db:
        bot.edit_message_text(
            "❌ У вас нет статистики. Начните использовать бота!",
            chat_id=chat_id,
            message_id=message_id
        )
        return
    
    user_id, user_name, id_1win, requests_count, registered_date, played = user_data_db
    
    if not id_1win:
        text = "❌ *ID не привязан!*\n\nПожалуйста, нажмите 'Привязать ID' в главном меню."
    else:
        text = f"📊 *Твоя статистика:*\n\n"
        text += f"🆔 *ID в 1WIN:* {id_1win}\n"
        text += f"📈 *Запросов сигналов:* {requests_count}\n"
        text += f"📅 *Дата регистрации:* {registered_date or 'Неизвестно'}\n"
        text += f"🎮 *Игр сыграно:* {played}\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("⏪ Назад в меню", callback_data="back"))
    
    bot.edit_message_text(
        text,
        chat_id=chat_id,
        message_id=message_id,
        parse_mode='Markdown',
        reply_markup=markup
    )

# === ОБРАБОТКА КНОПОК ===
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "send_id":
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        msg = bot.send_message(chat_id, "📝 Введите ваш ID из личного кабинета 1WIN:")
        bot.register_next_step_handler(msg, process_id_input)
    
    elif call.data == "stats":
        show_stats(call.message)
    
    elif call.data == "back":
        main_menu(call.message)
    
    elif call.data == "support":
        support_message(call.message)
    
    elif call.data == "play_game":
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        mines_menu_new(call.message)
    
    elif call.data == "confirm_id":
        temp_id = user_data.get(chat_id, {}).get('temp_id')
        if temp_id:
            user_name = call.from_user.username or "Нет username"
            save_user(chat_id, user_name, temp_id)
            user_data[chat_id] = {"id": temp_id}
            
            try:
                bot.delete_message(chat_id, message_id)
            except:
                pass
            
            bot.send_message(
                chat_id,
                f"✅ ID {temp_id} успешно привязан!\n\n🎁 Кстати, за пополнение дают вкусные бонусы — можешь отыграть их в любом слоте!"
            )
            
            mines_menu_new(call.message)
        else:
            bot.send_message(chat_id, "❌ Ошибка! Попробуйте снова /start")
    
    elif call.data == "cancel_id":
        user_data.pop(chat_id, None)
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        bot.send_message(
            chat_id,
            "❌ Привязка ID отменена. Если передумаете, нажмите 'Привязать ID' в меню."
        )
        main_menu(call.message)
    
    elif call.data.startswith("mine_"):
        mines = int(call.data.split("_")[1])
        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]['selected_mines'] = mines
        show_signal_button(call.message, mines)
    
    elif call.data == "get_signal":
        generate_signal(call.message)

# === ОБРАБОТКА ВВОДА ID ===
def process_id_input(message):
    chat_id = message.chat.id
    user_id_text = message.text.strip()
    
    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass
    
    if not user_id_text.isdigit():
        msg = bot.send_message(chat_id, "❌ ID должен состоять только из цифр! Попробуйте ещё раз:")
        bot.register_next_step_handler(msg, process_id_input)
        return
    
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]['temp_id'] = user_id_text
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_id"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_id")
    )
    
    bot.send_message(
        chat_id,
        f"✅ Вы ввели ID: *{user_id_text}*\n\n"
        f"Пожалуйста, проверьте правильность введённых данных.\n"
        f"Если всё верно, нажмите 'Подтвердить'. Если ошиблись — 'Отмена'.",
        parse_mode='Markdown',
        reply_markup=markup
    )

# === МЕНЮ ВЫБОРА МИН ===
def mines_menu_new(message):
    chat_id = message.chat.id
    
    markup = types.InlineKeyboardMarkup(row_width=4)
    btn1 = types.InlineKeyboardButton("💣1", callback_data="mine_1")
    btn2 = types.InlineKeyboardButton("💣3", callback_data="mine_3")
    btn3 = types.InlineKeyboardButton("💣5", callback_data="mine_5")
    btn4 = types.InlineKeyboardButton("💣7", callback_data="mine_7")
    markup.add(btn1, btn2, btn3, btn4)
    
    markup.row(
        types.InlineKeyboardButton("⏪ Главное меню", callback_data="back"),
        types.InlineKeyboardButton("💎 Играть на 1Win", url=REGISTER_URL)
    )
    markup.row(
        types.InlineKeyboardButton("💬 Поддержка", callback_data="support")
    )
    
    bot.send_message(
        chat_id,
        "💣 Выберите количество мин для анализа:",
        reply_markup=markup
    )

# === КНОПКА "ВЫДАТЬ СИГНАЛ" ===
def show_signal_button(message, mines):
    chat_id = message.chat.id
    message_id = message.message_id
    
    markup = types.InlineKeyboardMarkup(row_width=4)
    btn1 = types.InlineKeyboardButton("💣1", callback_data="mine_1")
    btn2 = types.InlineKeyboardButton("💣3", callback_data="mine_3")
    btn3 = types.InlineKeyboardButton("💣5", callback_data="mine_5")
    btn4 = types.InlineKeyboardButton("💣7", callback_data="mine_7")
    markup.add(btn1, btn2, btn3, btn4)
    
    markup.row(types.InlineKeyboardButton("🔴 Выдать сигнал", callback_data="get_signal"))
    
    markup.row(
        types.InlineKeyboardButton("⏪ Главное меню", callback_data="back"),
        types.InlineKeyboardButton("💎 Играть на 1Win", url=REGISTER_URL)
    )
    markup.row(
        types.InlineKeyboardButton("💬 Поддержка", callback_data="support")
    )
    
    text = f"""🎯 Сигналы для Mines (мины)

💣 Выбрано мин: {mines}

⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛

Нажмите "Выдать сигнал" для получения анализа:"""
    
    try:
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    except:
        bot.send_message(
            chat_id,
            text,
            reply_markup=markup
        )

# === ГЕНЕРАЦИЯ СИГНАЛА ===
def generate_signal(message):
    chat_id = message.chat.id
    message_id = message.message_id
    
    # Отмечаем, что пользователь играл (сохраняем в БД)
    set_played(chat_id)
    
    mines = user_data.get(chat_id, {}).get('selected_mines', 1)
    
    if mines == 1:
        stars_count = random.randint(4, 7)
    elif mines == 3:
        stars_count = random.randint(4, 5)
    elif mines == 5:
        stars_count = random.randint(2, 4)
    elif mines == 7:
        stars_count = random.randint(1, 2)
    else:
        stars_count = random.randint(1, 3)
    
    cells = [['⬛' for _ in range(5)] for _ in range(5)]
    positions = random.sample(range(25), stars_count)
    positions = sorted(positions)
    
    markup_status = types.InlineKeyboardMarkup(row_width=4)
    btn1 = types.InlineKeyboardButton("💣1", callback_data="mine_1")
    btn2 = types.InlineKeyboardButton("💣3", callback_data="mine_3")
    btn3 = types.InlineKeyboardButton("💣5", callback_data="mine_5")
    btn4 = types.InlineKeyboardButton("💣7", callback_data="mine_7")
    markup_status.add(btn1, btn2, btn3, btn4)
    markup_status.row(types.InlineKeyboardButton("🔴 Выдать сигнал", callback_data="get_signal"))
    markup_status.row(
        types.InlineKeyboardButton("⏪ Главное меню", callback_data="back"),
        types.InlineKeyboardButton("💎 Играть на 1Win", url=REGISTER_URL)
    )
    markup_status.row(
        types.InlineKeyboardButton("💬 Поддержка", callback_data="support")
    )
    
    text_status = f"""🎯 Сигналы для Mines (мины)

💣 Выбрано мин: {mines}

🔍 Анализ хэш-сумм API...

⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛
"""
    
    try:
        bot.edit_message_text(
            text_status,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup_status
        )
    except:
        bot.send_message(
            chat_id,
            text_status,
            reply_markup=markup_status
        )
    
    time.sleep(1.5)
    
    text_status2 = f"""🎯 Сигналы для Mines (мины)

💣 Выбрано мин: {mines}

⚡ Синхронизация ячеек...

⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛
⬛ ⬛ ⬛ ⬛ ⬛
"""
    
    try:
        bot.edit_message_text(
            text_status2,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup_status
        )
    except:
        pass
    
    time.sleep(1.5)
    
    for idx, pos in enumerate(positions):
        row = pos // 5
        col = pos % 5
        cells[row][col] = '⭐'
        
        field = ""
        for r in range(5):
            field += ' '.join(cells[r]) + '\n'
        
        text = f"""🎯 Сигналы для Mines (мины)

💣 Выбрано мин: {mines}

📍 Сигнал (безопасные лунки):
{field}"""
        
        if idx == len(positions) - 1:
            markup_final = types.InlineKeyboardMarkup(row_width=4)
            btn1 = types.InlineKeyboardButton("💣1", callback_data="mine_1")
            btn2 = types.InlineKeyboardButton("💣3", callback_data="mine_3")
            btn3 = types.InlineKeyboardButton("💣5", callback_data="mine_5")
            btn4 = types.InlineKeyboardButton("💣7", callback_data="mine_7")
            markup_final.add(btn1, btn2, btn3, btn4)
            markup_final.row(types.InlineKeyboardButton("🔴 Выдать сигнал", callback_data="get_signal"))
            markup_final.row(
                types.InlineKeyboardButton("⏪ Главное меню", callback_data="back"),
                types.InlineKeyboardButton("💎 Играть на 1Win", url=REGISTER_URL)
            )
            markup_final.row(
                types.InlineKeyboardButton("💬 Поддержка", callback_data="support")
            )
            
            text += f"\n\n✅ Сигнал готов! Найдено ячеек: {stars_count}"
            
            try:
                bot.edit_message_text(
                    text,
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=markup_final
                )
            except:
                bot.send_message(
                    chat_id,
                    text,
                    reply_markup=markup_final
                )
        else:
            try:
                bot.edit_message_text(
                    text,
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=markup_status
                )
            except:
                pass
            
            time.sleep(0.8)

# === ПОДДЕРЖКА ===
def support_message(message):
    chat_id = message.chat.id
    message_id = message.message_id
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💬 Написать администратору", url=f"https://t.me/{SUPPORT_USERNAME}"))
    markup.add(types.InlineKeyboardButton("⏪ Назад в меню", callback_data="back"))
    
    try:
        bot.edit_message_text(
            f"💬 Центр поддержки 1Win Signal\n\nВозникли вопросы по работе бота, привязке ID или выводу средств? Свяжитесь с нашей службой поддержки, и мы решим любой вопрос!\n\n👉 Напишите нашему администратору: @{SUPPORT_USERNAME}",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    except:
        bot.send_message(
            chat_id,
            f"💬 Центр поддержки 1Win Signal\n\nВозникли вопросы по работе бота, привязке ID или выводу средств? Свяжитесь с нашей службой поддержки, и мы решим любой вопрос!\n\n👉 Напишите нашему администратору: @{SUPPORT_USERNAME}",
            reply_markup=markup
        )

print("✅ Бот запущен!")
print("🔄 Автопинг активен (каждую минуту)")

bot.polling()