import inspect
import logging
from datetime import datetime

import pymongo
from pymongo import MongoClient


class Database(object):
    id_field = "_id"

    def __init__(self, host, port, username, password, db, tweets="tweets", chats="chats"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(inspect.currentframe().f_code.co_name)

        uri = self.uri(username, password, host, port, db)
        self.logger.debug("mongodb uri: %s", uri)

        client = MongoClient(uri)
        self.setup(client, db, tweets, chats)
        db = client[db]
        self.tweets = db.get_collection(tweets)
        self.chats = db.get_collection(chats)

    @staticmethod
    def tweet_document(tweet):
        return {
            Database.id_field: str(tweet.id),
            "text": tweet.text,
            "created_at": tweet.created_at
        }

    @staticmethod
    def chat_document(chat, latest_id):
        return {
            Database.id_field: str(chat.id),
            "title": chat.title,
            "subscribed": datetime.now(),
            "latest_id": str(latest_id)
        }

    def save_chat(self, chat, latest_id):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.logger.debug("chat: %s", chat)
        chat_id_str = str(chat.id)
        document = self.chat_document(chat, latest_id)
        filter = {Database.id_field: chat_id_str}
        result = self.chats.update_one(filter=filter, update={"$set": document}, upsert=True)
        self.logger.debug("update_one result: %s", str(result))

    def remove_chat(self, chat_id):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        chat_id_str = str(chat_id)
        self.logger.debug("chat id: %s", chat_id_str)
        result = self.chats.remove({Database.id_field: chat_id_str})
        self.logger.debug("remove result: %s", str(result))

    def save_tweet(self, tweet):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.logger.debug("tweet: %s", tweet)
        document = self.tweet_document(tweet)
        tweet_id = str(tweet.id)
        filter = {Database.id_field: tweet_id}
        result = self.tweets.update_one(filter=filter, update={"$set": document}, upsert=True)
        self.logger.debug("update_one result: %s", str(result))

    def remove_tweet(self, tweet_id):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        tweet_id_str = str(tweet_id)
        self.logger.debug("tweet id: %s", tweet_id_str)
        result = self.tweets.remove({Database.id_field: tweet_id_str})
        self.logger.debug("remove result: %s", str(result))

    def setup(self, client, db_name, tweets_name, chats_name):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        exist = db_name in client.database_names()
        if exist:
            self.logger.warn("drop existing database")
            client.drop_database(db_name)
            # return TODO: remove previous line, uncomment this in production
        db = client.get_database(db_name)
        statuses = db.get_collection(tweets_name)
        statuses.create_index([("created_at", pymongo.DESCENDING)], name="oldest", unique=True)
        db.get_collection(chats_name)
        return db

    def uri(self, user, pwd, host, port, db):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        try:
            from urllib.parse import quote_plus
        except ImportError:
            from urllib import quote_plus

        uri_mask = "mongodb://{user}{split1}{password}{at}{host}{split2}{port}{split3}{database}"
        uri = uri_mask.format(
            user=quote_plus(user) if user else "",
            split1=":" if pwd and user else "",
            password=quote_plus(pwd) if user else "",
            at="@" if user else "",
            host=host,
            split2=":" if port else "",
            port=port,
            split3="/" if db else "",
            database=db
        )
        return uri
