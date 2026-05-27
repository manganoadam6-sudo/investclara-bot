import os
import logging
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

user_histories = {} 
SYSTEM_PROMPT = """Tu es l'assistant pédagogique officiel d'Invest avec Adam, spécialisé dans l'éducation financière pour les débutants en Belgique et en France. Tu t'appelles Adam. Tu es patient, rassurant et pédagogique. Tu tutoies l'apprenant chaleureusement. Tu ne promets JAMAIS de gains garantis. Tu encourages toujours une approche prudente et long terme."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_histories[user.id] = []
    keyboard = [
        [InlineKeyboardButton("📈 C'est quoi un ETF ?", callback_data="etf")],
        [InlineKeyboardButton("🏦 Comment ouvrir un compte ?", callback_data="compte")],
        [InlineKeyboardButton("💰 Commencer avec peu d'argent", callback_data="debutant")],
        [InlineKeyboardButton("📊 C'est quoi le DCA ?", callback_data="dca")],
        [InlineKeyboardButton("🇧🇪 Fiscalité Belgique", callback_data="fisc_be"),
         InlineKeyboardButton("🇫🇷 Fiscalité France", callback_data="fisc_fr")],
        [InlineKeyboardButton("₿ Comprendre la crypto", callback_data="crypto")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"👋 Bonjour {user.first_name} ! Je suis l'assistant d'Invest avec Adam.\n\nPose-moi toutes tes questions sur l'investissement !",
        parse_mode="Markdown",
        reply_markup=reply_markup
    ) 
async def get_ai_response(user_id: int, user_message: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "content": user_message})
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=user_histories[user_id]
        )
        assistant_message = response.content[0].text
        user_histories[user_id].append({"role": "assistant", "content": assistant_message})
        return assistant_message
    except Exception as e:
        logger.error(f"Erreur API: {e}")
        return "😅 Petit souci technique, réessaie dans quelques secondes !"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    response = await get_ai_response(user_id, user_message)
    await update.message.reply_text(response, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    questions = {"etf": "Explique-moi simplement ce qu'est un ETF.", "compte": "Comment ouvrir un compte Trade Republic ?", "debutant": "Comment investir avec peu d'argent ?", "dca": "C'est quoi le DCA ?", "fisc_be": "Fiscalité Belgique pour Trade Republic ?", "fisc_fr": "Fiscalité France pour Trade Republic ?", "crypto": "C'est quoi une cryptomonnaie ?"}
    question = questions.get(query.data, "")
    if question:
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action="typing")
        response = await get_ai_response(query.from_user.id, question)
        await query.message.reply_text(response, parse_mode="Markdown")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot démarré !")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
