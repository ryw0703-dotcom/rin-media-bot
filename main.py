import os
import re
import uuid
import shutil
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(level=logging.INFO)

TOKEN = "8909156348:AAESlvw-ej2xEwiZIR0GWbCE3o_2nB7DI8s"
ADMIN_ID = 5664157833             # آيدي حسابك لتلقي الرسائل
CHANNEL_USERNAME = "@rin_media"  # يوزر قناتك لشرط الاشتراك

SUPPORTED_DOMAINS = re.compile(r'(tiktok\.com|instagram\.com|twitter\.com|x\.com|snapchat\.com)')

# التحقق من اشتراك المستخدم في القناة
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Subscription Check Error: {e}")
        return True  # في حال وجود خطأ في الصلاحيات لا نعطل المستخدم

# رسالة الترحيب والأزرار
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    welcome_text = (
        f"<b>أهلاً بك عزيزي {user.first_name} ✨📥</b>\n\n"
        "🎬 <b>بوت التحميل الشامل للوسائط:</b>\n"
        "• <b>تيك توك</b> 🎵 (مقاطع - صور - ستوريات)\n"
        "• <b>إنستغرام</b> 📸 (ستوريات - هايلات - ريلز - صور)\n"
        "• <b>سناب شات</b> 👻 (منشورات - ستوريات)\n"
        "• <b>تويتر / X</b> 🐦 (فيديوهات - صور)\n\n"
        "📌 <i>ملاحظة: تُحذف المقاطع والوسائط تلقائياً بعد 30 ثانية للحفاظ على الخصوصية والمساحة ⏱️</i>"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📢 قناة البوت", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"),
            InlineKeyboardButton("👨‍💻 الدعم الفني", url="https://t.me/rvviii69")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)

# حذف الرسائل تلقائياً بعد 30 ثانية
async def auto_delete_messages(bot, chat_id, message_ids, delay=30):
    await asyncio.sleep(delay)
    for msg_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass

# التفاعل مع الأزرار (تحقق من الاشتراك)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_sub":
        subscribed = await is_subscribed(query.from_user.id, context)
        if subscribed:
            await query.message.delete()
            await query.message.reply_text("✅ <b>تم التحقق بنجاح! يمكنك الآن إرسال أي رابط لتحميله ✨</b>", parse_mode='HTML')
        else:
            await query.answer("❌ للأسف لم تشترك بالقناة بعد! اشترك ثم اضغط تحقق.", show_alert=True)

# معالجة الرسائل والروابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text.strip() if update.message.text else ""

    # 1. توجيه جميع رسائل العالم للإدمن فوراً 📩
    if user.id != ADMIN_ID:
        try:
            admin_log = (
                f"📬 <b>رسالة جديدة من مستخدم:</b>\n"
                f"👤 <b>الاسم:</b> {user.full_name}\n"
                f"ج <b>اليوزر:</b> @{user.username if user.username else 'بدون يوزر'}\n"
                f"🆔 <b>ID:</b> <code>{user.id}</code>\n\n"
                f"💬 <b>المحتوى:</b>\n<code>{text}</code>"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_log, parse_mode='HTML')
        except Exception as e:
            logging.error(f"Failed to forward to admin: {e}")

    # 2. شرط الاشتراك الإجباري 🔒
    subscribed = await is_subscribed(user.id, context)
    if not subscribed:
        sub_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك في القناة أولاً", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")]
        ])
        await update.message.reply_text(
            "⚠️ <b>عذراً عزيزي! يجب عليك الاشتراك في القناة أولاً لاستخدام البوت:</b>",
            parse_mode='HTML',
            reply_markup=sub_keyboard
        )
        return

    if not SUPPORTED_DOMAINS.search(text):
        return

    status_msg = await update.message.reply_text("⏳ <b>جاري جلب الوسائط والستوريات...</b>", parse_mode='HTML')

    session_id = str(uuid.uuid4())
    download_dir = os.path.join('downloads', session_id)
    os.makedirs(download_dir, exist_ok=True)

    # إعدادات yt-dlp المتطورة للستوريات والهايلات والمقاطع
    ydl_opts = {
        'outtmpl': os.path.join(download_dir, '%(id)s_%(autonumber)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'writesubtitles': False,
        'ignoreerrors': True,
        'format': 'bestvideo+bestaudio/best',
        'concurrent_fragment_downloads': 5,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }

    try:
        loop = asyncio.get_event_loop()
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(text, download=True)
        
        info = await loop.run_in_executor(None, download)
        
        if not info:
            await status_msg.edit_text("❌ <b>تعذر العثور على محتوى، أو أن الحساب خاص.</b>", parse_mode='HTML')
            return

        downloaded_files = []
        if os.path.exists(download_dir):
            for f in os.listdir(download_dir):
                file_path = os.path.join(download_dir, f)
                if os.path.isfile(file_path):
                    downloaded_files.append(file_path)

        if not downloaded_files:
            await status_msg.edit_text("❌ <b>لم يتم العثور على وسائط قابلة للتحميل في هذا الرابط.</b>", parse_mode='HTML')
            return

        media_group = []
        opened_files = []

        for filepath in downloaded_files:
            ext = os.path.splitext(filepath)[1].lower()
            f = open(filepath, 'rb')
            opened_files.append(f)
            
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                media_group.append(InputMediaPhoto(media=f))
            elif ext in ['.mp4', '.mkv', '.mov', '.webm']:
                media_group.append(InputMediaVideo(media=f))

        sent_messages = []
        if len(media_group) == 1:
            with open(downloaded_files[0], 'rb') as f_single:
                if isinstance(media_group[0], InputMediaPhoto):
                    m = await update.message.reply_photo(photo=f_single)
                else:
                    m = await update.message.reply_video(video=f_single)
                sent_messages.append(m.message_id)
        elif len(media_group) > 1:
            for i in range(0, len(media_group), 10):
                msgs = await update.message.reply_media_group(media=media_group[i:i+10])
                sent_messages.extend([m.message_id for m in msgs])

        for f in opened_files:
            f.close()
            
        await status_msg.delete()

        # جدولة الحذف التلقائي للملفات بعد 30 ثانية ⏱️
        if sent_messages:
            asyncio.create_task(auto_delete_messages(context.bot, chat_id, sent_messages, delay=30))

    except Exception as e:
        logging.error(f"Download Error: {e}")
        await status_msg.edit_text("❌ <b>حدث خطأ أثناء جلب الوسائط، تأكد أن الحساب ليس خاصاً.</b>", parse_mode='HTML')

    finally:
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir, ignore_errors=True)

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()
