from telegram.ext import Updater, CommandHandler
from telegram.error import NetworkError
import rss_parser
import threading, logging
import os

RSS_PARSER_BOT_TOKEN = os.environ.get("RSS_PARSER_BOT_TOKEN", None)

rss = rss_parser.Rss()

def start_parsing(tg_updater):
    thread = threading.Thread(target=rss.loop_rss(tg_updater.bot))
    thread.daemon = True
    thread.start()
    thread.join()

def add_rss(update, context):
    temp_url = update.message.text.replace("/add", '').strip()
    if rss.add_rss(temp_url, update.message.chat_id):
        update.message.reply_markdown(f"Added new [rss feed]({temp_url})")
    elif temp_url is '':
        update.message.reply_markdown(f"*No RSS_URL provided* - use /help")
    else:
        update.message.reply_markdown(f"Wrong rss url `{temp_url}`")

def del_rss(update, context):
    temp_url = update.message.text.replace("/del", '').strip()
    if rss.del_rss(temp_url, update.message.chat_id):
        update.message.reply_markdown(f"Deleted [rss feed]({temp_url})")
    elif temp_url is '':
        update.message.reply_markdown(f"*No RSS_URL provided* - use /help")
    else:
        update.message.reply_markdown(f"Wrong rss url or rss url not saved `{temp_url}`")

def list_rss(update, context):
    l = rss.get_user_rss_list(update.message.chat_id)
    if l is None:
        update.message.reply_markdown("No subscribed feeds")
        return
    message = ""
    for pos,feed in enumerate(l):
        message += f"\t{pos+1}. {feed} \n"
    update.message.reply_markdown(f"""
Your subscribed feeds: 
{message}
""")

def help_commands(update, context):
    commands = f"""
---------------------------\n
\t/add `RSS_URL` - get regular updates for given rss feed \n
\t/del `RSS_URL` - stop getting regular updates for given rss feed \n
\t/list - get your subscribed rss feeds   \n
\t/help - show this message \n
---------------------------
"""
    update.message.reply_markdown(commands)

if __name__ == "__main__":
    if RSS_PARSER_BOT_TOKEN is None:
        print("RSS_PARSER_BOT_TOKEN env var not set")
        exit(1)
    max_time = 30*60
    try:
        updater = Updater(RSS_PARSER_BOT_TOKEN, use_context=True)
        updater.dispatcher.add_handler(CommandHandler('add', add_rss))
        updater.dispatcher.add_handler(CommandHandler('del', del_rss))
        updater.dispatcher.add_handler(CommandHandler('list', list_rss))
        updater.dispatcher.add_handler(CommandHandler('help', help_commands))
        updater.dispatcher.add_handler(CommandHandler('start', help_commands))
        updater.start_polling()
        start_parsing(updater)
    except KeyboardInterrupt:
        exit(0)