import os
import re
import uuid
import shutil
import asyncio
import logging
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(level=logging.INFO)

TOKEN = "8909156348:AAESlvw-ej2xEwiZIR0GWbCE3o_2nB7DI8s"

SUPPORTED_DOMAINS = re.compile(r'(tiktok\.com|instagram\.com|twitter\.com|x\.com|snapchat\.com)')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل رابط (تيك توك، إنستغرام، تويتر، سناب شات) لتحميل المقاطع والصور مباشرة.\n\nللدعم الفني: @rvviii69")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not SUPPORTED_DOMAINS.search(url):
        return

    status_msg = await update.message.reply_text("⏳ جاري جلب وسائط الرابط...")

    session_id = str(uuid.uuid4())
    download_dir = os.path.join('downloads', session_id)
    os.makedirs(download_dir, exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join(download_dir, '%(id)s_%(autonumber)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'writesubtitles': False,
        'ignoreerrors': True,
        'format': 'best',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        }
    }

    try:
        loop = asyncio.get_event_loop()
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)
        
        info = await loop.run_in_executor(None, download)
        
        if not info:
            await status_msg.edit_text("❌ لم يتم العثور على محتوى أو الحساب خاص.")
            return

        downloaded_files = []
        if os.path.exists(download_dir):
            for f in os.listdir(download_dir):
                file_path = os.path.join(download_dir, f)
                if os.path.isfile(file_path):
                    downloaded_files.append(file_path)

        if not downloaded_files:
            await status_msg.edit_text("❌ تعذر تحميل الوسائط من هذا الرابط.")
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

        if len(media_group) == 1:
            with open(downloaded_files[0], 'rb') as f_single:
                if isinstance(media_group[0], InputMediaPhoto):
                    await update.message.reply_photo(photo=f_single)
                else:
                    await update.message.reply_video(video=f_single)
        elif len(media_group) > 1:
            for i in range(0, len(media_group), 10):
                await update.message.reply_media_group(media=media_group[i:i+10])

        for f in opened_files:
            f.close()
            
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Download Error: {e}")
        await status_msg.edit_text("❌ حدث خطأ أثناء التحميل. تأكد من صحة الرابط وأن الحساب ليس خاصاً.")

    finally:
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir, ignore_errors=True)

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()
