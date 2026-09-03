import telebot
from telebot import types
import random
import threading
import time
from flask import Flask, request
import requests
import os

# === ТОКЕН БОТА ===
TOKEN = '8941493056:AAGDwx7ayDFvDBF6XpEo02dQnQEV4334kHU'

# === СОЗДАЁМ ФЛАСК-СЕРВЕР ДЛЯ ПИНГА ===
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает!", 200

@app.route('/ping')
def ping():
    return "pong", 200

# === ФУНКЦИЯ ДЛЯ АВТОПИНГА (КАЖДУЮ МИНУТУ) ===
def keep_alive():
    """Каждую минуту отправляет запрос к самому себе, чтобы Render не уснул"""
    url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/ping"
    while True:
        try:
            requests.get(url, timeout=10)
            print("🔄 Автопинг отправлен")
        except Exception as e:
            print(f"❌ Ошибка автопинга: {e}")
        time.sleep(60)

# === ЗАПУСКАЕМ ФЛАСК И АВТОПИНГ В ОТДЕЛЬНЫХ ПОТОКАХ ===
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

# === ВСЕ ФУНКЦИИ БОТА ===

# Главное меню
def main_menu(message):
    chat_id = message.chat.id
    message_id = message.message_id
    user_first_name = message.from_user.first_name or "Гость"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🌐 Зарегистрироваться на сайте 1WIN", url="https://one-vv6776.com/?open=register&p=m1cy")
    btn2 = types.InlineKeyboardButton("🚀 Привязать ID", callback_data="send_id")
    btn3 = types.InlineKeyboardButton("💬 Поддержка", callback_data="support")
    markup.add(btn1, btn2, btn3)
    
    text = f"""👋 Приветствую тебя, {user_first_name}! в AI Signals 1Win

🔥 Чтобы получить максимум от использования этого бота, необходимо следовать следующим шагам:

1. Зарегистрируйте новый аккаунт!
(Если у вас уже есть аккаунт, пожалуйста, выйдите и зарегистрируйте новый, это важно, потому что наш ИИ работает только с новыми аккаунтами)

2. После регистрации вы автоматически получите уведомление о успешной регистрации.

❗ Если вы не выполните эти шаги, наш бот не сможет добавить ваш аккаунт в свою базу данных, и предоставленные сигналы могут не соответствовать ❗

🤝 Спасибо за понимание!

👇 Снизу после регистрации нажмите на кнопку "Привязать ID" """
    
    try:
        bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=markup)
    except:
        bot.send_message(chat_id, text, reply_markup=markup)

# Старт
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_first_name = message.from_user.first_name or "Гость"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🌐 Зарегистрироваться на сайте 1WIN", url="https://one-vv6776.com/?open=register&p=m1cy")
    btn2 = types.InlineKeyboardButton("🚀 Привязать ID", callback_data="send_id")
    btn3 = types.InlineKeyboardButton("💬 Поддержка", callback_data="support")
    markup.add(btn1, btn2, btn3)
    
    text = f"""👋 Приветствую тебя, {user_first_name}! в AI Signals 1Win

🔥 Чтобы получить максимум от использования этого бота, необходимо следовать следующим шагам:

1. Зарегистрируйте новый аккаунт!
(Если у вас уже есть аккаунт, пожалуйста, выйдите и зарегистрируйте новый, это важно, потому что наш ИИ работает только с новыми аккаунтами)

2. После регистрации вы автоматически получите уведомление о успешной регистрации.

❗ Если вы не выполните эти шаги, наш бот не сможет добавить ваш аккаунт в свою базу данных, и предоставленные сигналы могут не соответствовать ❗

🤝 Спасибо за понимание!

👇 Снизу после регистрации нажмите на кнопку "Привязать ID" """
    
    bot.send_message(chat_id, text, reply_markup=markup)

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
        msg = bot.send_message(chat_id, "📝 Введите ваш ID из личного кабинета 1WIN:")
        bot.register_next_step_handler(msg, save_id)
    
    elif call.data == "mines_menu":
        mines_menu(call.message)
    
    elif call.data == "back":
        main_menu(call.message)
    
    elif call.data == "support":
        support_message(call.message)
    
    elif call.data == "play":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("💎 Играть на 1Win", url="https://one-vv6776.com/?open=register&p=m1cy"))
        try:
            bot.edit_message_text(
                "🎰 Переход на сайт...",
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=markup
            )
        except:
            pass
    
    elif call.data.startswith("mine_"):
        mines = int(call.data.split("_")[1])
        start_game(call.message, mines)
    
    elif call.data == "new_game":
        mines_menu(call.message)

