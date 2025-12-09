import os
import re
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.downloader import VideoDownloader

# إعدادات البوت
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
downloader = VideoDownloader()

# دعم المنصات
SUPPORTED_PLATFORMS = {
    'youtube': 'YouTube',
    'instagram': 'Instagram',
    'tiktok': 'TikTok',
    'facebook': 'Facebook',
    'twitter': 'Twitter'
}

# تعريف الأنماط
URL_PATTERNS = {
    'youtube': r'(youtube\.com|youtu\.be)',
    'instagram': r'instagram\.com',
    'tiktok': r'tiktok\.com',
    'facebook': r'facebook\.com|fb\.watch',
    'twitter': r'twitter\.com|x\.com'
}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
🎬 *مرحباً بك في بوت تحميل الفيديوهات* 🎬

*المميزات:*
✅ تحميل من YouTube
✅ تحميل من Instagram (Reels/Posts)
✅ تحميل من TikTok
✅ تحميل من Facebook/Reels
✅ اختيار الجودة المتاحة

*كيفية الاستخدام:*
1. أرسل رابط الفيديو
2. اختر الجودة المناسبة
3. انتظر التحميل

*المنصات المدعومة:*
- YouTube
- Instagram
- TikTok
- Facebook
- Twitter/X

🚀 *ابدأ بإرسال رابط الآن!*
"""
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['supported'])
def supported_platforms(message):
    platforms_text = "📱 *المنصات المدعومة:*\n\n"
    for key, name in SUPPORTED_PLATFORMS.items():
        platforms_text += f"✅ {name}\n"
    
    platforms_text += "\n🚫 *غير مدعوم:*\n"
    platforms_text += "❌ Netflix\n❌ Disney+\n❌ المنصات المحمية"
    
    bot.send_message(message.chat.id, platforms_text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    
    # التحقق من وجود روابط
    urls = extract_urls(text)
    
    if not urls:
        bot.reply_to(message, "❌ لم أجد أي رابط في رسالتك.\nأرسل رابط فيديو من إحدى المنصات المدعومة.")
        return
    
    for url in urls:
        platform = detect_platform(url)
        
        if not platform:
            bot.reply_to(message, f"❌ المنصة غير مدعومة أو رابط غير صالح.\nالرابط: {url}")
            continue
        
        # إرسال رسالة الانتظار
        wait_msg = bot.reply_to(message, f"⏳ جارٍ تحليل الرابط من {SUPPORTED_PLATFORMS.get(platform, platform)}...")
        
        try:
            # تحليل الرابط والحصول على المعلومات
            video_info = downloader.get_video_info(url, platform)
            
            if not video_info:
                bot.edit_message_text(
                    f"❌ لم أتمكن من تحميل معلومات الفيديو من {platform}",
                    chat_id=message.chat.id,
                    message_id=wait_msg.message_id
                )
                continue
            
            # إنشاء زر لاختيار الجودة
            keyboard = InlineKeyboardMarkup()
            
            if 'qualities' in video_info and video_info['qualities']:
                for quality in video_info['qualities'][:5]:  # عرض أول 5 خيارات فقط
                    keyboard.add(InlineKeyboardButton(
                        text=f"⬇️ {quality}",
                        callback_data=f"download_{platform}_{quality}_{url}"
                    ))
            else:
                keyboard.add(InlineKeyboardButton(
                    text="⬇️ تحميل الفيديو",
                    callback_data=f"download_{platform}_default_{url}"
                ))
            
            # إرسال معلومات الفيديو
            caption = f"""
📹 *معلومات الفيديو:*
📌 *المصدر:* {SUPPORTED_PLATFORMS.get(platform, platform)}
🏷️ *العنوان:* {video_info.get('title', 'غير معروف')}
⏱️ *المدة:* {video_info.get('duration', 'غير معروف')}
👁️ *المشاهدات:* {video_info.get('views', 'غير معروف')}
👍 *الإعجابات:* {video_info.get('likes', 'غير معروف')}

⬇️ *اختر جودة التحميل:*
"""
            bot.edit_message_text(
                caption,
                chat_id=message.chat.id,
                message_id=wait_msg.message_id,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
        except Exception as e:
            bot.edit_message_text(
                f"❌ حدث خطأ أثناء تحليل الرابط: {str(e)}",
                chat_id=message.chat.id,
                message_id=wait_msg.message_id
            )

@bot.callback_query_handler(func=lambda call: call.data.startswith('download_'))
def handle_download(call):
    try:
        # تحليل البيانات
        _, platform, quality, url = call.data.split('_', 3)
        url = url.replace('%%%', '/')
        
        # تحديث الرسالة
        bot.answer_callback_query(call.id, "⏳ جارٍ التحميل...")
        
        processing_msg = bot.send_message(
            call.message.chat.id,
            f"⏳ جارٍ تحميل الفيديو من {SUPPORTED_PLATFORMS.get(platform, platform)}..."
        )
        
        # تحميل الفيديو
        video_path = downloader.download_video(url, platform, quality)
        
        if not video_path or not os.path.exists(video_path):
            bot.edit_message_text(
                "❌ فشل تحميل الفيديو",
                chat_id=call.message.chat.id,
                message_id=processing_msg.message_id
            )
            return
        
        # إرسال الفيديو
        with open(video_path, 'rb') as video_file:
            bot.send_video(
                call.message.chat.id,
                video_file,
                caption=f"✅ تم التحميل بنجاح!\n📌 المصدر: {SUPPORTED_PLATFORMS.get(platform, platform)}\n⚡ الجودة: {quality}",
                reply_to_message_id=call.message.message_id
            )
        
        bot.delete_message(call.message.chat.id, processing_msg.message_id)
        
        # حذف الملف المؤقت
        try:
            os.remove(video_path)
        except:
            pass
            
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ حدث خطأ: {str(e)}")

def extract_urls(text):
    """استخراج الروابط من النص"""
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)

def detect_platform(url):
    """كشف المنصة من الرابط"""
    for platform, pattern in URL_PATTERNS.items():
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return None

# Webhook endpoints
@app.route('/')
def home():
    return "🎬 Video Downloader Bot is running!"

@app.route('/health')
def health():
    return {"status": "healthy", "service": "video-downloader-bot"}

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Bad request', 400

if __name__ == '__main__':
    # تنظيف أي webhook سابق
    bot.remove_webhook()
    
    # تعيين webhook جديد
    app_url = os.environ.get('RENDER_URL', 'https://tele-down1.onrender.com')
    bot.set_webhook(url=f"{app_url}/webhook")
    print(f"✅ Webhook set to: {app_url}/webhook")
    
    # تشغيل الخادم
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
