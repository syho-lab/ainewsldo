import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import httpx
import json

# Загружаем ключи из переменных окружения
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Получаем OpenRouter API ключ
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Получаем Telegram API ключ

# Проверка наличия ключей
if not OPENROUTER_API_KEY or not TELEGRAM_TOKEN:
    raise ValueError("API ключи не найдены в переменных окружения!")

# Начальная личность бота
bot_personality = "Добрый"

# Функция для асинхронного запроса к OpenRouter API с изменением личности
async def get_openrouter_response(user_message, personality):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "deepseek/deepseek-r1-0528:free",  # Модель остается прежней
        "messages": [
            {"role": "system", "content": f"Ты {personality}, и ты помогаешь пользователю с его вопросами."},  # Личность бота
            {"role": "user", "content": user_message}
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body, timeout=10.0)
            response.raise_for_status()  # Выбросить ошибку в случае неуспешного запроса
            response_data = response.json()

            return response_data['choices'][0]['message']['content']
    except httpx.RequestError as e:
        logging.error(f"Request error: {e}")
        return "Sorry, there was an error while processing your request."
    except Exception as e:
        logging.error(f"Error: {e}")
        return "Sorry, there was an error while processing your request."

# Функция обработки сообщений от пользователя
async def handle_message(update: Update, context):
    # Отправляем сообщение "Думаю..."
    thinking_message = await update.message.reply_text("Думаю...")

    user_message = update.message.text
    bot_reply = await get_openrouter_response(user_message, bot_personality)

    # Удаляем сообщение "Думаю..."
    await thinking_message.delete()

    # Отправляем ответ бота
    await update.message.reply_text(bot_reply)

# Функция обработки команды /start
async def start(update: Update, context):
    welcome_message = "Привет! Я Жопоглазая, и я помогу тебе с вопросами. Напиши мне что-нибудь, и я постараюсь ответить."
    await update.message.reply_text(welcome_message)

# Функция для команды /help с подсказками
async def help_command(update: Update, context):
    help_text = (
        "/start - Приветственное сообщение\n"
        "/help - Покажет список команд\n"
        "/change - Изменить личность бота\n"
        "/clear - Очистить чат (функция по желанию)"
    )
    await update.message.reply_text(help_text)

# Функция для команды /change с инлайн кнопками
async def change_personality(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Злой", callback_data='Злой')],
        [InlineKeyboardButton("Злой с матами", callback_data='Злой с матами')],
        [InlineKeyboardButton("Добрый", callback_data='Добрый')],
        [InlineKeyboardButton("Средний", callback_data='Средний')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите личность бота:", reply_markup=reply_markup)

# Функция обработки выбора личности через инлайн кнопки
async def button(update: Update, context):
    global bot_personality
    query = update.callback_query
    bot_personality = query.data  # Обновляем личность
    await query.answer()  # Подтверждаем выбор
    await query.edit_message_text(f"Теперь я буду {bot_personality}! 😄")

# Основная функция для запуска бота
def main():
    # Включаем логирование
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Создаем Application и передаем ему ваш Telegram Token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))  # Обработчик команды /start
    application.add_handler(CommandHandler("help", help_command))  # Обработчик команды /help
    application.add_handler(CommandHandler("change", change_personality))  # Обработчик команды /change
    application.add_handler(CallbackQueryHandler(button))  # Обработчик инлайн кнопок
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Обработчик для текста

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
