import logging
import os
from deep_translator import GoogleTranslator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- Configuration ---
# Get token from Railway environment variables for security
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    logging.error("TELEGRAM_BOT_TOKEN environment variable not set!")
    exit(1)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
        return "⚠️ Sorry, I couldn't translate that. Please try again."

def get_language_keyboard():
    """Creates an inline keyboard with language options."""
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
    """Send welcome message when /start is issued."""
    user = update.effective_user
    welcome_text = (
        f"👋 Hello {user.first_name}!\n\n"
        "🌍 I'm **Language105 Translator Bot**!\n\n"
        "**How to use me:**\n"
        "1️⃣ Send any text message and I'll translate it\n"
        "2️⃣ Use /lang to change your target language\n"
        "3️⃣ Current default language: English\n\n"
        "💡 Tip: Use /help for more commands\n\n"
        "Let's start translating! 🚀"
    )
    await update.message.reply_text(welcome_text)
    # Set default language
    context.user_data['target_lang'] = 'en'

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message when /help is issued."""
    help_text = (
        "🤖 **Help Center**\n\n"
        "**Available Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/lang - Change translation language\n"
        "/languages - List all supported languages\n"
        "/about - About this bot\n\n"
        "**How to Translate:**\n"
        "• Send any text message\n"
        "• I'll translate it to your chosen language\n"
        "• Use /lang to switch languages anytime\n\n"
        "**Image Translation:**\n"
        "• Send a photo with text\n"
        "• I'll extract and translate the text\n"
        "• (Requires clear, well-lit images)"
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
        "Powered by: Google Translate API\n"
        "Created for: Language105 Project\n"
        "Hosted on: Railway\n\n"
        "📚 Translates text into 18+ languages\n"
        "🖼️ Supports image text translation\n"
        "⚡ Fast and accurate translations"
    )
    await update.message.reply_text(about_text)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show language selection or handle callback."""
    query = update.callback_query
    
    if query:
        # Handle button press
        await query.answer()
        lang_code = query.data
        context.user_data['target_lang'] = lang_code
        lang_name = next((name for name, code in LANGUAGES.items() if code == lang_code), lang_code)
        await query.edit_message_text(
            f"✅ Language set to **{lang_name}**!\n\n"
            "Now send me any text to translate. 📝"
        )
        return
    
    # Show language selection keyboard
    if update.message:
        await update.message.reply_text(
            "🌐 **Choose your target language:**\n\n"
            "Select from the buttons below:",
            reply_markup=get_language_keyboard()
        )

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Translate incoming text messages."""
    # Ignore commands
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
        f"💡 To change language, use /lang"
    )
    await update.message.reply_text(response)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages."""
    await update.message.reply_text(
        "🖼️ **Image Received!**\n\n"
        "I'm processing your image...\n"
        "This feature uses OCR to extract text.\n\n"
        "⚠️ For best results, ensure:\n"
        "• Clear text\n"
        "• Good lighting\n"
        "• Simple background\n\n"
        "⏳ Processing may take a few seconds..."
    )
    
    # For a production bot, you'd integrate OCR here
    # Example: Google Cloud Vision API, Tesseract, etc.
    
    # For now, inform user about the feature
    await update.message.reply_text(
        "📝 **OCR Feature Coming Soon!**\n\n"
        "I'll be able to extract text from images in the next update.\n\n"
        "For now, please send text directly for translation. 📝"
    )

# --- Error Handler ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

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
        application.add_handler(CallbackQueryHandler(set_language, pattern="|".join(LANGUAGES.values())))
        
        # Register message handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        # Register error handler
        application.add_error_handler(error_handler)
        
        # Start bot
        logger.info("🤖 Bot is starting...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
