import os
import re
import html
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8909156348:AAESlvw-ej2xEwiZIR0GWbCE3o_2nB7DI8s"

CHANNEL_USERNAME = "@Riiin69"
SUPPORT_USERNAME = "@rvviii69"

ADMIN_ID = 7195085575  

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Subscription Check Error: {e}")
        return False

async def delete_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_ids: list, delay: int = 30):
    await asyncio.sleep(delay)
    for msg_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = html.escape(update.effective_user.first_name or "المستخدم")

    is_subscribed = await check_subscription(user_id, context)

    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة هنا", url="https://t.me/Riiin69")],
            [InlineKeyboardButton("✅ تم الاشتراك (تحقق)", callback_data="check_sub")],
            [InlineKeyboardButton("🛠️ الدعم الفني والخدمات", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"أهلاً وسهلاً بك يا {user_name}! 🌸✨\n\n"
            f"⚠️ <b>لاستخدام البوت والاستفادة من خدماته، يرجى الاشتراك في القناة أولاً.</b>\n\n"
            f"اشترك في القناة ثم اضغط على زر (تم الاشتراك) أو أرسل رابط المقطع مباشرة! 🚀\n\n"
            f"📩 في حال مواجهة أي مشكلة أو للاستفسار: {SUPPORT_USERNAME}",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        return

    keyboard = [
        [InlineKeyboardButton("🛠️ الدعم الفني والخدمات", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"يا أهلاً وسهلاً بك يا {user_name}! 🌟🎬\n\n"
        f"البوت الشامل جاهز لخدمتك لتحميل المقاطع والوسائط من جميع المنصات:\n"
        f"📌 (X / TikTok / Instagram / YouTube Shorts / Facebook)\n\n"
        f"💡 <b>طريقة الاستخدام:</b>\n"
        f"أرسل رابط المقطع مباشرة وسأقوم بمعالجته وتحميله لك خلال لحظات.\n\n"
        f"📩 <b>عند مواجهة أي مشكلة:</b> {SUPPORT_USERNAME}",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def check_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_name = html.escape(query.from_user.first_name or "المستخدم")

    is_subscribed = await check_subscription(user_id, context)

    if is_subscribed:
        keyboard = [
            [InlineKeyboardButton("🛠️ الدعم الفني والخدمات", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"تم التحقق بنجاح! 🎉\nأهلاً بك يا {user_name}، أرسل الآن رابط المقطع وسأقوم بتحميله لك فوراً.",
            reply_markup=reply_markup
        )
    else:
        await query.answer("⚠️ لم يتم العثور على اشتراكك في القناة بعد، يرجى الاشتراك أولاً!", show_alert=True)

def download_with_ytdlp(url: str, user_id: int):
    output_filename = f"dl_{user_id}.mp4"
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 49 * 1024 * 1024,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if os.path.exists(output_filename):
        return output_filename
    return None

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = html.escape(update.effective_user.first_name or "المستخدم")
    chat_id = update.effective_chat.id
    url = update.message.text.strip()

    if not re.search(r'https?://[^\s]+', url):
        return

    is_subscribed = await check_subscription(user_id, context)

    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة هنا", url="https://t.me/Riiin69")],
            [InlineKeyboardButton("✅ تم الاشتراك (تحقق)", callback_data="check_sub")],
            [InlineKeyboardButton("🛠️ الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"⚠️ لا يمكنك تحميل المحتوى حتى تشترك في القناة أولاً!\n\n"
            f"للدعم الفني: {SUPPORT_USERNAME}",
            reply_markup=reply_markup
        )
        return

    msg = await update.message.reply_text("جاري استخراج المقطع وتحميله...")

    try:
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_with_ytdlp, url, user_id)

        if not file_path or not os.path.exists(file_path):
            await msg.edit_text(f"تعذر تحميل المقطع. قد يكون الحساب خاصاً أو حجم المقطع كبيراً جداً.\n\nللدعم الفني: {SUPPORT_USERNAME}")
            return

        caption_text = "تم التحميل بنجاح ✨\n⏱️ سيتم حذف هذا المحتوى ورابطك تلقائياً بعد 30 ثانية."
        admin_caption = f"📥 <b>سجل تحميل جديد</b>\n👤 المستخدم: {user_name} (<code>{user_id}</code>)\n🔗 الرابط: {html.escape(url)}"

        with open(file_path, "rb") as f:
            sent_v = await update.message.reply_video(video=f, caption=caption_text)

        try:
            with open(file_path, "rb") as f_admin:
                await context.bot.send_video(chat_id=ADMIN_ID, video=f_admin, caption=admin_caption, parse_mode="HTML")
        except Exception as admin_err:
            print(f"Admin Log Failed: {admin_err}")

        if os.path.exists(file_path):
            os.remove(file_path)

        await msg.delete()

        delete_list = [sent_v.message_id, update.message.message_id]
        asyncio.create_task(
            delete_after_delay(
                context, 
                chat_id=chat_id, 
                message_ids=delete_list, 
                delay=30
            )
        )

    except Exception as e:
        print(f"General Download Error: {e}")
        await msg.edit_text(f"حدث خطأ أثناء تحميل المقطع، تأكد من صحة الرابط.\n\nللدعم الفني: {SUPPORT_USERNAME}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_button_callback, pattern="^check_sub$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()
