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

# === ТОКЕН БОТА ===
TOKEN = '8941493056:AAGDwx7ayDFvDBF6XpEo02dQnQEV4334kHU'

# === БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        user_name TEXT,
        id_1win TEXT,
        language TEXT DEFAULT 'ru',
        requests INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_user(user_id, user_name=None, id_1win=None, language=None, requests=None):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    user = get_user(user_id)
    if user:
        if user_name:
            cursor.execute('UPDATE users SET user_name = ? WHERE user_id = ?', (user_name, user_id))
        if id_1win:
            cursor.execute('UPDATE users SET id_1win = ? WHERE user_id = ?', (id_1win, user_id))
        if language:
            cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
        if requests is not None:
            cursor.execute('UPDATE users SET requests = ? WHERE user_id = ?', (requests, user_id))
    else:
        cursor.execute('INSERT INTO users (user_id, user_name, id_1win, language, requests) VALUES (?, ?, ?, ?, ?)',
                       (user_id, user_name or '', id_1win or '', language or 'ru', requests or 0))
    conn.commit()
    conn.close()

def increment_requests(user_id):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET requests = requests + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# === ТЕКСТЫ ДЛЯ ЛОКАЛИЗАЦИИ ===
TEXTS = {
    'ru': {
        'welcome': '👋 Приветствую тебя, {}! в AI Signals 1Win\n\n🔥 Чтобы получить максимум от использования этого бота, необходимо следовать следующим шагам:\n\n1. Зарегистрируйте новый аккаунт!\n(Если у вас уже есть аккаунт, пожалуйста, выйдите и зарегистрируйте новый, это важно, потому что наш ИИ работает только с новыми аккаунтами)\n\n2. После регистрации вы автоматически получите уведомление о успешной регистрации.\n\n❗ Если вы не выполните эти шаги, наш бот не сможет добавить ваш аккаунт в свою базу данных, и предоставленные сигналы могут не соответствовать ❗\n\n🤝 Спасибо за понимание!\n\n👇 Снизу после регистрации нажмите на кнопку "Привязать ID"',
        'enter_id': '📝 Введите ваш ID из личного кабинета 1WIN:',
        'confirm_id': '📝 Вы ввели ID: {}\n\n✅ Всё верно? Подтвердите:',
        'id_success': '✅ ID {} успешно привязан!\n\n🎁 Кстати, за пополнение дают вкусные бонусы — можешь отыграть их в любом слоте!\n\n💣 Выберите количество мин для анализа раунда:',
        'stats': '📊 Твоя статистика:\n\n🆔 ID: {}\n📈 Запросов: {}\n🗂️ Язык: {}',
        'choose_mines': '💣 Выберите количество мин для анализа раунда:',
        'analysis': '⚙️ Анализ параметров:\n💣 Количество мин: {}\n🎯 Вероятность успеха: {}%\n📊 Ожидаемый коэффициент (Шаг 1): {}x\n\n📍 Сигнал (безопасные лунки):\n{}\n\n🔄 Выберите другое количество или перейдите к игре:',
        'language_changed': '🌍 Язык изменён на Русский!',
        'support': '💬 Центр поддержки 1Win Signal\n\nВозникли вопросы по работе бота, привязке ID или выводу средств? Свяжитесь с нашей службой поддержки, и мы решим любой вопрос!\n\n👉 Напишите нашему администратору: @Alexanderii_173',
        'back': '⏪ Назад в меню',
        'play': '💎 Играть на 1Win',
        'register': '🌐 Зарегистрироваться на сайте 1WIN',
        'bind_id': '🚀 Привязать ID',
        'support_btn': '💬 Поддержка',
        'stats_btn': '📊 Статистика',
        'lang_btn': '🌍 Язык',
        'confirm': '✅ Подтвердить',
        'cancel': '❌ Отмена'
    },
    'en': {
        'welcome': '👋 Welcome, {}! to AI Signals 1Win\n\n🔥 To get the most out of this bot, follow these steps:\n\n1. Register a new account!\n(If you already have an account, please log out and register a new one, this is important because our AI only works with new accounts)\n\n2. After registration you will automatically receive a notification of successful registration.\n\n❗ If you do not follow these steps, our bot cannot add your account to its database, and the signals provided may not match ❗\n\n🤝 Thank you for understanding!\n\n👇 After registration, click the "Bind ID" button below',
        'enter_id': '📝 Enter your ID from your 1WIN personal account:',
        'confirm_id': '📝 You entered ID: {}\n\n✅ Is that correct? Confirm:',
        'id_success': '✅ ID {} successfully bound!\n\n🎁 By the way, deposits give nice bonuses — you can play them in any slot!\n\n💣 Choose the number of mines for round analysis:',
        'stats': '📊 Your statistics:\n\n🆔 ID: {}\n📈 Requests: {}\n🗂️ Language: {}',
        'choose_mines': '💣 Choose the number of mines for round analysis:',
        'analysis': '⚙️ Analysis parameters:\n💣 Mines: {}\n🎯 Success rate: {}%\n📊 Expected coefficient (Step 1): {}x\n\n📍 Signal (safe cells):\n{}\n\n🔄 Choose different amount or go to game:',
        'language_changed': '🌍 Language changed to English!',
        'support': '💬 1Win Signal Support Center\n\nHave questions about the bot, ID binding, or withdrawals? Contact our support team, and we will solve any issue!\n\n👉 Write to our administrator: @Alexanderii_173',
        'back': '⏪ Back to menu',
        'play': '💎 Play on 1Win',
        'register': '🌐 Register on 1WIN',
        'bind_id': '🚀 Bind ID',
        'support_btn': '💬 Support',
        'stats_btn': '📊 Statistics',
        'lang_btn': '🌍 Language',
        'confirm': '✅ Confirm',
        'cancel': '❌ Cancel'
    }
}

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

