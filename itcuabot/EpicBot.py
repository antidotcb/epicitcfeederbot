import inspect
import logging
from telegram import Bot
from telegram.utils.request import Request
from tweepy import Cursor


class EpicBot(Bot):
    def __init__(self, token, db, twitter, user_id):
        super(EpicBot, self).__init__(token, request=(Request(con_pool_size=10)))
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(inspect.currentframe().f_code.co_name)

        self.twitter = twitter
        self.user_id = user_id
        self.db = db
        self.since_id = None

    def reply(self, update, text, *args, **kwargs):
        self.logger.info(inspect.currentframe().f_code.co_name)

        self.logger.info("text: %s", text)
        self.sendMessage(chat_id=update.message.chat.id, text=text, *args, **kwargs)

    def cmd_start(self, update):
        self.logger.info(inspect.currentframe().f_code.co_name)

        chat = update.message.chat
        self.db.save_chat(chat, self.since_id)
        self.chats = self.db.chats.find()
        self.reply(update, "You successfully subscribed to news.")

    def cmd_stop(self, update):
        self.logger.info(inspect.currentframe().f_code.co_name)

        chat = update.chat
        self.db.remove_chat(chat.id)
        self.chats = self.db.chats.find()
        self.reply(update, "You successfully un-subscribed to news.")

    def cmd_ping(self, update):
        self.logger.info(inspect.currentframe().f_code.co_name)

        self.reply(update, 'Pong!')

    def cmd_latest(self, update):
        self.logger.info(inspect.currentframe().f_code.co_name)

        timeline = self.twitter.user_timeline(self.user_id, count=1)
        latest = next(iter(timeline), None)
        if latest:
            self.reply(update, latest.text)

    def cmd_today(self, update):
        self.logger.info(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def cmd_week(self, update):
        self.logger.info(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def cmd_sleep(self, update):
        self.logger.info(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def cmd_wakeup(self, update):
        self.logger.info(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def cmd_settings(self, update):
        self.logger.info(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def cmd_help(self, update):
        self.logger.info(inspect.currentframe().f_code.co_name)

        self.not_implemented(update)

    def error_handler(self, update, error):
        self.logger.info(inspect.currentframe().f_code.co_name)

        self.logger.error("Error: %s", error)

    def not_implemented(self, update):
        self.logger.info(inspect.currentframe().f_code.co_name)

        self.reply(update, "{} is not implemented yet!".format(update.message.text))

    def job_fetch(self, job):
        self.logger.info("start job: %s", inspect.currentframe().f_code.co_name)
        if self.since_id:
            tweets = Cursor(self.twitter.user_timeline, id=self.user_id, since_id=self.since_id)
        else:
            tweets = Cursor(self.twitter.user_timeline, id=self.user_id, count=1)

        latest_id = None
        for tweet in tweets.items():
            latest_id = tweet.id if not latest_id else latest_id
            self.db.save_tweet(tweet)

        if latest_id:
            self.logger.info("latest id: %s", latest_id)
            self.since_id = latest_id

        self.logger.info("tweets: %s", self.db.tweets.count())
        self.logger.info("finish job: %s", inspect.currentframe().f_code.co_name)

    def job_send(self, job):
        self.logger.info("start job: %s", inspect.currentframe().f_code.co_name)
        self.logger.info("chats: %s", self.db.chats.count())

        tweets = [tweet for tweet in self.db.tweets.find()]
        chats = [chat for chat in self.db.chats.find()]

        for tweet in tweets:
            tweet_id = tweet["_id"]
            for chat in chats:
                since_id = chat["since_id"]
                if since_id > tweet_id:
                    print "send!"
                    self.sendMessage(chat_id=chat["_id"], text=tweet["text"])
            self.db.remove_tweet(tweet_id)

        self.logger.info("tweets: %s", self.db.tweets.count())
        self.logger.info("finish job: %s", inspect.currentframe().f_code.co_name)
