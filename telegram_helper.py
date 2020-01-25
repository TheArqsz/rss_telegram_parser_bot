import requests
import config
import logging

TG_BOT_TOKEN = config.RSS_PARSER_BOT_TOKEN
TG_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

def send_message(user_id, msg, parse_mode="Markdown", disable_notification=False):
    params = {
        'chat_id': user_id,
        'text': msg,
        'parse_mode': parse_mode,
        'disable_notification': disable_notification
    }
    return requests.post(TG_URL, data=params)

