import time, hashlib, feedparser, logging, os
from datetime import datetime, timezone
import database
from dateutil import parser

class Rss:
    def __init__(self):
        self.db = database.Db()
        self.db.connect()
        self.rss_feeds = {}
        self.rss_users = {}
        self._update_rss_feeds()
        self._update_rss_users()
        self.lookup_window = int(os.environ.get("RSS_LOOKUP_WINDOW", 30)) # in sec

    def _update_rss_feeds(self):
        self.rss_feeds = self.db.get_rss_feeds()

    def _update_rss_users(self):
        self.rss_users = self.db.get_users_feeds()
        
    def get_user_rss_list(self, user_id):
        if user_id in self.rss_users:
            return list(self.rss_users[user_id])
        else:
            return None

    def get_top_rss(self):
        return self.db.get_top_rss()

    def add_rss(self, rss_url, user_id):
        rss_feed = feedparser.parse(rss_url)
        if "bozo_exception" in rss_feed:
            return False
        else:
            first_hash = hashlib.md5((rss_feed.entries[0].link + rss_feed.entries[0].title).encode()).hexdigest()
            if user_id in self.rss_users:
                self.db.add_feed(user_id, rss_url, first_hash)
            else:
                self.db.add_user(user_id)
                self.db.add_feed(user_id, rss_url, first_hash)
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

    def loop_rss(self, tg_bot):
        while 1:
            try:
                for user_id in self.rss_users:
                    for rss_url in self.rss_users[user_id]:
                        rss_feed = feedparser.parse(rss_url)
                        current_hash = hashlib.md5((rss_feed.entries[0].link + rss_feed.entries[0].title).encode()).hexdigest()
                        if current_hash == self.rss_feeds[rss_url]:
                            continue
                        else:
                            self.db.update_rss_feeds(rss_url, current_hash)
                            self._update_rss_feeds()
                            safe_markdown_title = rss_feed.entries[0].title.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\`")
                            safe_markdown_url = rss_feed.entries[0].links[0].href.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\`")
                            safe_feed_title = rss_feed.feed.title.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\`")
                            local_post_time = utc_to_local(parser.parse(rss_feed.entries[0].published)).strftime(" %m/%d/%Y %H:%M:%S")
                            msg = f"""
-------------------------------------
*{safe_markdown_title}*

FROM: *{safe_feed_title}*

URL: {safe_markdown_url}

POSTED AT: `{local_post_time}`
-------------------------------------
"""
                            resp = tg_bot.send_message(user_id, msg, parse_mode='Markdown', disable_notification=True)
                            logging.debug("[RSS_PARSER] Successufully sent update")
            except (Exception) as e:
                logging.error(e)
                continue
            time.sleep(self.lookup_window)
        
def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)