import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН")
ADMIN_ID = 7798379121

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Базы данных в памяти
banned_users = set()
user_languages = {}  # {user_id: 'ru'|'uk'|'en'}

# --- СЛОВАРЬ ПЕРЕВОДОВ С НОВЫМ ПРИВЕТСТВИЕМ ---
TEXTS = {
    'ru': {
        'start': "👋 **Привет!** Добро пожаловать в бот сотрудничества **Music Game Series**.\n\nНапишите ваше сообщение или предложение, и администрация ответит вам в ближайшее время!\nОбязательно прочитайте правила по команде /rules.\nОстальные команды: /rules /language /start",
        'select_lang': "🌐 **Выберите язык интерфейса / Оберіть мову / Select a language:**",
        'lang_changed': "✅ Язык успешно изменен на **Русский**!",
        'rules': "📜 **Правила обращения через бота:**\n\n1. Пишите всё в одном сообщении. Не нужно отправлять «Привет», «А можно вопрос?» и ждать ответа — формулируйте предложение сразу.\n2. Без спама и флуда. Повторные или бессмысленные сообщения приведут к блокировке.\n3. Уважение и вежливость. Сообщения с оскорблениями и неадекватным мнением не рассматриваются.\n4. Терпение. Нам нужно время на обработку заявки, ответим при первой возможности!",
        'blocked': "🚫 Вы заблокированы в этом боте.",
        'sent': "✅ Ваше сообщение успешно отправлено администрации!",
        'reply_usage': "⚠️ Использование: `/reply USER_ID Ваш текст`",
        'ban_usage': "⚠️ Использование: `/ban USER_ID`",
        'unban_usage': "⚠️ Использование: `/unban USER_ID`",
        'user_banned': "🚫 Пользователь `{user_id}` заблокирован!",
        'user_unbanned': "✅ Пользователь `{user_id}` разблокирован!",
        'reply_sent': "✅ Ответ успешно отправлен пользователю `{user_id}`!",
        'no_admin': "⛔ У вас нет прав для выполнения этой команды.",
    },
    'uk': {
        'start': "👋 **Привіт!** Ласкаво просимо до бота співпраці **Music Game Series**.\n\nНапишіть ваше повідомлення або пропозицію, і адміністрація відповість вам найближчим часом!\nОбов'язково прочитайте правила за командою /rules.\nІнші команди: /rules /language /start",
        'select_lang': "🌐 **Оберіть мову / Выберите язык / Select a language:**",
        'lang_changed': "✅ Мову успішно змінено на **Українську**!",
        'rules': "📜 **Правила звернення через бота:**\n\n1. Пишіть усе в одному повідомленні. Не потрібно надсилати «Привіт», «А можна запитання?» і чекати відповіді — формулюйте пропозицію одразу.\n2. Без спаму та флуду. Повторні або беззмістовні повідомлення призведуть до блокування.\n3. Повага та ввічливість. Повідомлення з образами та неадекватною думкою не розглядаються.\n4. Терпіння. Нам потрібен час на обробку заявки, відповімо за першої можливості!",
        'blocked': "🚫 Ви заблоковані в цьому боті.",
        'sent': "✅ Ваше повідомлення успішно надіслано адміністрації!",
        'reply_usage': "⚠️ Використання: `/reply USER_ID Ваш текст`",
        'ban_usage': "⚠️ Використання: `/ban USER_ID`",
        'unban_usage': "⚠️ Використання: `/unban USER_ID`",
        'user_banned': "🚫 Користувача `{user_id}` заблоковано!",
        'user_unbanned': "✅ Користувача `{user_id}` розблоковано!",
        'reply_sent': "✅ Відповідь успішно надіслано користувачеві `{user_id}`!",
        'no_admin': "⛔ У вас немає прав для виконання цієї команди.",
    },
    'en': {
        'start': "👋 **Hello!** Welcome to the **Music Game Series** collaboration bot.\n\nSend your message or proposal, and the admin will respond to you shortly!\nBe sure to read the rules using the /rules command.\nOther commands: /rules /language /start",
        'select_lang': "🌐 **Select a language / Выберите язык / Оберіть мову:**",
        'lang_changed': "✅ Language successfully set to **English**!",
        'rules': "📜 **Rules for contacting via bot:**\n\n1. Write everything in a single message. Do not send 'Hi', 'Can I ask a question?' and wait for a reply — state your proposal right away.\n2. No spam or flood. Duplicate or meaningless messages will lead to a ban.\n3. Respect and courtesy. Messages with insults and inappropriate opinions will not be considered.\n4. Patience. We need time to process your request and will reply as soon as possible!",
        'blocked': "🚫 You are blocked in this bot.",
        'sent': "✅ Your message has been successfully sent to the admin!",
        'reply_usage': "⚠️ Usage: `/reply USER_ID Your text`",
        'ban_usage': "⚠️ Usage: `/ban USER_ID`",
        'unban_usage': "⚠️ Usage: `/unban USER_ID`",
        'user_banned': "🚫 User `{user_id}` has been blocked!",
        'user_unbanned': "✅ User `{user_id}` has been unblocked!",
        'reply_sent': "✅ Reply successfully sent to user `{user_id}`!",
        'no_admin': "⛔ You do not have permission to use this command.",
    }
}

