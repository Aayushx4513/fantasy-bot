from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

TOKEN = "8533156744:AAE2Fesm35bggPg47V2UBjJolJnRsJ-pjVA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📢 BOT UPDATES", url="https://t.me/clbotofficial")],
                [InlineKeyboardButton("👥 MAIN GROUP", url="https://t.me/+eTD1m8Cjc_wyOTNl")]]
    await update.message.reply_text("✅ Bot Working!", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
