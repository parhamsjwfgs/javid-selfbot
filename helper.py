import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8994843551:AAFbF5KtXf-1RQ0PN5woZUPyZFP6517OAaI"
PANEL_IMAGE_URL = "https://t.me/Sspideermman2/230" 

def create_button(text, callback_data, style=None):
    if style:
        return InlineKeyboardButton(text=text, callback_data=callback_data, style=style)
    return InlineKeyboardButton(text=text, callback_data=callback_data)

def get_all_menu_buttons(user_id, page=1):
    return [
        create_button("سیستم", f"menu_system:{page}:{user_id}"),
        create_button("ادمین", f"menu_admin:{page}:{user_id}"),
        create_button("پروفایل", f"sub_profile:{page}:{user_id}"),
        create_button("سرگرمی", f"menu_fun:{page}:{user_id}"),
        create_button("کاربردی", f"sub_useful:{page}:{user_id}"),
        create_button("دشمن", f"menu_enemy:{page}:{user_id}"),
        create_button("متغیر", f"menu_variable:{page}:{user_id}"),
        create_button("مشنی", f"menu_menshi:{page}:{user_id}"),
        create_button("حالت متن", f"menu_text_mode:{page}:{user_id}"),
        create_button("ری‌اکشن", f"menu_reaction:{page}:{user_id}"),
        create_button("حالت اکشن", f"menu_action:{page}:{user_id}"),
        create_button("اولین کامنت", f"menu_comment:{page}:{user_id}")
    ]

def main_menu_keyboard(user_id, page=1):
    buttons = get_all_menu_buttons(user_id, page)
    per_page = 6
    total_pages = (len(buttons) + per_page - 1) // per_page
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_buttons = buttons[start_idx:end_idx]
    
    keyboard = []

    if len(page_buttons) >= 1:
        keyboard.append([page_buttons[0]])

    if len(page_buttons) >= 3:
        keyboard.append([page_buttons[1], page_buttons[2]])
    elif len(page_buttons) == 2:
        keyboard.append([page_buttons[1]])

    if len(page_buttons) >= 4:
        keyboard.append([page_buttons[3]])

    if len(page_buttons) == 6:
        keyboard.append([page_buttons[4], page_buttons[5]])
    elif len(page_buttons) == 5:
        keyboard.append([page_buttons[4]])

    navigation_row = []
    
    if page > 1:
        navigation_row.append(create_button("《", f"change_page:{page-1}:{user_id}", style="primary"))
    else:
        navigation_row.append(create_button(" ", f"ignore:{user_id}"))
        
    navigation_row.append(create_button(f"{page} از {total_pages}", f"ignore:{user_id}"))
    
    if page < total_pages:
        navigation_row.append(create_button("》", f"change_page:{page+1}:{user_id}", style="primary"))
    else:
        navigation_row.append(create_button(" ", f"ignore:{user_id}"))
        
    keyboard.append(navigation_row)
    keyboard.append([create_button("بستن پنل", f"close_panel:{user_id}", style="danger")])
    
    return InlineKeyboardMarkup(keyboard)

def system_submenu_keyboard(user_id, page):
    return InlineKeyboardMarkup([
        [create_button("دستورات اصلی سیستم", f"sys_main:{page}:{user_id}")],
        [create_button("بخش بکاپ", f"sys_backup:{page}:{user_id}")],
        [create_button("برگشت به منوی اصلی", f"back_to_main:{page}:{user_id}", style='danger')]
    ])

def profile_submenu_keyboard(user_id, page):
    return InlineKeyboardMarkup([
        [create_button("عکس پروفایل", f"prof_pic:{page}:{user_id}"), create_button("بخش اسم", f"prof_name:{page}:{user_id}")],
        [create_button("بخش فامیل", f"prof_last:{page}:{user_id}"), create_button("بخش بیو", f"prof_bio:{page}:{user_id}")],
        [create_button("فونت ساعت و تاریخ", f"prof_fonts:{page}:{user_id}")],
        [create_button("برگشت به منوی اصلی", f"back_to_main:{page}:{user_id}", style='danger')]
    ])