# --- ВПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_user_lang(user: types.User) -> str:
    if user.id in user_languages:
        return user_languages[user.id]
    lang = user.language_code
    if lang in ['ru', 'be']: return 'ru'
    elif lang in ['uk', 'ua']: return 'uk'
    return 'en'

def get_text(user: types.User, key: str, **kwargs) -> str:
    lang_code = get_user_lang(user)
    template = TEXTS[lang_code].get(key, TEXTS['en'][key])
    return template.format(**kwargs) if kwargs else template

def get_language_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="set_lang_ru")
    builder.button(text="🇺🇦 Українська", callback_data="set_lang_uk")
    builder.button(text="🇬🇧 English", callback_data="set_lang_en")
    builder.adjust(1)
    return builder.as_markup()


# --- КОМАНДЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id in banned_users:
        await message.answer(get_text(message.from_user, 'blocked'))
        return

    if message.from_user.id not in user_languages:
        await message.answer(get_text(message.from_user, 'select_lang'), reply_markup=get_language_keyboard(), parse_mode="Markdown")
    else:
        await message.answer(get_text(message.from_user, 'start'), parse_mode="Markdown")

@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    if message.from_user.id in banned_users:
        await message.answer(get_text(message.from_user, 'blocked'))
        return
    await message.answer(get_text(message.from_user, 'select_lang'), reply_markup=get_language_keyboard(), parse_mode="Markdown")

@dp.message(Command("rules"))
async def cmd_rules(message: types.Message):
    if message.from_user.id in banned_users:
        await message.answer(get_text(message.from_user, 'blocked'))
        return
    await message.answer(get_text(message.from_user, 'rules'), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("set_lang_"))
async def process_language_choice(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[-1]
    user_languages[user_id] = lang_code
    
    await callback.answer()
    await callback.message.edit_text(get_text(callback.from_user, 'lang_changed'), parse_mode="Markdown")
    await callback.message.answer(get_text(callback.from_user, 'start'), parse_mode="Markdown")

@dp.message(Command("reply"))
async def cmd_reply(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(get_text(message.from_user, 'no_admin'))
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(get_text(message.from_user, 'reply_usage'), parse_mode="Markdown")
        return
    target_id, text_to_send = int(args[1]), args[2]
    try:
        await bot.send_message(target_id, f"📩 **Ответ от администрации:**\n\n{text_to_send}", parse_mode="Markdown")
        await message.answer(get_text(message.from_user, 'reply_sent', user_id=target_id), parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")

@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(get_text(message.from_user, 'no_admin'))
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer(get_text(message.from_user, 'ban_usage'), parse_mode="Markdown")
        return
    target_id = int(args[1])
    banned_users.add(target_id)
    await message.answer(get_text(message.from_user, 'user_banned', user_id=target_id), parse_mode="Markdown")

@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(get_text(message.from_user, 'no_admin'))
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer(get_text(message.from_user, 'unban_usage'), parse_mode="Markdown")
        return
    target_id = int(args[1])
    banned_users.discard(target_id)
    await message.answer(get_text(message.from_user, 'user_unbanned', user_id=target_id), parse_mode="Markdown")


# --- ХЕНДЛЕР ОБЫЧНЫХ СООБЩЕНИЙ ---
@dp.message(F.text)
async def handle_user_message(message: types.Message):
    user_id = message.from_user.id

    if user_id in banned_users:
        await message.answer(get_text(message.from_user, 'blocked'))
        return

    if user_id == ADMIN_ID:
        return

    info = f"📩 **Новое сообщение!**\nОт: `{user_id}` (@{message.from_user.username or 'no_username'})\n\n{message.text}"
    
    await bot.send_message(ADMIN_ID, info, parse_mode="Markdown")
    await message.answer(get_text(message.from_user, 'sent'))


# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    # Запускаем поллинг бота параллельно с веб-сервером
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
    