# Сохранение ID
def save_id(message):
    chat_id = message.chat.id
    user_id = message.text.strip()
    user_data[chat_id] = {"id": user_id}
    
    markup = types.InlineKeyboardMarkup(row_width=4)
    btn1 = types.InlineKeyboardButton("💣1", callback_data="mine_1")
    btn2 = types.InlineKeyboardButton("💣3", callback_data="mine_3")
    btn3 = types.InlineKeyboardButton("💣5", callback_data="mine_5")
    btn4 = types.InlineKeyboardButton("💣7", callback_data="mine_7")
    markup.add(btn1, btn2, btn3, btn4)
    
    markup.row(
        types.InlineKeyboardButton("💎 Играть на 1Win", url="https://one-vv6776.com/?open=register&p=m1cy"),
        types.InlineKeyboardButton("⏪ Назад в меню", callback_data="back")
    )
    markup.row(
        types.InlineKeyboardButton("💬 Поддержка", callback_data="support")
    )
    
    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass
    
    bot.send_message(
        chat_id,
        f"✅ ID {user_id} успешно привязан!\n\n🎁 Кстати, за пополнение дают вкусные бонусы — можешь отыграть их в любом слоте!\n\n💣 Выберите количество мин для анализа раунда:",
        reply_markup=markup
    )

# Меню выбора мин
def mines_menu(message):
    chat_id = message.chat.id
    message_id = message.message_id
    
    markup = types.InlineKeyboardMarkup(row_width=4)
    btn1 = types.InlineKeyboardButton("💣1", callback_data="mine_1")
    btn2 = types.InlineKeyboardButton("💣3", callback_data="mine_3")
    btn3 = types.InlineKeyboardButton("💣5", callback_data="mine_5")
    btn4 = types.InlineKeyboardButton("💣7", callback_data="mine_7")
    markup.add(btn1, btn2, btn3, btn4)
    
    markup.row(
        types.InlineKeyboardButton("💎 Играть на 1Win", url="https://one-vv6776.com/?open=register&p=m1cy"),
        types.InlineKeyboardButton("⏪ Назад в меню", callback_data="back")
    )
    markup.row(
        types.InlineKeyboardButton("💬 Поддержка", callback_data="support")
    )
    
    try:
        bot.edit_message_text(
            "💣 Выберите количество мин для анализа раунда:",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    except:
        bot.send_message(
            chat_id,
            "💣 Выберите количество мин для анализа раунда:",
            reply_markup=markup
        )

# Поддержка
def support_message(message):
    chat_id = message.chat.id
    message_id = message.message_id
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💬 Написать администратору", url="https://t.me/Alexanderii_173"))
    markup.row(
        types.InlineKeyboardButton("⏪ Назад в меню", callback_data="back")
    )
    
    try:
        bot.edit_message_text(
            "💬 Центр поддержки 1Win Signal\n\nВозникли вопросы по работе бота, привязке ID или выводу средств? Свяжитесь с нашей службой поддержки, и мы решим любой вопрос!\n\n👉 Напишите нашему администратору: @Alexanderii_173",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    except:
        bot.send_message(
            chat_id,
            "💬 Центр поддержки 1Win Signal\n\nВозникли вопросы по работе бота, привязке ID или выводу средств? Свяжитесь с нашей службой поддержки, и мы решим любой вопрос!\n\n👉 Напишите нашему администратору: @Alexanderii_173",
            reply_markup=markup
        )

# Игра
def start_game(message, mines):
    chat_id = message.chat.id
    message_id = message.message_id
    
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
        types.InlineKeyboardButton("💎 Играть на 1Win", url="https://one-vv6776.com/?open=register&p=m1cy"),
        types.InlineKeyboardButton("⏪ Назад в меню", callback_data="back")
    )
    markup.row(
        types.InlineKeyboardButton("💬 Поддержка", callback_data="support")
    )
    
    try:
        bot.edit_message_text(
            f"⚙️ Анализ параметров:\n"
            f"💣 Количество мин: {mines}\n"
            f"🎯 Вероятность успеха: {probability}%\n"
            f"📊 Ожидаемый коэффициент (Шаг 1): {coefficient}x\n\n"
            f"📍 Сигнал (безопасные лунки):\n{field}\n\n"
            f"🔄 Выберите другое количество или перейдите к игре:",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    except:
        bot.send_message(
            chat_id,
            f"⚙️ Анализ параметров:\n"
            f"💣 Количество мин: {mines}\n"
            f"🎯 Вероятность успеха: {probability}%\n"
            f"📊 Ожидаемый коэффициент (Шаг 1): {coefficient}x\n\n"
            f"📍 Сигнал (безопасные лунки):\n{field}\n\n"
            f"🔄 Выберите другое количество или перейдите к игре:",
            reply_markup=markup
        )

print("✅ Бот запущен!")
print("🔄 Автопинг активен (каждую минуту)")

# Запускаем бота
bot.polling()