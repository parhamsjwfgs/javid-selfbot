import os
import time
import paramiko
import ipaddress
import asyncio
import logging
from contextlib import contextmanager
from pytz import timezone
from datetime import timedelta, datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telethon import TelegramClient
from telethon.sessions import SQLiteSession, StringSession
from telethon.errors import SessionPasswordNeededError, PasswordHashInvalidError

if not os.path.exists("database"):
    os.makedirs("database", exist_ok=True)

if not os.path.exists("sessions"):
    os.makedirs("sessions", exist_ok=True)

DB_TEXT_PATH = "database/database.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="bot.log"
)
logger = logging.getLogger(__name__)

API_ID = 29481612
API_HASH = "01a41600f41fa58017c7220b954b7df8"
BOT_TOKEN = "8994843551:AAFbF5KtXf-1RQ0PN5woZUPyZFP6517OAaI"
OWNER_IDS = [6201723470]
CHANNEL_ID = "JavidSelf"
GROUP_ID = "JavidSelfGp"
PRIVATE_CHANNEL_ID = -1003804957958

BANNED_FILE = "banned.txt"
BANNED_NUMBERS_FILE = "banned_numbers.txt"
MAX_RUNS_FILE = "max_runs.txt"
LAST_RUNS_FILE = "last_runs.txt"

GET_NUMBER = 0
GET_CODE = 1
GET_2FA = 2
GET_IP = 3
GET_USER = 4
GET_PASS = 5
ADMIN_INPUT_RUNS = 6
ADMIN_INPUT_BAN = 7
ADMIN_INPUT_UNBAN = 8
ADMIN_INPUT_CHANNEL = 9

USER_DATA_STORE = {}
RUNNING_USER = None
RUN_STARTED_AT = None
NEXT_RUN_ALLOWED_AT = None
BOT_ACTIVE = True
BANNED_USERS = set()
BANNED_NUMBERS = set()
REMAINING_RUNS = 0
LAST_RUNS = {}
ADNUMBER = ["989924991756", "989940458599"]

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