def useful_submenu_keyboard(user_id, page):
    return InlineKeyboardMarkup([
        [create_button("بخش ذخیره", f"use_save_sub:{page}:{user_id}"), create_button("بخش دانلود", f"use_download_sub:{page}:{user_id}")],
        [create_button("نگهبان پیوی", f"use_pv_guard_sub:{page}:{user_id}"), create_button("اکانت و بلاک", f"use_account:{page}:{user_id}")],
        [create_button("تنظیمات چت و پیام", f"use_chat:{page}:{user_id}"), create_button("کاربردی عمومی", f"use_general_sub:{page}:{user_id}")],
        [create_button("برگشت به منوی اصلی", f"back_to_main:{page}:{user_id}", style='danger')]
    ])

def back_to_system_keyboard(user_id, page):
    return InlineKeyboardMarkup([
        [create_button("برگشت به منوی سیستم", f"menu_system:{page}:{user_id}", style='danger')]
    ])

def back_to_profile_keyboard(user_id, page):
    return InlineKeyboardMarkup([
        [create_button("برگشت به منوی پروفایل", f"sub_profile:{page}:{user_id}", style='danger')]
    ])

def back_to_useful_keyboard(user_id, page):
    return InlineKeyboardMarkup([
        [create_button("برگشت به منوی کاربردی", f"sub_useful:{page}:{user_id}", style='danger')]
    ])

