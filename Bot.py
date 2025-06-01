from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
import jdatetime
import json
import os
import nest_asyncio

nest_asyncio.apply()

# 🟢 تنظیمات اصلی
TOKEN = "7998418773:AAHPZ82U2VGeLkW-PIA-p2u1_NpBoW9dOsI"
DATA_FILE = "attendees.json"
MESSAGE_FILE = "message_id.txt"
ALLOWED_USERS = [966421375]  # ← شناسه عددی خودتو اینجا بذار (از userinfobot بگیر)

# 📆 تاریخ شمسی امروز
def get_today_shamsi():
    return jdatetime.date.today().strftime("%Y/%m/%d")

# 📥 خواندن داده‌ها
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 💾 ذخیره داده‌ها
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 🎛 دکمه‌ها
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ حاضر هستم", callback_data="hazer")],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel")]
    ])

# 🔐 بررسی مجاز بودن کاربر
async def is_admin(update: Update) -> bool:
    user_id = update.effective_user.id
    chat = update.effective_chat

    if user_id in ALLOWED_USERS:
        return True

    try:
        member = await chat.get_member(user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except:
        return False

# ❌ حذف پیام قبلی
async def delete_previous_message(context, chat_id):
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, "r") as f:
            msg_id = f.read().strip()
            if msg_id:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=int(msg_id))
                except:
                    pass

# ▶️ هندلر /start
async def start_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("❌ فقط مدیران گروه یا کاربران مجاز می‌تونن این دستور رو اجرا کنن.")
        return

    today = get_today_shamsi()
    data = load_data()
    users = data.get(today, [])

    await delete_previous_message(context, update.effective_chat.id)

    text = f"📅 حضور و غیاب امروز: *{today}*\n\n"
    text += "👋 برای اعلام حضور یکی از دکمه‌های زیر رو بزن:\n\n"
    if users:
        text += "✅ افراد حاضر:\n" + "\n".join([f"{i+1}. {u}" for i, u in enumerate(users)])
    else:
        text += "هنوز کسی اعلام حضور نکرده 😶"

    msg = await update.message.reply_text(text, reply_markup=get_keyboard(), parse_mode="Markdown")

    with open(MESSAGE_FILE, "w") as f:
        f.write(str(msg.message_id))

# 🔘 هندلر دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    name = user.first_name
    today = get_today_shamsi()

    data = load_data()
    users = data.get(today, [])

    if query.data == "hazer" and name not in users:
        users.append(name)
    elif query.data == "cancel" and name in users:
        users.remove(name)

    data[today] = users
    save_data(data)

    text = f"📅 حضور و غیاب امروز: *{today}*\n\n"
    text += "👋 برای اعلام حضور یکی از دکمه‌های زیر رو بزن:\n\n"
    if users:
        text += "✅ افراد حاضر:\n" + "\n".join([f"{i+1}. {u}" for i, u in enumerate(users)])
    else:
        text += "هنوز کسی اعلام حضور نکرده 😶"

    await query.edit_message_text(text=text, reply_markup=get_keyboard(), parse_mode="Markdown")

# 🚀 اجرای ربات
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start_attendance))
app.add_handler(CallbackQueryHandler(button_handler))

print("✅ ربات حضور و غیاب با تاریخ شمسی، حذف پیام‌های قبلی و محدودیت اجرا شده...")
app.run_polling()
