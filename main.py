import os
import re
import html
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8909156348:AAFn4Ys3sjr4jnYlPxKzp9jXsILVBc7INYs"
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
            f"اشترك في القناة ثم اضغط على زر (تم الاشتراك) أو أرسل رابط التغريدة مباشرة! 🚀\n\n"
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
        f"البوت جاهز لخدمتك لتحميل المقاطع والصور من منصة X/تويتر بأعلى جودة. 🚀\n\n"
        f"📌 <b>طريقة الاستخدام:</b>\n"
        f"أرسل لي رابط التغريدة مباشرة وسأقوم بتحميل الوسائط لك فوراً.\n\n"
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
            f"تم التحقق بنجاح! 🎉\nأهلاً بك يا {user_name}، أرسل الآن رابط التغريدة وسأقوم بتحميل الوسائط لك فوراً.",
            reply_markup=reply_markup
        )
    else:
        await query.answer("⚠️ لم يتم العثور على اشتراكك في القناة بعد، يرجى الاشتراك أولاً!", show_alert=True)

def fetch_tweet_data(tweet_id: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(f"https://api.fxtwitter.com/status/{tweet_id}", headers=headers, timeout=10).json()
        if res.get("code") == 200 and "tweet" in res:
            return res["tweet"], "fxtwitter"
    except Exception as e:
        print(f"fxtwitter API Error: {e}")

    try:
        res = requests.get(f"https://api.vxtwitter.com/status/{tweet_id}", headers=headers, timeout=10).json()
        if res:
            return res, "vxtwitter"
    except Exception as e:
        print(f"vxtwitter API Error: {e}")

    return None, None

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = html.escape(update.effective_user.first_name or "المستخدم")
    chat_id = update.effective_chat.id
    url = update.message.text.strip()

    if "twitter.com" not in url and "x.com" not in url:
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

    msg = await update.message.reply_text("جاري استخراج المحتوى وتحميله...")

    try:
        match = re.search(r'status/(\d+)', url)
        if not match:
            await msg.edit_text(f"الرابط غير صحيح، يرجى التأكد منه.\n\nللدعم الفني: {SUPPORT_USERNAME}")
            return

        tweet_id = match.group(1)
        loop = asyncio.get_event_loop()
        tweet_data, source = await loop.run_in_executor(None, fetch_tweet_data, tweet_id)

        if not tweet_data:
            await msg.edit_text(f"تعذر استخراج البيانات من هذا الرابط. قد تكون التغريدة خاصة أو محذوفة.\n\nللدعم الفني: {SUPPORT_USERNAME}")
            return

        sent_messages = []
        caption_text = "تم التحميل بنجاح ✨\n⏱️ سيتم حذف هذا المحتوى ورابطك تلقائياً بعد 30 ثانية."
        admin_caption = f"📥 <b>سجل تحميل جديد</b>\n👤 المستخدم: {user_name} (<code>{user_id}</code>)\n🔗 الرابط: {html.escape(url)}"

        video_url = None
        photos_urls = []

        if source == "fxtwitter":
            media_info = tweet_data.get("media", {})
            videos = media_info.get("videos", [])
            photos = media_info.get("photos", [])

            if videos:
                video_url = videos[0].get("url")
            elif photos:
                photos_urls = [p.get("url") for p in photos if p.get("url")]

        elif source == "vxtwitter":
            media_extend = tweet_data.get("media_extend", [])
            for item in media_extend:
                if item.get("type") == "video":
                    video_url = item.get("url")
                    break
                elif item.get("type") == "image":
                    photos_urls.append(item.get("url"))
            
            if not video_url and not photos_urls:
                if tweet_data.get("video_url"):
                    video_url = tweet_data.get("video_url")

        if video_url:
            headers = {"User-Agent": "Mozilla/5.0"}
            video_bytes = await loop.run_in_executor(None, lambda: requests.get(video_url, headers=headers).content)
            
            file_path = f"temp_video_{user_id}.mp4"
            with open(file_path, "wb") as f:
                f.write(video_bytes)

            try:
                with open(file_path, "rb") as f:
                    sent_v = await update.message.reply_video(video=f, caption=caption_text)
                    sent_messages.append(sent_v.message_id)

                try:
                    with open(file_path, "rb") as f_admin:
                        await context.bot.send_video(chat_id=ADMIN_ID, video=f_admin, caption=admin_caption, parse_mode="HTML")
                except Exception as admin_err:
                    print(f"Admin Log Failed: {admin_err}")

            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

        elif photos_urls:
            if len(photos_urls) == 1:
                photo_url = photos_urls[0]
                sent_p = await update.message.reply_photo(photo=photo_url, caption=caption_text)
                sent_messages.append(sent_p.message_id)

                try:
                    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_url, caption=admin_caption, parse_mode="HTML")
                except Exception as admin_err:
                    print(f"Admin Log Failed: {admin_err}")
            else:
                media_group = [InputMediaPhoto(media=p_url, caption=caption_text if i == 0 else "") for i, p_url in enumerate(photos_urls)]
                sent_group = await update.message.reply_media_group(media=media_group)
                sent_messages.extend([m.message_id for m in sent_group])

                try:
                    admin_media = [InputMediaPhoto(media=p_url, caption=admin_caption if i == 0 else "", parse_mode="HTML") for i, p_url in enumerate(photos_urls)]
                    await context.bot.send_media_group(chat_id=ADMIN_ID, media=admin_media)
                except Exception as admin_err:
                    print(f"Admin Log Failed: {admin_err}")
        else:
            await msg.edit_text(f"لم يتم العثور على صور أو مقاطع فيديو داخل هذه التغريدة.\n\nللدعم الفني: {SUPPORT_USERNAME}")
            return

        await msg.delete()

        delete_list = sent_messages + [update.message.message_id]
        asyncio.create_task(
            delete_after_delay(
                context, 
                chat_id=chat_id, 
                message_ids=delete_list, 
                delay=30
            )
        )

    except Exception as e:
        print(f"Error: {e}")
        await msg.edit_text(f"حدث خطأ أثناء جلب الفيديو، تأكد من صحة الرابط.\n\nللدعم الفني: {SUPPORT_USERNAME}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_button_callback, pattern="^check_sub$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()
