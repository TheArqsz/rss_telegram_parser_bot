from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, ForeignKey, func, DateTime, Column, Integer, String, UniqueConstraint, join
from os import getcwd
import config
import logging
from datetime import datetime

Base = declarative_base()


class RssFeed(Base):
    __tablename__ = 'rss_feed'

    id =  Column( Integer, primary_key=True)
    rss_url =  Column( String(256), index=True, unique=True)
    content_hash = Column( String(128), index=True)
    content_publish_date = Column( DateTime, index=True)
    feed_title = Column( String(128), index=True)
    user = relationship("UserFeeds")

    def __repr__(self):
        return '<RssFeed {}>'.format(self.rss_url)   

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_tg_code = Column(Integer, nullable=False)

    feed = relationship("UserFeeds")

    __table_args__ = (UniqueConstraint('user_tg_code', name='_user_tg_code_uc'),
                      )

    def to_dict(self):
        return dict(id=self.id,
                    rss_feed=self.feed_id,
                    user=self.user_id)

class UserFeeds(Base):
    __tablename__ = 'user_feeds'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(
        'users.id'), nullable=False)
    feed_id = Column(Integer, ForeignKey(
        'rss_feed.id'), nullable=False)

    def to_dict(self):
        return dict(id=self.id,
                    rss_feed=self.feed_id,
                    user=self.user_id)


class Db:
    def __init__(self):
        if 'sqlite' in config.SQLALCHEMY_DATABASE_URI:
            self.engine = create_engine(config.SQLALCHEMY_DATABASE_URI, connect_args={'check_same_thread': False})
        else:
            self.engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker()
        Session.configure(bind=self.engine) 
        self.session = Session()

    def connect(self):
        self.engine.connect
        Base.metadata.create_all(self.engine)
        logging.info("[DATABASE] Connected to DB")

    def add_user(self, user_code):
        usr = Users(user_tg_code=user_code)
        return self._add_session(usr, msg="Added user")

    def add_feed(self, user_code, rss_feed, content_hash=None, content_publish_date=datetime(1980,1,1,1,0,0), title='Unknown'):
        temp = self.session.query(Users, RssFeed, UserFeeds).filter(Users.id == UserFeeds.user_id).filter(RssFeed.id == UserFeeds.feed_id).all()
        feed = RssFeed(rss_url=rss_feed, content_hash=content_hash, content_publish_date=content_publish_date, feed_title=title)
        for t in temp:
            if t[0].user_tg_code == user_code and t[1].rss_url == rss_feed:
                return
        self._add_session(feed,  msg="Added feed")
        usr_id = self.session.query(Users.id).filter_by(user_tg_code=user_code).first()[0]
        feed_id = self.session.query(RssFeed.id).filter_by(rss_url=rss_feed).first()[0]
        usr_feed = UserFeeds(user_id=usr_id, feed_id=feed_id)
        return self._add_session(usr_feed, msg="Added user's feed")

    def get_rss_feeds(self):
        all_feeds = self.session.query(RssFeed).all()
        l = {}
        for o in all_feeds:
            l[o.rss_url] = {
                'hash': o.content_hash,
                'publish_time': o.content_publish_date,
                'title': o.feed_title
            }
        return l

    def get_top_rss(self):
        top_feeds = self.session.query(RssFeed.rss_url, func.count(UserFeeds.user_id)).filter(RssFeed.id == UserFeeds.feed_id).group_by(RssFeed.rss_url).order_by(func.count(UserFeeds.user_id).desc()).all()
        l = []
        for o in top_feeds:
            l.append(o[0])
        return l[0:3]
    
    def get_count_users(self):
        return self.session.query(func.count(Users.id)).first()

    def get_count_feeds(self):
        return self.session.query(func.count(RssFeed.id)).first()

    def update_rss_feeds(self, rss_url, content_hash, change_rss_url=False, new_rss_url=None, change_publish_date=False, new_publish_date=None, change_title=False, new_title=None):
        o = self.session.query(RssFeed).filter_by(rss_url=rss_url).first()
        self.session.query(RssFeed).filter_by(rss_url=rss_url).update({RssFeed.content_hash:content_hash}, synchronize_session = False)
        if change_rss_url and new_rss_url is not None:
            self.session.query(RssFeed).filter_by(rss_url=rss_url).update({RssFeed.rss_url:new_rss_url}, synchronize_session = False)
        if change_publish_date and new_publish_date is not None:
            self.session.query(RssFeed).filter_by(rss_url=rss_url).update({RssFeed.content_publish_date:new_publish_date}, synchronize_session = False)
        if change_title and new_title is not None:
            self.session.query(RssFeed).filter_by(rss_url=rss_url).update({RssFeed.feed_title:new_title}, synchronize_session = False)
        self.session.commit()

    def get_users_feeds(self):
        all_feeds = self.session.query(Users, RssFeed, UserFeeds).filter(Users.id == UserFeeds.user_id).filter(RssFeed.id == UserFeeds.feed_id).all()
        l = {}
        for o in all_feeds:
            if o[0].user_tg_code in l:
                l[o[0].user_tg_code].add(o[1].rss_url)
            else:
                l[o[0].user_tg_code] = set([o[1].rss_url])
        return l

    def delete_feed(self, user_code, rss_feed):
        usr_id = self.session.query(Users.id).filter_by(user_tg_code=user_code).first()[0]
        feed_id = self.session.query(RssFeed.id).filter_by(rss_url=rss_feed).first()[0]
        
        usr_feed = self.session.query(UserFeeds).filter_by(user_id=usr_id).filter_by(feed_id=feed_id).first()
        return self._del_session(usr_feed, msg="Deleted user's feed")
    
    def _add_session(self, obj, msg=None):
        try:
            self.session.add(obj)
            self.session.commit()
            if msg is None:
                logging.debug("[ADD] Added object to DB")
            else:
                logging.debug(f"[ADD] {msg}")
            return True
        except (Exception, IntegrityError) as e:
            self.session.rollback()
            logging.error(f"[ADD] Error occured {e.orig}")
            return False

    def _commit_session(self, msg=None):
        try:
            self.session.commit()
            if msg is None:
                logging.debug("[DATABASE] Performed successful commit")
            else:
                logging.debug(f"[DATABASE] {msg}")
            return True
        except (Exception, IntegrityError) as e:
            self.session.rollback()
            logging.error(f"[DATABASE] Error occured {e.__dict__}")
            return False
    
    def _del_session(self, obj, msg=None):
        try:
            self.session.delete(obj)
            self.session.commit()
            # self.session.commit()
            if msg is None:
                logging.debug("[DELETE] Deleted object from DB")
            else:
                logging.debug(f"[DELETE] {msg}")
            return True
        except (InvalidRequestError) as e:
            self.session.rollback()
            logging.error(f"[DELETE] Error occured")
            return False