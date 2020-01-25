import time, hashlib, feedparser, logging, os
from datetime import datetime, timezone
import database
from dateutil import parser as dateparser
import config
from telegram_helper import send_message

class Rss:
    def __init__(self):
        self.db = database.Db()
        self.db.connect()
        self.rss_feeds = {}
        self.rss_users = {}
        self._update_rss_feeds()
        self._update_rss_users()
        self.lookup_window = int(os.environ.get("RSS_LOOKUP_WINDOW", 60)) # in sec

    def _update_rss_feeds(self):
        self.rss_feeds = self.db.get_rss_feeds()

    def _update_rss_users(self):
        self.rss_users = self.db.get_users_feeds()

    def get_user_rss_list(self, user_id):
        if user_id in self.rss_users:
            return list(self.rss_users[user_id])
        else:
            return None

    def get_all_rss_list(self, amount=3):
        urls = list(self.rss_feeds.keys())[0:amount]
        tmp = {}
        for feed in list(self.rss_feeds.keys())[0:amount]:
            tmp[feed] = self.rss_feeds[feed]['title']
        return tmp

    def get_top_rss(self):
        return self.db.get_top_rss()

    def add_rss(self, rss_url, user_id):
        rss_feed = feedparser.parse(rss_url)
        if len(rss_feed.entries) == 0:
            return False
        else:
            first_hash = hashlib.md5((rss_feed.entries[0].link + rss_feed.entries[0].title).encode()).hexdigest()
            if user_id in self.rss_users:
                self.db.add_feed(user_id, rss_url, first_hash, title=rss_feed.feed.get('title', 'Unknown'))
            else:
                self.db.add_user(user_id)
                self.db.add_feed(user_id, rss_url, first_hash, title=rss_feed.feed.get('title', 'Unknown'))
            self._update_rss_feeds()
            self._update_rss_users()
            return True

    def del_rss(self, rss_url, user_id):
        self._update_rss_feeds()
        self._update_rss_users()
        if rss_url in self.rss_feeds:
            if user_id not in self.rss_users:
                return True
            if rss_url in self.rss_users[user_id]:
                self.db.delete_feed(user_id, rss_url)
                self._update_rss_feeds()
                self._update_rss_users()
                return True
        return False

    def get_users_count(self):
        return self.db.get_count_users()

    def get_feeds_count(self):
        return self.db.get_count_feeds()

    def loop_rss(self, tg_bot):
        while 1:
            try:
                logging.info(f"[PARSER] {self.rss_feeds}")
                for rss_url in self.rss_feeds:
                    rss_feed = feedparser.parse(rss_url)
                    if rss_feed is None:
                        continue
                    _all_entries = rss_feed.entries
                    sort_feed_dict(_all_entries)
                    _newest_entry = _all_entries[0]
                    _tmp_date_parsed = _newest_entry.get('published_parsed') or rss_feed.feed.get('updated_parsed') # published_parsed is not always available
                    _publish_time_as_datetime = datetime(*_tmp_date_parsed[:6])
                    _current_hash = hashlib.md5((_newest_entry.link + _newest_entry.title).encode()).hexdigest()
                    if _current_hash == self.rss_feeds[rss_url]['hash']:
                        logging.info(f"[PARSER] NOT PROCESSING {self.rss_feeds[rss_url]}: Publish time - {_publish_time_as_datetime}; Saved time: {self.rss_feeds[rss_url]['publish_time']}")
                        continue
                    elif _publish_time_as_datetime <= self.rss_feeds[rss_url]['publish_time']: # Protects from duplicates recieved from Telegram
                        logging.info(f"[PARSER] NOT PROCESSING {self.rss_feeds[rss_url]}: Publish time - {_publish_time_as_datetime}; Saved time: {self.rss_feeds[rss_url]['publish_time']}")
                        continue
                    else:
                        logging.info(f"[PARSER] PROCESSING Statement for {self.rss_feeds[rss_url]}: Publish time - {_publish_time_as_datetime}; Saved time: {self.rss_feeds[rss_url]['publish_time']}")
                        self.db.update_rss_feeds(rss_url, _current_hash, change_publish_date=True, new_publish_date=_publish_time_as_datetime)
                        self._update_rss_feeds()
                        _safe_markdown_title = _safe_markdown_parser(_newest_entry.title)
                        _safe_markdown_url = _safe_markdown_parser(_newest_entry.link)
                        _safe_feed_title = _safe_markdown_parser(self.rss_feeds[rss_url]['title'])
                        _update_time = dateparser.parse(_all_entries[0].updated).strftime(" %m/%d/%Y %H:%M:%S %Z ")
                        msg = f"""
-------------------------------------
*{_safe_markdown_title}*

FROM: `{_safe_feed_title}`

URL: {_safe_markdown_url}

POSTED AT: `{_update_time}`
-------------------------------------
"""
                        for user_id in self.rss_users:
                            if rss_url in self.rss_users[user_id]:
                                resp = send_message(user_id, msg, parse_mode='Markdown', disable_notification=True)
                                logging.info(f"[RSS_PARSER] Successufully sent update for {rss_url}")
            except (Exception) as e:
                logging.error(f"[PARSER] {e}")
                continue
            time.sleep(self.lookup_window)

def _utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

def _safe_markdown_parser(sample):
    return sample.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\'").replace("&quot;", '"')

def simple_parse(url):
        f = feedparser.parse(url)
        if len(f.entries) == 0:
            return {
                'feed': {
                    'title' : 'Unknown'
                }
            }
        else:
            return f

def sort_feed_dict(entries):
    if entries[0].get('updated_parsed') is None:
        return
    else:
        size = len(entries)
        for i in range(size):
        	min_index = i
        	for j in range(i + 1, size):
        		if datetime(*entries[min_index]["updated_parsed"][:6]) < datetime(*entries[j]["updated_parsed"][:6]):
        			min_index = j
        	temp = entries[i]
        	entries[i] = entries[min_index]
        	entries[min_index] = temp
