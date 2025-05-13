from telegram.ext import Application, MessageHandler, filters, CommandHandler

async def reply(update, context):
    await update.message.reply_text("Hello there!")

def main():
    token = "8043165930:AAENESZbRd55O0iFR2IuB-RLkANLGVnyni8"
    application = Application.builder().token(token).concurrent_updates(True).read_timeout(30).write_timeout(30).build()
    application.add_handler(MessageHandler(filters.TEXT, reply))
    application.add_handler(CommandHandler("hello", reply))
    print("Telegram Bot started!", flush=True)
    application.run_polling()


if __name__ == '__main__':
    main()
