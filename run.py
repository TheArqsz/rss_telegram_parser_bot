from telegram.ext import Updater, CommandHandler
from telegram.error import NetworkError
import parser
import threading, logging
import os
import config
from humanfriendly import format_timespan

RSS_PARSER_BOT_TOKEN = os.environ.get("RSS_PARSER_BOT_TOKEN", None)

rss = parser.Rss()

def start_parsing(tg_updater):
    thread = threading.Thread(target=rss.loop_rss(tg_updater.bot))
    thread.daemon = True
    thread.start()
    thread.join()

def add_rss(update, context):
    if update.message is None:
        logging.error(f"Message is none for {update.__dict__}")
        return
    temp_url = update.message.text.split("/add")[1].strip()
    if rss.add_rss(temp_url, update.message.chat_id):
        update.message.reply_markdown(f"Subscribed to a new [rss feed]({temp_url})")
        return
    elif temp_url is '':
        update.message.reply_markdown(f"*No RSS_URL provided* - use /help")
        return
    else:
        update.message.reply_markdown(f"Wrong rss url `{parser._safe_markdown_parser(temp_url)}`")
        return

def get_info(update, context):
    msg = f"""
-------------------------------------
Total feeds: `{rss.get_feeds_count()[0]}` 
Total users: `{rss.get_users_count()[0]}` 
RSS refresh time: `{format_timespan(rss.lookup_window)}`
Maintainer: {config.MAINTAINER}
-------------------------------------
"""
    update.message.reply_markdown(msg)

def del_rss(update, context):
    if update.message is None:
        logging.error(update.message.__dict__)
        return
    temp_url = update.message.text.split("/del")[1].strip()
    if rss.del_rss(temp_url, update.message.chat_id):
        update.message.reply_markdown(f"Unsubscribed from [rss feed]({temp_url})")
        return
    elif temp_url is '':
        update.message.reply_markdown(f"*No RSS_URL provided* - use /help")
        return
    else:
        update.message.reply_markdown(f"Wrong rss url or rss url not saved `{temp_url}`")
        return

def list_rss(update, context):
    if update.message is None:
        logging.error(f"Message is none for {update.__dict__}")
        return
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

def listall_rss(update, context):
    if update.message is None:
        logging.error(f"Message is none for {update.__dict__}")
        return
    MAX = 20
    l = None
    _temp = update.message.text.split("/listall")[1].strip()
    if _temp == '':
        l = rss.get_all_rss_list()
    else:
        try:
            amount = int(_temp)
            if amount > MAX or amount < 1:
                raise ValueError
            l = rss.get_all_rss_list(amount=amount)
        except ValueError:
            update.message.reply_markdown(f"`{parser._safe_markdown_parser(_temp)}` is not a valid positive number or number higher than `{MAX}`")    
            return
    if l is None:
        update.message.reply_markdown("No feeds in DB")
        return
    message = ""
    for pos,url in enumerate(l):
        message += f"\t{pos+1}. `{parser.simple_parse(url)['feed']['title']}`: {parser._safe_markdown_parser(url)} \n"
    update.message.reply_markdown(f"""
Feeds in DB (showing `{len(l)}`): 
{message}
""")

def help_commands(update, context):
    if update.message is None:
        logging.error(f"Message is none for {update.__dict__}")
        return
    commands = f"""
---------------------------\n
\t/add `RSS_URL` - get regular updates for given rss feed \n
\t/del `RSS_URL` - stop getting regular updates for given rss feed \n
\t/list - get your subscribed rss feeds   \n
\t/listall `AMOUNT` - show `AMOUNT` of feeds from database (default: 3)   \n
\t/top - get list of the most popular rss feeds   \n
\t/info - get information about bot   \n
\t/help - show this message \n
---------------------------
"""
    update.message.reply_markdown(commands)

def top_rss(update, context):
    if update.message is None:
        logging.error(f"Message is none for {update.__dict__}")
        return
    l = rss.get_top_rss()
    if l is None:
        update.message.reply_markdown("No feeds in DB")
        return
    message = ""
    for pos,feed in enumerate(l):
        message += f"\t{pos+1}. {feed} \n"
    update.message.reply_markdown( f"""
Top RSS feeds: 
{message}
""")

if __name__ == "__main__":
    if RSS_PARSER_BOT_TOKEN is None:
        print("RSS_PARSER_BOT_TOKEN env var not set")
        exit(1)
    max_time = 30*60
    try:
        updater = Updater(RSS_PARSER_BOT_TOKEN, use_context=True)
        if not config.DEBUG:
            updater.dispatcher.add_handler(CommandHandler('add', add_rss))
            updater.dispatcher.add_handler(CommandHandler('del', del_rss))
            updater.dispatcher.add_handler(CommandHandler('list', list_rss))
            updater.dispatcher.add_handler(CommandHandler('help', help_commands))
            updater.dispatcher.add_handler(CommandHandler('start', help_commands))
            updater.dispatcher.add_handler(CommandHandler('top', top_rss))
            updater.dispatcher.add_handler(CommandHandler('info', get_info))
            updater.dispatcher.add_handler(CommandHandler('listall', listall_rss))
        updater.start_polling()
        start_parsing(updater)
    except KeyboardInterrupt:
        exit(0)