# Инициализация БД
init_db()

# Хранилище для ожидания подтверждения
pending_ids = {}

# === ВСЕ ФУНКЦИИ БОТА ===

def get_text(user_id, key):
    user = get_user(user_id)
    lang = user[3] if user else 'ru'
    return TEXTS[lang].get(key, TEXTS['ru'][key])

# Главное меню
def main_menu(message):
    chat_id = message.chat.id
    message_id = message.message_id
    user_first_name = message.from_user.first_name or "Гость"
    
    update_user(chat_id, user_name=user_first_name)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton(get_text(chat_id, 'register'), url="https://one-vv6776.com/?open=register&p=m1cy")
    btn2 = types.InlineKeyboardButton(get_text(chat_id, 'bind_id'), callback_data="send_id")
    btn3 = types.InlineKeyboardButton(get_text(chat_id, 'stats_btn'), callback_data="stats")
    btn4 = types.InlineKeyboardButton(get_text(chat_id, 'lang_btn'), callback_data="language")
    btn5 = types.InlineKeyboardButton(get_text(chat_id, 'support_btn'), callback_data="support")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    text = get_text(chat_id, 'welcome').format(user_first_name)
    
    try:
        bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup)
    except:
        bot.send_message(chat_id, text, reply_markup=markup)

# Старт
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_first_name = message.from_user.first_name or "Гость"
    update_user(chat_id, user_name=user_first_name)
    main_menu(message)

# Обработка кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "send_id":
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        msg = bot.send_message(chat_id, get_text(chat_id, 'enter_id'))
        bot.register_next_step_handler(msg, process_id)
    
    elif call.data == "confirm_id":
        if chat_id in pending_ids:
            id_1win = pending_ids[chat_id]
            update_user(chat_id, id_1win=id_1win)
            del pending_ids[chat_id]
            
            markup = types.InlineKeyboardMarkup(row_width=4)
            btn1 = types.InlineKeyboardButton("💣1", callback_data="mine_1")
            btn2 = types.InlineKeyboardButton("💣3", callback_data="mine_3")
            btn3 = types.InlineKeyboardButton("💣5", callback_data="mine_5")
            btn4 = types.InlineKeyboardButton("💣7", callback_data="mine_7")
            markup.add(btn1, btn2, btn3, btn4)
            markup.row(
                types.InlineKeyboardButton(get_text(chat_id, 'play'), url="https://one-vv6776.com/?open=register&p=m1cy"),
                types.InlineKeyboardButton(get_text(chat_id, 'back'), callback_data="back")
            )
            markup.row(types.InlineKeyboardButton(get_text(chat_id, 'support_btn'), callback_data="support"))
            
            try:
                bot.edit_message_text(
                    get_text(chat_id, 'id_success').format(id_1win),
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    chat_id,
                    get_text(chat_id, 'id_success').format(id_1win),
                    reply_markup=markup
                )
    
    elif call.data == "cancel_id":
        if chat_id in pending_ids:
            del pending_ids[chat_id]
        main_menu(call.message)
    
    elif call.data == "back":
        main_menu(call.message)
    
    elif call.data == "support":
        support_message(call.message)
    
    elif call.data == "stats":
        stats_message(call.message)
    
    elif call.data == "language":
        language_menu(call.message)
    
    elif call.data.startswith("lang_"):
        lang = call.data.split("_")[1]
        update_user(chat_id, language=lang)
        try:
            bot.edit_message_text(
                get_text(chat_id, 'language_changed'),
                chat_id=chat_id,
                message_id=message_id
            )
        except:
            bot.send_message(chat_id, get_text(chat_id, 'language_changed'))
        time.sleep(1)
        main_menu(call.message)
    
    elif call.data.startswith("mine_"):
        mines = int(call.data.split("_")[1])
        start_game(call.message, mines)

