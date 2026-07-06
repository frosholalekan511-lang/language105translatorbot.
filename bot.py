import logging
import os
import sys
import time
from deep_translator import GoogleTranslator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- RETRY MECHANISM FOR TOKEN ---
MAX_RETRIES = 5
RETRY_DELAY = 5

def get_bot_token():
    """Get token with retry mechanism"""
    for attempt in range(MAX_RETRIES):
        token = (
            os.environ.get("TELEGRAM_BOT_TOKEN") or 
            os.environ.get("BOT_TOKEN") or 
            os.environ.get("TOKEN") or 
            os.environ.get("TELEGRAM_TOKEN")
        )
        
        if token:
            logger.info(f"✅ Token found on attempt {attempt + 1}")
            return token
        
        logger.warning(f"⚠️ No token found (attempt {attempt + 1}/{MAX_RETRIES})")
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
    
    return None

# --- Get Token ---
logger.info("=" * 60)
logger.info("🚀 STARTING BOT...")
logger.info("=" * 60)

TOKEN = get_bot_token()

if not TOKEN:
    logger.error("❌ CRITICAL: No bot token found after all retries!")
    logger.error("Please set TELEGRAM_BOT_TOKEN in Railway variables")
    sys.exit(1)

logger.info(f"✅ Token loaded: {TOKEN[:10]}... (hidden)")

# --- Language Mapping ---
LANGUAGES = {
    "🇺🇸 English": "en",
    "🇪🇸 Spanish": "es",
    "🇫🇷 French": "fr",
    "🇩🇪 German": "de",
    "🇮🇹 Italian": "it",
    "🇵🇹 Portuguese": "pt",
    "🇷🇺 Russian": "ru",
    "🇸🇦 Arabic": "ar",
    "🇨🇳 Chinese": "zh-CN",
    "🇯🇵 Japanese": "ja",
    "🇰🇷 Korean": "ko",
    "🇮🇳 Hindi": "hi",
    "🇹🇷 Turkish": "tr",
    "🇳🇱 Dutch": "nl",
    "🇬🇷 Greek": "el",
    "🇻🇳 Vietnamese": "vi",
    "🇹🇭 Thai": "th",
    "🇮🇩 Indonesian": "id"
}

# --- Helper Functions ---
def get_translated_text(text, target_lang):
    """Translates text with error handling"""
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        translation = translator.translate(text)
        return translation if translation else "⚠️ Translation returned empty result"
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return "⚠️ Sorry, I couldn't translate that. Please try again."

def get_language_keyboard():
    """Creates inline keyboard"""
    keyboard = []
    row = []
    for i, (name, code) in enumerate(LANGUAGES.items()):
        row.append(InlineKeyboardButton(name, callback_data=code))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# --- Bot Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message"""
    try:
        user = update.effective_user
        context.user_data['target_lang'] = 'en'
        
        welcome = (
            f"👋 Hello {user.first_name}!\n\n"
            "🌍 I'm **Language105 Translator Bot**!\n\n"
            "**How to use:**\n"
            "1️⃣ Send any text - I'll translate it\n"
            "2️⃣ Use /lang to change language\n"
            "3️⃣ Default: English\n\n"
            "💡 Use /help for more\n\n"
            "Let's start! 🚀"
        )
        await update.message.reply_text(welcome)
    except Exception as e:
        logger.error(f"Start error: {e}")
        await update.message.reply_text("⚠️ Sorry, something went wrong. Please try again.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help message"""
    help_text = (
        "🤖 **Help Center**\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/help - This help\n"
        "/lang - Change language\n"
        "/languages - All languages\n"
        "/about - About this bot\n\n"
        "**How to Translate:**\n"
        "• Send any text message\n"
        "• I'll translate it automatically"
    )
    await update.message.reply_text(help_text)

async def languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all languages"""
    lang_list = "\n".join([f"• {name}" for name in LANGUAGES.keys()])
    await update.message.reply_text(
        f"🌐 **Supported Languages ({len(LANGUAGES)}):**\n\n{lang_list}"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """About message"""
    about = (
        "🤖 **Language105 Translator Bot**\n\n"
        "Version: 2.0.0\n"
        "Powered by: Google Translate\n"
        "Hosted on: Railway\n\n"
        "📚 18+ languages\n"
        "⚡ Fast & accurate\n"
        "🆓 Completely free"
    )
    await update.message.reply_text(about)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection"""
    try:
        query = update.callback_query
        
        if query:
            await query.answer()
            lang_code = query.data
            context.user_data['target_lang'] = lang_code
            lang_name = next((name for name, code in LANGUAGES.items() if code == lang_code), lang_code)
            await query.edit_message_text(
                f"✅ Language set to **{lang_name}**!\n\n"
                "Now send me text to translate. 📝"
            )
            return
        
        if update.message:
            await update.message.reply_text(
                "🌐 **Choose your target language:**",
                reply_markup=get_language_keyboard()
            )
    except Exception as e:
        logger.error(f"Language selection error: {e}")
        await update.message.reply_text("⚠️ Error setting language. Please try again.")

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main translation function"""
    try:
        if update.message.text.startswith('/'):
            return
        
        user_lang = context.user_data.get('target_lang', 'en')
        text = update.message.text
        
        # Send typing indicator
        await update.message.chat.send_action(action="typing")
        
        # Translate
        translated = get_translated_text(text, user_lang)
        
        # Get language name
        lang_name = next((name for name, code in LANGUAGES.items() if code == user_lang), user_lang)
        
        # Send response
        response = (
            f"🌍 **Translation ({lang_name}):**\n\n"
            f"{translated}\n\n"
            f"💡 Use /lang to change language"
        )
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text("⚠️ Error translating. Please try again.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photos"""
    await update.message.reply_text(
        "🖼️ **Image Received!**\n\n"
        "📝 OCR feature coming soon!\n\n"
        "For now, please send text directly."
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler"""
    logger.error(f"Update {update} caused error: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Something went wrong. Please try again."
            )
    except:
        pass

# --- Main Function ---
def main():
    """Start the bot with error handling"""
    try:
        logger.info("=" * 60)
        logger.info("🤖 INITIALIZING BOT...")
        logger.info("=" * 60)
        
        # Create application
        application = Application.builder().token(TOKEN).build()
        logger.info("✅ Application created")
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("lang", set_language))
        application.add_handler(CommandHandler("languages", languages_command))
        application.add_handler(CommandHandler("about", about_command))
        
        # Language selection callback
        pattern = "|".join(LANGUAGES.values())
        application.add_handler(CallbackQueryHandler(set_language, pattern=pattern))
        
        # Message handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        # Error handler
        application.add_error_handler(error_handler)
        
        logger.info("✅ All handlers registered")
        logger.info("=" * 60)
        logger.info("🚀 BOT IS RUNNING!")
        logger.info(f"📱 @language105translatorbot")
        logger.info("=" * 60)
        
        # Start polling with retry
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        time.sleep(10)
        sys.exit(1)

if __name__ == "__main__":
    main()
