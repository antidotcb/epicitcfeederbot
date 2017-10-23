import inspect
import logging

import pymongo
from telegram import Bot
from telegram.utils.request import Request
from tweepy import Cursor

from itcuabot.Database import Database


class EpicBot(Bot):
    def __init__(self, token, db, twitter, user_id, stop_callback):
        super(EpicBot, self).__init__(token, request=(Request(con_pool_size=10)))
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.twitter = twitter
        self.user_id = user_id
        self.db = db
        self.latest_id = None
        self.stop_callback = stop_callback

    def reply(self, update, text, *args, **kwargs):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.logger.debug("text: %s", text)
        self.sendMessage(chat_id=update.message.chat.id, text=text, *args, **kwargs)

    def cmd_terminate(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        user = update.message.from_user
        if user and user.username == "antidotcb":
            if callable(self.stop_callback):
                self.logger.info("terminating bot")
                self.reply(update, "Terminating bot. Please restart manually")
                self.stop_callback()
            else:
                self.reply(update, "No callback assigned. Do nothing.")
                self.logger.warn("Callback: %s", self.stop_callback)
        elif user:
            self.reply(update, "You are not authorized to terminate bot.")

    def cmd_start(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        chat = update.message.chat
        if chat.id != -1001096194569:
            self.reply(update, "Only https://t.me/itcuachat is allowed to use this bot for now.")
            return
        self.db.save_chat(chat, self.latest_id)
        self.chats = self.db.chats.find()
        self.reply(update, "You successfully subscribed to news.")

    def cmd_stop(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        chat = update.message.chat
        user = update.message.from_user
        if user and not (user.username == "antidotcb" or user.username == "St_Claus"):
            self.reply(update, "Only administrators can unsubscribe.")
            return
        self.db.remove_chat(chat.id)
        self.chats = self.db.chats.find()
        self.reply(update, "You successfully un-subscribed to news.")

    def cmd_ping(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.reply(update, 'Pong!')

    def cmd_latest(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        timeline = self.twitter.user_timeline(self.user_id, count=1)
        latest = next(iter(timeline), None)
        if latest:
            self.reply(update, latest.text)

    def cmd_today(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def cmd_week(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def cmd_sleep(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def cmd_wakeup(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def cmd_settings(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def cmd_help(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def error_handler(self, update, error):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.logger.error("Error: %s", error)

    def not_implemented(self, update):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.reply(update, "{} is not implemented yet!".format(update.message.text))

    def job_fetch(self, job):
        self.logger.debug("start job: %s", inspect.currentframe().f_code.co_name)

        self.logger.debug("latest id: %s", self.latest_id)

        tweets = Cursor(self.twitter.user_timeline, id=self.user_id, since_id=self.latest_id)

        count = 5 if self.latest_id else 1
        latest_id = None
        for tweet in tweets.items(count):
            latest_id = tweet.id if latest_id < tweet.id else latest_id
            self.db.save_tweet(tweet)

        if latest_id:
            self.logger.info("latest id: %s", latest_id)
            self.latest_id = latest_id

        self.logger.info("tweets after fetch: %s", self.db.tweets.count())

        self.logger.debug("finish job: %s", inspect.currentframe().f_code.co_name)

    def job_send(self, job):
        self.logger.debug("start job: %s", inspect.currentframe().f_code.co_name)

        self.logger.info("chats: %s", self.db.chats.count())
        self.logger.info("tweets before send: %s", self.db.tweets.count())

        tweets = [tweet for tweet in self.db.tweets.find().sort([(Database.id_field, pymongo.ASCENDING)])]
        chats = [chat for chat in self.db.chats.find()]

        class Chat:
            def __init__(self, **entries):
                self.__dict__.update(entries)

        for tweet in tweets:
            tweet_id = tweet["_id"]
            for chat in chats:
                chat["id"] = chat["_id"]
                latest_id = chat["latest_id"]
                send = tweet_id > latest_id if latest_id and latest_id != u'None' else True
                if send:
                    self.sendMessage(chat_id=chat["_id"], text=tweet["text"])
                    self.db.save_chat(Chat(**chat), tweet_id)
            self.db.remove_tweet(tweet_id)

        self.logger.debug("tweets after send: %s", self.db.tweets.count())

        self.logger.debug("finish job: %s", inspect.currentframe().f_code.co_name)