def load_last_runs():
    global LAST_RUNS
    LAST_RUNS = {}
    if os.path.exists(LAST_RUNS_FILE):
        with open(LAST_RUNS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                parts = line_str.split(",")
                if len(parts) == 2:
                    if parts[0].isdigit():
                        uid = int(parts[0])
                        ts = float(parts[1])
                        LAST_RUNS[uid] = ts

def save_last_runs():
    with open(LAST_RUNS_FILE, "w", encoding="utf-8") as f:
        for uid, ts in LAST_RUNS.items():
            f.write(f"{uid},{ts}\n")

def load_max_runs():
    if os.path.exists(MAX_RUNS_FILE):
        with open(MAX_RUNS_FILE, "r") as f:
            try:
                content = f.read().strip()
                return int(content)
            except:
                return 0
    return 0

def save_max_runs(count):
    with open(MAX_RUNS_FILE, "w") as f:
        f.write(str(count))

def save_banned_users():
    with open(BANNED_FILE, "w") as f:
        for uid in BANNED_USERS:
            f.write(f"{uid}\n")

def save_banned_numbers():
    with open(BANNED_NUMBERS_FILE, "w") as f:
        for number in BANNED_NUMBERS:
            f.write(f"{number}\n")

if os.path.exists(BANNED_FILE):
    with open(BANNED_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line.isdigit():
                BANNED_USERS.add(int(line))

if os.path.exists(BANNED_NUMBERS_FILE):
    with open(BANNED_NUMBERS_FILE, "r") as f:
        for line in f:
            BANNED_NUMBERS.add(line.strip())

REMAINING_RUNS = load_max_runs()
load_last_runs()

@contextmanager
def ssh_connection(ip, username, password):
    ssh = paramiko.SSHClient()
    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            ip, 
            username=username, 
            password=password, 
            timeout=20, 
            allow_agent=False, 
            look_for_keys=False
        )
        yield ssh
    finally:
        ssh.close()

def save_user_text(user_id, username=None, phone=None, ip=None, server_user=None, passwd=None, string_session=None):
    if username and not username.startswith("@"):
        username = f"@{username}"
    lines = []
    updated = False
    if os.path.exists(DB_TEXT_PATH):
        with open(DB_TEXT_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
    for i, line in enumerate(lines):
        parts = line.strip().split('. ', 1)
        if len(parts) == 2:
            if parts[1].startswith(f"{user_id} "):
                existing_fields = parts[1].split(" ")
                existing_user_id = existing_fields[0]
                
                existing_username = existing_fields[1] if len(existing_fields) > 1 else ""
                existing_phone = existing_fields[2] if len(existing_fields) > 2 else ""
                existing_ip = existing_fields[3] if len(existing_fields) > 3 else "None"
                existing_suser = existing_fields[4] if len(existing_fields) > 4 else "None"
                existing_spass = existing_fields[5] if len(existing_fields) > 5 else "None"
                existing_string = existing_fields[6] if len(existing_fields) > 6 else "None"
                    
                final_username = username if username else existing_username
                final_phone = phone if phone else existing_phone
                final_ip = ip if ip else existing_ip
                final_suser = server_user if server_user else existing_suser
                final_spass = passwd if passwd else existing_spass
                final_string = string_session if string_session else existing_string
                    
                new_data = f"{existing_user_id} {final_username} {final_phone} {final_ip} {final_suser} {final_spass} {final_string}".strip()
                lines[i] = f"{parts[0]}. {new_data}\n"
                updated = True
                break
                
    if not updated:
        index = len(lines) + 1
        final_username = username or "None"
        final_phone = phone or "None"
        final_ip = ip or "None"
        final_suser = server_user or "None"
        final_spass = passwd or "None"
        final_string = string_session or "None"
        new_data = f"{user_id} {final_username} {final_phone} {final_ip} {final_suser} {final_spass} {final_string}".strip()
        lines.append(f"{index}. {new_data}\n")
        
    with open(DB_TEXT_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

async def cleanup_sessions(user_id):
    if user_id in USER_DATA_STORE:
        if "client" in USER_DATA_STORE[user_id]:
            try:
                await USER_DATA_STORE[user_id]["client"].disconnect()
            except:
                pass

async def update_channel_message(application: Application):
    try:
        now = datetime.now(timezone("Asia/Tehran"))
        current_time = now.strftime('%H:%M')
        message_text = f"ساعت: {current_time}\nتعداد ران مجاز: {REMAINING_RUNS} نفر\n"
        
        if NEXT_RUN_ALLOWED_AT and now < NEXT_RUN_ALLOWED_AT:
            allowed_str = NEXT_RUN_ALLOWED_AT.strftime('%H:%M')
            message_text += f"ربات استفاده شده تا ساعت: {allowed_str}\n"
        else:
            message_text += "به یاد کسانی که دیگه بینمون نیستن :)\n"
            
        message_text += "Creator | t.me/uezrz\n@JavidSelfBot"
        try:
            await application.bot.edit_message_text(chat_id=f"@{CHANNEL_ID}", message_id=32, text=message_text)
        except Exception:
            await application.bot.edit_message_caption(chat_id=f"@{CHANNEL_ID}", message_id=32, caption=message_text)
    except:
        pass

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    return True

def get_numeric_keyboard(current_code=""):
    buttons = [
        [
            InlineKeyboardButton("1", callback_data="code_add_1"),
            InlineKeyboardButton("2", callback_data="code_add_2"),
            InlineKeyboardButton("3", callback_data="code_add_3")
        ],
        [
            InlineKeyboardButton("4", callback_data="code_add_4"),
            InlineKeyboardButton("5", callback_data="code_add_5"),
            InlineKeyboardButton("6", callback_data="code_add_6")
        ],
        [
            InlineKeyboardButton("7", callback_data="code_add_7"),
            InlineKeyboardButton("8", callback_data="code_add_8"),
            InlineKeyboardButton("9", callback_data="code_add_9")
        ],
        [
            InlineKeyboardButton("0", callback_data="code_add_0")
        ],
        [
            InlineKeyboardButton("تایید کد", callback_data="code_confirm"),
            InlineKeyboardButton("انصراف", callback_data="code_cancel"),
            InlineKeyboardButton("پاک کردن", callback_data="code_clear_all")
        ]
    ]
    text = "کد ورود را وارد کنید :\n\n"
    if current_code:
        text += f"{current_code}\n"
    return InlineKeyboardMarkup(buttons), text

async def send_main_menu(chat_id, user_id, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [
            InlineKeyboardButton("اجرای سلف", callback_data="run_self", style='success'),
            InlineKeyboardButton("چک کردن شماره", callback_data="check_number", style='success')
        ],
        [
            InlineKeyboardButton("قوانین", callback_data="rules", style='danger')
        ],
        [
            InlineKeyboardButton("پشتیبانی", url="https://t.me/parham_1218", style='primary')
        ] 
    ]
    if is_owner(user_id):
        buttons.append([InlineKeyboardButton("پنل مدیریت", callback_data="admin_panel", style='success')])
        
    kb = InlineKeyboardMarkup(buttons)
    try:
        await context.bot.copy_message(
            chat_id=chat_id, 
            from_chat_id=PRIVATE_CHANNEL_ID, 
            message_id=5,
            caption="**سلام، به ربات سلف ساز Javid خوش اومدی!\n\nقبل از اجرای سلف حتما قوانین را مطالعه کن:**",
            reply_markup=kb, 
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="**سلام، به ربات سلف ساز Javid خوش اومدی!\n\nقبل از اجرای سلف حتما قوانین را مطالعه کن:**",
            reply_markup=kb, 
            parse_mode=ParseMode.MARKDOWN
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUNNING_USER, RUN_STARTED_AT
    user_id = update.effective_user.id
    if user_id in BANNED_USERS:
        return ConversationHandler.END
        
    is_member = await check_membership(update, context, user_id)
    if not is_member:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("عضو شو", url=f"https://t.me/{CHANNEL_ID}", style='primary')],
            [InlineKeyboardButton("عضو شو", url=f"https://t.me/{GROUP_ID}", style='primary')]
        ])
        await update.message.reply_text("شما عضو کانال و گروه نیستید. لطفاً ابتدا عضو شوید و سپس /start را ارسال کنید.", reply_markup=kb)
        return ConversationHandler.END
        
    if not BOT_ACTIVE and not is_owner(user_id):
        await update.message.reply_text("ربات در حال حاضر خاموش است!")
        return ConversationHandler.END
    
    current_username = update.effective_user.username or update.effective_user.first_name
    save_user_text(user_id, username=current_username)
    
    if RUNNING_USER == user_id:
        RUNNING_USER = None
        RUN_STARTED_AT = None
        if user_id in USER_DATA_STORE:
            USER_DATA_STORE.pop(user_id)
            
    await send_main_menu(update.effective_chat.id, user_id, context)
    return ConversationHandler.END

async def reset_run_task(bot_instance, chat_id, uid):
    await asyncio.sleep(300)
    global RUNNING_USER, RUN_STARTED_AT
    if RUNNING_USER == uid:
        RUNNING_USER = None
        RUN_STARTED_AT = None
        if uid in USER_DATA_STORE:
            USER_DATA_STORE.pop(uid)
        try:
            await bot_instance.send_message(chat_id=chat_id, text="به محدودیت زمانی 5 دقیقه رسیدید! برای اجرای دوباره سلف، دستور /start را ارسال کنید.")
        except:
            pass

def update_all_servers_sync():
    if not os.path.exists(DB_TEXT_PATH):
        return 0, 0

    local_self_py = None
    for path in ["file/self.py", "bot/file/self.py", "self.py"]:
        if os.path.exists(path):
            local_self_py = path
            break
            
    if not local_self_py:
        return -1, -1

    success_count = 0
    fail_count = 0

    with open(DB_TEXT_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split('. ', 1)
        if len(parts) != 2:
            continue
        fields = parts[1].split(" ")

        if len(fields) < 6:
            continue

        ip = fields[3]
        suser = fields[4]
        spass = fields[5]

        if ip == "None" or suser == "None" or spass == "None":
            continue

        try:
            with ssh_connection(ip, suser, spass) as ssh:
                sftp = ssh.open_sftp()
                ssh.exec_command("mkdir -p self", timeout=15)
                time.sleep(0.5)

                sftp.put(local_self_py, "self/self.py")

                ssh.exec_command("pkill -f self.py", timeout=10)
                time.sleep(1)

                run_cmd = "cd self && nohup python3 self.py > self_error.log 2>&1 &"
                ssh.exec_command(run_cmd)
                success_count += 1
        except Exception as e:
            logger.error(f"Failed bulk update for server {ip}: {e}")
            fail_count += 1

    return success_count, fail_count

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE, RUNNING_USER, RUN_STARTED_AT, REMAINING_RUNS, NEXT_RUN_ALLOWED_AT, LAST_RUNS
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data

    if data in ["admin_ban_user", "admin_unban_user", "set_run_custom", "admin_set_channel_custom", "run_self", "check_number"]:
        try:
            await query.answer()
        except:
            pass
        return

    if data == "rules":
        await query.answer()
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="back_to_start", style='primary')]])
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="کاربر گرامی، فروش این سلف به هر صورت غیر مجاز بوده و در صورت فروش حساب شما دیلیت خواهد شد و هرگونه مشکلی که برای حساب شما رخ دهد به سلف و مالک مربوط نخواهد بود. همچنین هرگونه بی احترامی به مدیران و سازنده سلف ممنوع می‌باشد.",
            reply_markup=kb
        )
        return ConversationHandler.END

    elif data == "back_to_start":
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
        await send_main_menu(update.effective_chat.id, user_id, context)
        return ConversationHandler.END

    elif data == "admin_panel":
        if not is_owner(user_id): 
            await query.answer("شما دسترسی ندارید")
            return ConversationHandler.END
        await query.answer()
        try:
            with open("channel_id.txt", "r") as f:
                ch_id = f.read().strip()
                ch_text = f"{ch_id}"
        except:
            ch_text = "ثبت نشده"
        
        if BOT_ACTIVE:
            status_emoji = "آنلاین"
            toggle_style = 'success'
        else:
            status_emoji = "آفلاین"
            toggle_style = 'danger'
        
        admin_text = (
            "🛠 **پنل مدیریت سلف‌ساز**\n\n"
            f"📡 **آیدی چنل اطلاعات کاربران:** `{ch_text}`\n"
            f"🔢 **تعداد دسترسی ران:** {str(REMAINING_RUNS)}\n"
            f"🚦 **وضعیت ربات:** {status_emoji}\n\n"
            "_Welcome Boss, what's your next command?_"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"وضعیت ربات : {status_emoji}", callback_data="admin_toggle_bot", style=toggle_style)],
            [
                InlineKeyboardButton("مدیریت کاربران", callback_data="admin_user_manage", style='primary'), 
                InlineKeyboardButton("آپدیت همگانی سلف‌ها", callback_data="admin_bulk_update", style='danger')
            ], 
            [
                InlineKeyboardButton("ایدی چنل اطلاعات", callback_data="admin_channel_id_info", style='danger'),
                InlineKeyboardButton("تنظیم دسترسی ران", callback_data="admin_set_runs", style='primary')
            ],
            [InlineKeyboardButton("برداشتن محدودیت ران روزانه", callback_data="admin_clear_daily_limits", style='primary')],
            [InlineKeyboardButton("دریافت دیتابیس کاربران", callback_data="admin_get_db", style='success')],
            [InlineKeyboardButton("بستن پنل", callback_data="back_to_start", style='danger')]
        ])
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(chat_id=update.effective_chat.id, text=admin_text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

    elif data == "admin_clear_daily_limits":
        if not is_owner(user_id):
            await query.answer("شما دسترسی ندارید")
            return ConversationHandler.END
        
        LAST_RUNS = {}
        save_last_runs()
        await query.answer("محدودیت روزانه تمام کاربران برداشته شد! حق ران مجدد آزاد شد.", show_alert=True)
        return ConversationHandler.END

    elif data == "admin_bulk_update":
        if not is_owner(user_id):
            await query.answer("شما دسترسی ندارید")
            return ConversationHandler.END
        await query.answer("عملیات آپدیت همگانی آغاز شد...", show_alert=False)
        
        wait_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="در حال اتصال به سرورها و آپدیت سورس سلف‌ها...\nلطفاً شکیبا باشید.")
        
        s_count, f_count = await asyncio.to_thread(update_all_servers_sync)
        
        try:
            await wait_msg.delete()
        except:
            pass
            
        if s_count == -1:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="خطا: فایل سورس جدید سلف (self.py) روی هاست ربات پیدا نشد!")
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"عملیات آپدیت همگانی به پایان رسید.\n\nموفق: {s_count} سرور\nناموفق: {f_count} سرور"
            )
        return ConversationHandler.END

    elif data == "admin_toggle_bot":
        if not is_owner(user_id):
            await query.answer("شما دسترسی ندارید")
            return ConversationHandler.END
        await query.answer()
        
        BOT_ACTIVE = not BOT_ACTIVE
            
        try:
            with open("channel_id.txt", "r") as f:
                ch_id = f.read().strip()
                ch_text = f"{ch_id}"
        except:
            ch_text = "ثبت نشده"
        
        if BOT_ACTIVE:
            status_emoji = "آنلاین"
            toggle_style = 'success'
        else:
            status_emoji = "آفلاین"
            toggle_style = 'danger'
        
        admin_text = (
            "🛠 **پنل مدیریت سلف‌ساز**\n\n"
            f"📡 **آیدی چنل اطلاعات کاربران:** `{ch_text}`\n"
            f"🔢 **تعداد دسترسی ران:** {str(REMAINING_RUNS)}\n"
            f"🚦 **وضعیت ربات:** {status_emoji}\n\n"
            "_Welcome Boss, what's your next command?_"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"وضعیت ربات : {status_emoji}", callback_data="admin_toggle_bot", style=toggle_style)],
            [
                InlineKeyboardButton("مدیریت کاربران", callback_data="admin_user_manage", style='primary'), 
                InlineKeyboardButton("آپدیت همگانی سلف‌ها", callback_data="admin_bulk_update", style='dang
