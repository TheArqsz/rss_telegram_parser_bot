import time, hashlib, feedparser, logging, os
from datetime import datetime, timezone
import database
from dateutil import parser as dateparser
import config

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

    def get_top_rss(self):
        return self.db.get_top_rss()

    def add_rss(self, rss_url, user_id):
        rss_feed = feedparser.parse(rss_url)
        if len(rss_feed.entries) == 0:
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

    def get_users_count(self):
        return self.db.get_count_users()

    def get_feeds_count(self):
        return self.db.get_count_feeds()

    def loop_rss(self, tg_bot):
        while 1:
            try:
                for user_id in self.rss_users:
                    for rss_url in self.rss_users[user_id]:
                        rss_feed = feedparser.parse(rss_url)
                        _newest_entry = rss_feed.entries[0]# newest_entry(rss_feed)
                        current_hash = hashlib.md5((_newest_entry.link + _newest_entry.title).encode()).hexdigest()
                        if current_hash == self.rss_feeds[rss_url]:
                            continue
                        else:
                            self.db.update_rss_feeds(rss_url, current_hash)
                            self._update_rss_feeds()
                            safe_markdown_title = _newest_entry.title.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\`")
                            safe_markdown_url = _newest_entry.links[0].href.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\`")
                            safe_feed_title = rss_feed.feed.title.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\`")
                            local_post_time = dateparser.parse(rss_feed.entries[0].updated).strftime(" %m/%d/%Y %H:%M:%S")
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
        
def _utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

# def newest_entry(feed):
#     from datetime import datetime
#     entries = feed.entries
#     newest_entry_date = datetime(1971, 1, 1).replace(tzinfo=timezone.utc)
#     newest_entry = 0
#     for i, e in enumerate(entries):
#         entry_date = dateparser.parse(e.updated).replace(tzinfo=timezone.utc)
#         if entry_date > newest_entry_date:
#             newest_entry_date = entry_date
#             newest_entry = i
#             print(i)
#     return entries[newest_entry]