# Обработка ввода ID
def process_id(message):
    chat_id = message.chat.id
    user_id_text = message.text.strip()
    
    if not user_id_text.isdigit():
        msg = bot.send_message(chat_id, "❌ ID должен состоять только из цифр! Попробуйте снова:")
        bot.register_next_step_handler(msg, process_id)
        return
    
    pending_ids[chat_id] = user_id_text
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(get_text(chat_id, 'confirm'), callback_data="confirm_id"),
        types.InlineKeyboardButton(get_text(chat_id, 'cancel'), callback_data="cancel_id")
    )
    
    bot.send_message(
        chat_id,
        get_text(chat_id, 'confirm_id').format(user_id_text),
        reply_markup=markup
    )

# Статистика
def stats_message(message):
    chat_id = message.chat.id
    message_id = message.message_id
    user = get_user(chat_id)
    
    if user:
        id_1win = user[2] or 'Не привязан'
        requests_count = user[4] or 0
        lang = user[3] or 'ru'
        lang_text = 'Русский' if lang == 'ru' else 'English'
        
        text = get_text(chat_id, 'stats').format(id_1win, requests_count, lang_text)
    else:
        text = "❌ Данные не найдены"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(get_text(chat_id, 'back'), callback_data="back"))
    
    try:
        bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup)
    except:
        bot.send_message(chat_id, text, reply_markup=markup)

# Язык
def language_menu(message):
    chat_id = message.chat.id
    message_id = message.message_id
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    markup.add(types.InlineKeyboardButton(get_text(chat_id, 'back'), callback_data="back"))
    
    try:
        bot.edit_message_text(
            "🌍 Выберите язык / Choose language:",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    except:
        bot.send_message(
            chat_id,
            "🌍 Выберите язык / Choose language:",
            reply_markup=markup
        )

# Поддержка
def support_message(message):
    chat_id = message.chat.id
    message_id = message.message_id
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💬 Написать администратору", url="https://t.me/Alexanderii_173"))
    markup.row(types.InlineKeyboardButton(get_text(chat_id, 'back'), callback_data="back"))
    
    try:
        bot.edit_message_text(
            get_text(chat_id, 'support'),
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    except:
        bot.send_message(
            chat_id,
            get_text(chat_id, 'support'),
            reply_markup=markup
        )

# Игра
def start_game(message, mines):
    chat_id = message.chat.id
    message_id = message.message_id
    
    increment_requests(chat_id)
    
    cells = [['⬛' for _ in range(5)] for _ in range(5)]
    safe_cells = 25 - mines
    probability = round((safe_cells / 25) * 100, 1)
    coefficient = round(25 / safe_cells, 2)
    
    safe_positions = random.sample(range(25), mines)
    safe_positions = sorted(safe_positions)
    
    for pos in safe_positions:
        row = pos // 5
        col = pos % 5
        cells[row][col] = '⭐'
    
    field = ""
    for row in cells:
        field += ' '.join(row) + '\n'
    
    markup = types.InlineKeyboardMarkup(row_width=4)
    btn1 = types.InlineKeyboardButton("💣1", callback_data="mine_1")
    btn2 = types.InlineKeyboardButton("💣3", callback_data="mine_3")
    btn3 = types.InlineKeyboardButton("💣5", callback_data="mine_5")
    btn4 = types.InlineKeyboardButton("💣7", callback_data="mine_7")
    markup.add(btn1, btn2, btn3, btn4)
    markup.row(
        types.InlineKeyboardButton(get_text(chat_id, 'play'), url="https://one-vv6776.com/?open=register&p=m1cy"),
        types.InlineKeyboardButton(get_text(chat_id, 'back'), callback_data="back")
    )
    markup.row(types.InlineKeyboardButton(get_text(chat_id, 'support_btn'), callback_data="support"))
    
    try:
        bot.edit_message_text(
            get_text(chat_id, 'analysis').format(mines, probability, coefficient, field),
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    except:
        bot.send_message(
            chat_id,
            get_text(chat_id, 'analysis').format(mines, probability, coefficient, field),
            reply_markup=markup
        )

print("✅ Бот запущен!")
print("🔄 Автопинг активен (каждую минуту)")

bot.polling()