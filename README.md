# Telegram rss parser bot

[![Python](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-blue?style=flat&logo=appveyor)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-brightgreen?style=flat&logo=appveyor)](https://choosealicense.com/licenses/mit/)
<br>

Simple telegram bot that parses given rss feeds and gives you regular updates if new posts appear

## Prerequisites

Before you can use it you need to have:
* Telegram account

## Usage 

You can find the bot at [this url](https://t.me/rssparser_bot)

### Available commands

* `/add RSS_URL` - allows you to subscribe a rss feed of your wish
* `/del RSS_URL` - allows you to unsubscribe a rss feed
* `/list` - lists your subscribed rss feeds
* `/listall AMOUNT` - lists all rss feeds (default AMOUNT is 3)
* `/top` - lists top rss feeds
* `/info` - shows information about the bot
* `/help` - shows available commands

## Maintainers

* [Arqsz](https://github.com/TheArqsz)

## Example results
![Telegram view](telegram_view.png)

## Used libraries

* [requests](https://2.python-requests.org/en/master/)
* [python-telegram-bot](https://python-telegram-bot.org/)
* [sqlalchemy](https://www.sqlalchemy.org/)
* [feedparser](https://pythonhosted.org/feedparser/)
* [dateutil](https://dateutil.readthedocs.io/en/stable/)