def back_keyboard(user_id, page):
    return InlineKeyboardMarkup([
        [create_button("برگشت به منوی اصلی", f"back_to_main:{page}:{user_id}", style='danger')]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        except:
            pass
        await context.bot.send_message(chat_id=update.effective_chat.id, text="هلپر اسپایدر سلف روشن است.\nبرای استفاده از پنل روی دستور زیر کلیک کنید و در چت مورد نظر پیست کنید یا بنویسید <b>پنل</b> \n<code>@helpspiderbot پنل</code>", parse_mode=ParseMode.HTML)

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    query_text = query.query.strip().lower()
    user = query.from_user
    user_id = user.id
    first_name = user.first_name or "قربان"

    if query_text == "پنل":
        results = [
            InlineQueryResultPhoto(
                id="1",
                photo_url=PANEL_IMAGE_URL,
                thumbnail_url=PANEL_IMAGE_URL,
                title="پنل شیشه ای اسپایدرسلف",
                description="برای باز کردن پنل شیشه ای کلیک کنید.",
                caption=f"درود بر شما {first_name}\nبه پنل راهنمای اسپایدرسلف خوش آمدید.\nهر آنچه که نیاز دارید را در این پنل پیدا کنید.",
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_keyboard(user_id, page=1)
            )
        ]
        await query.answer(results, cache_time=0)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data_raw = query.data

    try:
        parts = data_raw.split(":")
        stored_user_id = int(parts[-1])
        data = parts[0]
        page = int(parts[1]) if len(parts) == 3 else 1
    except:
        await query.answer("Unknown Activities", show_alert=True)
        return

    if stored_user_id != user_id:
        await query.answer("این پنل برای شما نیست.\nسلف رایگان | @SelfSazSpiderbot", show_alert=True)
        return

    if data == "ignore":
        await query.answer()
        return

    if data == "close_panel":
        await query.edit_message_caption(caption=f"<b>❈ پنل توسط {query.from_user.first_name} بسته شد.</b>", parse_mode=ParseMode.HTML)
        await query.answer("❈ پنل بسته شد.")
        return

    if data == "change_page":
        await query.edit_message_reply_markup(reply_markup=main_menu_keyboard(user_id, page=page))
        await query.answer()
        return

    if data == "back_to_main":
        await query.edit_message_caption(
            caption="بازگشت به منوی اصلی.\nبه چه چیزی نیاز دارید؟",
            reply_markup=main_menu_keyboard(user_id, page=page)
        )
        await query.answer()
        return

    if data == "menu_system":
        await query.edit_message_text(
            "<b>راهنمای کل سیستم</b>\n\nلطفاً یکی از بخش‌های زیر را انتخاب کنید:",
            reply_markup=system_submenu_keyboard(user_id, page),
            parse_mode=ParseMode.HTML
        )
        await query.answer()
        return

    if data == "sub_profile":
        await query.edit_message_text(
            "<b>راهنمای کل پروفایل</b>\n\nلطفاً یکی از بخش‌های زیر را انتخاب کنید:",
            reply_markup=profile_submenu_keyboard(user_id, page),
            parse_mode=ParseMode.HTML
        )
        await query.answer()
        return

    if data == "sub_useful":
        await query.edit_message_text(
            "<b>راهنمای کل کاربردی</b>\n\nلطفاً یکی از بخش‌های زیر را انتخاب کنید:",
            reply_markup=useful_submenu_keyboard(user_id, page),
            parse_mode=ParseMode.HTML
        )
        await query.answer()
        return

    text = ""
    reply_markup = back_keyboard(user_id, page)

    if data == "sys_main":
        text = (
            "<b>راهنمای اصلی سیستم:</b>\n\n"
            "<code>وضعیت</code>\n"
            "<code>آپدیت</code>\n"
            "<code>ریست</code>\n"
            "<code>پینگ</code>\n"
            "<code>ربات</code> [ روشن | خاموش ]\n\n"
            "<b>توجه: ادمین مجاز به ارسال دستورات [ <code>ریست</code> ] و  [ <code>آپدیت</code> ] نیست!</b>"
        )
        reply_markup = back_to_system_keyboard(user_id, page)

    elif data == "sys_backup":
        text = (
            "<b>راهنمای بخش بکاپ:</b>\n\n"
            "<code>دریافت بکاپ</code>\n"
            "<code>اجرای بکاپ</code> [ ریپلای به فایل بکاپ ]"
        )
        reply_markup = back_to_system_keyboard(user_id, page)

    elif data == "prof_pic":
        text = (
            "<b>راهنمای عکس پروفایل:</b>\n\n"
            "<code>تنظیم پروفایل</code> [ ریپلای ]\n"
            "<code>پروفایل</code> [ روشن | خاموش ]\n"
            "<code>تنظیم زمان پروفایل</code> [ 10-60 ]\n"
            "<code>تنظیم تعداد پروفایل</code> [ 1-100 ]"
        )
        reply_markup = back_to_profile_keyboard(user_id, page)

    elif data == "prof_name":
        text = (
            "<b>راهنمای بخش اسم:</b>\n\n"
            "<code>اسم جدید</code> [ اسم ]\n"
            "<code>حذف اسم</code> [ اسم ]\n"
            "<code>لیست اسم</code>\n"
            "<code>پاکسازی لیست اسم</code>\n"
            "<code>اسم</code> [ روشن | خاموش ]\n"
            "<code>فونت ساعت اسم</code> [ شماره فونت ]\n"
            "<code>فونت تاریخ اسم</code> [ شماره فونت ]\n"
            "<code>تنظیم زمان</code> [ 24 | 12 ]\n"
            "<code>تنظیم تاریخ</code> [ شمسی | میلادی ]"
        )
        reply_markup = back_to_profile_keyboard(user_id, page)

    elif data == "prof_last":
        text = (
            "<b>راهنمای بخش فامیل:</b>\n\n"
            "<code>فامیل جدید</code> [ فامیل ]\n"
            "<code>حذف فامیل</code> [ فامیل ]\n"
            "<code>لیست فامیل</code>\n"
            "<code>پاکسازی لیست فامیل</code>\n"
            "<code>فامیل</code> [ روشن | خاموش ]\n"
            "<code>فونت ساعت فامیل</code> [ شماره فونت ]\n"
            "<code>فونت تاریخ فامیل</code> [ شماره فونت ]\n"
            "<code>تنظیم زمان</code> [ 24 | 12 ]\n"
            "<code>تنظیم تاریخ</code> [ شمسی | میلادی ]"
        )
        reply_markup = back_to_profile_keyboard(user_id, page)

    elif data == "prof_bio":
        text = (
            "<b>راهنمای بخش بیو:</b>\n\n"
            "<code>بیو جدید</code> [ بیو ]\n"
            "<code>حذف بیو</code> [ بیو ]\n"
            "<code>لیست بیو</code>\n"
            "<code>پاکسازی لیست بیو</code>\n"
            "<code>بیو</code> [ روشن | خاموش ]\n"
            "<code>فونت ساعت بیو</code> [ شماره فونت ]\n"
            "<code>فونت تاریخ بیو</code> [ شماره فونت ]\n"
            "<code>تنظیم زمان</code> [ 24 | 12 ]\n"
            "<code>تنظیم تاریخ</code> [ شمسی | میلادی ]"
        )
        reply_markup = back_to_profile_keyboard(user_id, page)

    elif data == "prof_fonts":
        text = (
            "<b>شماره فونت‌ های ساعت و تاریخ:</b>\n\n"
            "1 : 0 1 2 3 4 5 6 7 8 9\n"
            "2 : ۰ ۱ ۲ ۳ ۴ ۵ ۶ ۷ ۸ ۹\n"
            "3 : 𝟶 𝟷 𝟸 𝟹 𝟺 𝟻 𝟼 𝟽 𝟾 𝟿 \n"
            "4 : ₀ ¹ ₂ ³ ₄ ⁵ ₆ ⁷ ₈ ⁹\n"
            "5 : 𝟬 𝟭 𝟮 𝟯 𝟰 𝟱 𝟲 𝟳 𝟴 𝟵\n"
            "6 : 𝟎 𝟏 𝟐 𝟑 𝟒 𝟓 𝟔 𝟕 𝟖 𝟗\n"
            "7 : 𝟢 𝟣 𝟤 𝟥 𝟦 𝟧 𝟨 𝟩 𝟪 𝟫"
        )
        reply_markup = back_to_profile_keyboard(user_id, page)

    elif data == "use_save_sub":
        text = (
            "<b>راهنمای بخش ذخیره:</b>\n\n"
            "<code>ذخیره</code> [ ریپلای | لینک ]\n"
            "<code>ذخیره زماندار</code> [ روشن | خاموش ]\n"
            "<code>ذخیره ویرایش</code>\n"
            "<code>ذخیره حذف</code>\n"
            "<code>ذخیره مدیا</code>"
        )
        reply_markup = back_to_useful_keyboard(user_id, page)

    elif data == "use_download_sub":
        text = (
            "<b>راهنمای بخش دانلود:</b>\n\n"
            "<code>دریافت استوری</code> [ یوزرنیم | ریپلای | آیدی ]\n"
            "<code>دانلود استوری</code> [ یوزرنیم | ریپلای | آیدی ]\n"
            "<code>دانلود اینستا</code> [ لینک ]\n"
            "<code>دانلود یوتیوب</code> [ لینک ]"
        )
        reply_markup = back_to_useful_keyboard(user_id, page)

    elif data == "use_pv_guard_sub":
        text = (
            "<b>راهنمای نگهبان پیوی:</b>\n\n"
            "<code>قفل پیوی</code> [ روشن | خاموش ]\n"
            "<code>سین خودکار پیوی</code> [ روشن | خاموش ]"
        )
        reply_markup = back_to_useful_keyboard(user_id, page)

    elif data == "use_account":
        text = (
            "<b>راهنمای اکانت و بلاک:</b>\n\n"
            "<code>بلاک</code> [ ریپلای | آیدی | یوزرنیم ]\n"
            "<code>آنبلاک</code> [ ریپلای | آیدی | یوزرنیم ]\n"
            "<code>آیدی</code> [ ریپلای | آیدی | یوزرنیم ]\n"
            "<code>لفت همگانی کانال</code>\n"
            "<code>لفت همگانی گروه</code>"
        )
        reply_markup = back_to_useful_keyboard(user_id, page)

    elif data == "use_chat":
        text = (
            "<b>راهنمای تنظیمات چت و پیام:</b>\n\n"
            "<code>اسپم</code> [ ریپلای یا متن | تعداد ]\n"
            "<code>پاکسازی من</code> [ همه | عدد ]"
        )
        reply_markup = back_to_useful_keyboard(user_id, page)

    elif data == "use_general_sub":
        text = (
            "<b>راهنمای کاربردی عمومی:</b>\n\n"
            "<code>آنلاین</code> [ روشن | خاموش ]\n"
            "<code>هوش مصنوعی</code> [ سوال ]\n"
            "<code>آنتی لاگین</code> [ روشن | خاموش ]\n"
            "<code>امروز</code>"
        )
        reply_markup = back_to_useful_keyboard(user_id, page)

    elif data == "menu_admin":
        text = (
            "<b>راهنمای ادمین:</b>\n\n"
            "<code>تنظیم ادمین</code> [ یوزرنیم | ریپلای | آیدی ]\n"
            "<code>حذف ادمین</code> [ یوزرنیم | ریپلای | آیدی ]\n"
            "<code>پاکسازی لیست ادمین</code>\n"
            "<code>لیست ادمین</code>\n"
            "<code>وضعیت ادمین</code> [ نماد | عدد | حروف ]\n\n"
            "<b>توجه: ادمین مجاز به ارسال این دستورات نیست!</b>"
        )
    elif data == "menu_variable":
        text = (
            "<b>راهنمای متغیر:</b>\n\n"
            "<code>ساعت</code>\n"
            "<code>تاریخ</code>\n\nنکته : نگاه کنید برای اینکه اونجایی که میخاید ساعت یا تاریخ بیفته این متغیر هارو اونجا بزارید بعد میفته."
        )
    elif data == "menu_enemy":
        text = (
            "<b>راهنمای دشمن:</b>\n\n"
            "<code>تنظیم دشمن</code> [ ریپلای | آیدی | یوزرنیم ]\n"
            "<code>حذف دشمن</code> [ آیدی | یوزرنیم ]\n"
            "<code>پاکسازی لیست دشمن</code>\n"
            "<code>لیست دشمن</code>\n"
            "<code>تنظیم فحش</code> [ متن ]\n"
            "<code>لیست فحش</code>\n"
            "<code>تنظیم لیست فحش</code> [ ریپلای روی فایل txt ]"
        )
    elif data == "menu_menshi":
        text = (
            "<b>راهنمای منشی:</b>\n\n"
            "<code>منشی</code> [ روشن | خاموش ]\n"
            "<code>تنظیم منشی</code> [ متن ]\n"
            "<code>تنظیم زمان منشی</code> [ عدد به ثانیه ]"
        )
    elif data == "menu_text_mode":
        text = (
            "<b>راهنمای حالت متن:</b>\n\n"
            "<code>تنظیم حالت</code> [ بولد | ایتالیک | زیرخط | کدینگ | مونو | ساده ]\n"
            "<code>حالت متن خاموش</code>"
        )
    elif data == "menu_fun":
        text = (
            "<b>راهنمای سرگرمی:</b>\n\n"
            "<code>ربات</code>"
        )
    elif data == "menu_reaction":
        text = (
            "<b>راهنمای ری اکشن:</b>\n\n"
            "<code>تنظیم ری اکشن</code> [ ایموجی | ریپلای | یوزرنیم | آیدی ]\n"
            "<code>حذف ری اکشن</code>\n"
            "<code>لیست ری اکشن</code>\n"
            "<code>پاکسازی لیست ری اکشن</code>"
        )
    elif data == "menu_comment":
        text = (
            "<b>راهنمای کامنت اول:</b>\n\n"
            "<code>تنظیم کامنت اول</code> [ یوزرنیم | آیدی ]\n"
            "<code>حذف کامنت اول</code>\n"
            "<code>تنظیم کامنت</code>\n"
            "<code>لیست کامنت</code>\n"
            "<code>پاکسازی لیست کامنت</code>"
        )
    elif data == "menu_action":
        text = (
            "<b>راهنمای حالت اکشن:</b>\n\n"
            "<code>حالت چت</code> [ پیوی | گروه | روشن | خاموش ]\n"
            "<code>حالت بازی</code> [ پیوی | گروه | روشن | خاموش ]\n"
            "<code>حالت ویس</code> [ پیوی | گروه | روشن | خاموش ]"
        )

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    await query.answer()

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(inline_handler))
    application.add_handler(CallbackQueryHandler(callback_handler))
    print("Helper is Running...")
    application.run_polling()

if __name__ == "__main__":
    main()