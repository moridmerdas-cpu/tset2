import os
import json
from aiohttp import web
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ================= CONFIG =================
BOT_TOKEN = "BOT_TOKEN"
WEBHOOK_PATH = "WEBHOOK_URL"
WEBHOOK_URL = "https://YOUR-APP.onrender.com/webhook"
PORT = int(os.environ.get("PORT", 10000))

OWNER_ID = 858877317
OWNER_USERNAME = "@amele55"

DB_FILE = "db.json"

# ================= DATABASE =================
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({
                "users": {},
                "pending_users": {},
                "channels": {},
                "groups": {},
                "forwarding": {}
            }, f, indent=2)
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


# ================= HELPERS =================
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def main_menu(owner=False):
    buttons = [
        [InlineKeyboardButton("📡 تنظیم کانال مبدأ", callback_data="set_channel")],
        [InlineKeyboardButton("📋 لیست", callback_data="list")],
        [InlineKeyboardButton("▶️ شروع فوروارد", callback_data="start_fw")],
        [InlineKeyboardButton("⏹ توقف فوروارد", callback_data="stop_fw")],
        [InlineKeyboardButton("📞 ارتباط با ادمین", callback_data="contact")],
        [InlineKeyboardButton("❓ راهنما", callback_data="help")]
    ]
    if owner:
        buttons.insert(1, [InlineKeyboardButton("⚙️ تنظیمات گروه", callback_data="group_settings")])
    return InlineKeyboardMarkup(buttons)


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user = update.effective_user

    if not is_owner(user.id) and str(user.id) not in db["users"]:
        db["pending_users"][str(user.id)] = {
            "name": user.full_name,
            "username": user.username
        }
        save_db(db)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ پذیرش", callback_data=f"accept:{user.id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject:{user.id}")
            ]
        ])

        await context.bot.send_message(
            OWNER_ID,
            "👤 درخواست عضویت جدید\n\n"
            f"👤 اسم: {user.full_name}\n"
            f"🔗 یوزرنیم: @{user.username}\n"
            f"🆔 آیدی عددی: {user.id}",
            reply_markup=keyboard
        )

        await update.message.reply_text(
            "⏳ درخواست عضویت شما برای مالک ارسال شد"
        )
        return

    await update.message.reply_text(
        "👋 خوش اومدی!\nاز منوی زیر استفاده کن 👇",
        reply_markup=main_menu(is_owner(user.id))
    )


# ================= CALLBACKS =================
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = load_db()

    # ---- User approval ----
    if query.data.startswith(("accept:", "reject:")):
        action, uid = query.data.split(":")
        user = db["pending_users"].get(uid)

        if not user:
            return

        if action == "accept":
            db["users"][uid] = user
            await context.bot.send_message(
                int(uid),
                "✅ درخواستت تأیید شد و به ربات اضافه شدی 🎉"
            )
            await query.edit_message_text(
                f"✅ کاربر @{user['username']} اضافه شد"
            )
        else:
            await context.bot.send_message(
                int(uid),
                "❌ متأسفانه درخواستت رد شد"
            )
            await query.edit_message_text("❌ درخواست کاربر رد شد")

        del db["pending_users"][uid]
        save_db(db)
        return

    # ---- Panels ----
    if query.data == "contact":
        await query.message.reply_text(
            f"📞 ارتباط با ادمین:\n{OWNER_USERNAME}"
        )

    elif query.data == "help":
        await query.message.reply_text(
            "❓ راهنما:\n\n"
            "1️⃣ ربات را ادمین کانال یا گروه کنید\n"
            "2️⃣ لینک را با @ ارسال نمایید\n"
            "3️⃣ منتظر تأیید مالک بمانید 😎"
        )

    elif query.data == "list":
        await query.message.reply_text("📋 لیست در حال توسعه است…")

    elif query.data == "start_fw":
        await query.message.reply_text("▶️ فوروارد برای شما فعال شد")

    elif query.data == "stop_fw":
        await query.message.reply_text("⏹ فوروارد برای شما متوقف شد")


# ================= WEBHOOK HANDLER =================
async def telegram_webhook(request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return web.Response(text="OK")


# ================= KEEP ALIVE =================
async def health_check(request):
    return web.Response(text="Bot is alive 🤖🔥")


# ================= STARTUP =================
async def on_startup(app):
    await application.bot.set_webhook(WEBHOOK_URL)
    print("✅ Webhook set successfully")


# ================= APP =================
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(callbacks))

aio_app = web.Application()
aio_app.router.add_post(WEBHOOK_PATH, telegram_webhook)
aio_app.router.add_get("/", health_check)
aio_app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(aio_app, port=PORT)
