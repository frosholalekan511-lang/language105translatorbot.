import logging
import os
import sys
from deep_translator import GoogleTranslator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Token Configuration (Multiple Fallbacks) ---
TOKEN = (
    os.environ.get("TELEGRAM_BOT_TOKEN") or 
    os.environ.get("BOT_TOKEN") or 
    os.environ.get("TOKEN") or 
    os.environ.get("TELEGRAM_TOKEN")
)

# Debug: Check if token exists
logger.info("=" * 50)
logger.info("🔍 Checking Environment Variables...")
logger.info(f"TELEGRAM_BOT_TOKEN: {'✅ SET' if os.environ.get('TELEGRAM_BOT_TOKEN') else '❌ NOT SET'}")
logger.info(f"BOT_TOKEN: {'✅ SET' if os.environ.get('BOT_TOKEN') else '❌ NOT SET'}")
logger.info(f"TOKEN: {'✅ SET' if os.environ.get('TOKEN') else '❌ NOT SET'}")
logger.info("=" * 50)

if not TOKEN:
    logger.error("❌ CRITICAL: No bot token found in environment variables!")
    logger.error("Please add TELEGRAM_BOT_TOKEN to Railway variables.")
    logger.error("Example: TELEGRAM_BOT_TOKEN = 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
    sys.exit(1)

logger.info(f"✅ Bot token loaded successfully!")
logger.info(f"Token starts with: {TOKEN[:10]}... (hidden for security)")

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
    """Translates text using Google Translate."""
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        translation = translator.translate(text)
        return translation
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return "⚠️ Translation failed. Please try again."

def get_language_keyboard():
    """Creates inline keyboard with language options."""
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
    """Send welcome message."""
    user = update.effective_user
    context.user_data['target_lang'] = 'en'
    
    welcome_text = (
        f"👋 Hello {user.first_name}!\n\n"
        "🌍 I'm **Language105 Translator Bot**!\n\n"
        "**How to use me:**\n"
        "1️⃣ Send any text and I'll translate it\n"
        "2️⃣ Use /lang to change language\n"
        "3️⃣ Current language: English\n\n"
        "💡 Use /help for more commands\n\n"
        "Let's start! 🚀"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    help_text = (
        "🤖 **Help Center**\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/lang - Change language\n"
        "/languages - List all languages\n"
        "/about - About this bot\n\n"
        "**How to Translate:**\n"
        "• Send any text message\n"
        "• I'll translate it automatically\n"
        "• Use /lang to switch languages"
    )
    await update.message.reply_text(help_text)

async def languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all supported languages."""
    lang_list = "\n".join([f"• {name}" for name in LANGUAGES.keys()])
    await update.message.reply_text(
        f"🌐 **Supported Languages ({len(LANGUAGES)}):**\n\n{lang_list}\n\n"
        "Use /lang to change your target language."
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show about information."""
    about_text = (
        "🤖 **Language105 Translator Bot**\n\n"
        "Version: 1.0.0\n"
        "Powered by: Google Translate\n"
        "Hosted on: Railway\n\n"
        "📚 Translates into 18+ languages\n"
        "⚡ Fast and accurate\n"
        "🆓 Completely free to use"
    )
    await update.message.reply_text(about_text)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection."""
    query = update.callback_query
    
    if query:
        await query.answer()
        lang_code = query.data
        context.user_data['target_lang'] = lang_code
        lang_name = next((name for name, code in LANGUAGES.items() if code == lang_code), lang_code)
        await query.edit_message_text(
            f"✅ Language set to **{lang_name}**!\n\n"
            "Now send me any text to translate. 📝"
        )
        return
    
    if update.message:
        await update.message.reply_text(
            "🌐 **Choose your target language:**",
            reply_markup=get_language_keyboard()
        )

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Translate incoming text messages."""
    if update.message.text.startswith('/'):
        return
    
    user_lang = context.user_data.get('target_lang', 'en')
    text = update.message.text
    
    await update.message.chat.send_action(action="typing")
    
    translated = get_translated_text(text, user_lang)
    lang_name = next((name for name, code in LANGUAGES.items() if code == user_lang), user_lang)
    
    response = (
        f"🌍 **Translation ({lang_name}):**\n\n"
        f"{translated}\n\n"
        f"💡 Use /lang to change language"
    )
    await update.message.reply_text(response)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages."""
    await update.message.reply_text(
        "🖼️ **Image Received!**\n\n"
        "📝 OCR feature is coming soon!\n\n"
        "For now, please send text directly for translation."
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors."""
    logger.error(f"Update {update} caused error: {context.error}")

# --- Main Function ---
def main() -> None:
    """Start the bot."""
    try:
        # Create application
        application = Application.builder().token(TOKEN).build()
        
        # Register command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("lang", set_language))
        application.add_handler(CommandHandler("languages", languages_command))
        application.add_handler(CommandHandler("about", about_command))
        
        # Register callback handler for language buttons
        application.add_handler(CallbackQueryHandler(
            set_language, 
            pattern="|".join(LANGUAGES.values())
        ))
        
        # Register message handlers
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            translate_text
        ))
        application.add_handler(MessageHandler(
            filters.PHOTO, 
            handle_photo
        ))
        
        # Register error handler
        application.add_error_handler(error_handler)
        
        # Start bot
        logger.info("🤖 Bot is starting...")
        logger.info(f"✅ Bot @language105translatorbot is now running!")
        logger.info("Press Ctrl+C to stop.")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
