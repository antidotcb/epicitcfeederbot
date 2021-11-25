#!/usr/bin/python3.8
import inspect
import os.path
import json
import logging
from threading import Thread

from telegram.ext import CommandHandler, Updater
from tweepy import API, AppAuthHandler

from itcuabot.Database import Database
from itcuabot.EpicBot import EpicBot


class ConfigError:
    def __init__(self):
        pass


class AppTerminator:
    def __init__(self, app):
        self.app = app

    def __call__(self, *args, **kwargs):
        thread = Thread(target=App.close, args=(app,))
        thread.start()


class App:
    config_file = 'config.json'
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    def __init__(self):
        logging.basicConfig(format=App.log_format, level=logging.INFO)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self._options = self.load_options()

        options_telegram = self._options['telegram']
        options_twitter = self._options['twitter']
        options_mongodb = self._options['mongodb']

        telegram_token = options_telegram['token']
        twitter_auth = options_twitter['auth']
        polling_id = options_twitter['polling_id']

        self.db = Database(**options_mongodb)

        self.twitter = API(AppAuthHandler(**twitter_auth))
        print("polling id: %s" % str(polling_id))
        self.polling_id = self.twitter.get_user(screen_name=polling_id).id

        terminator = AppTerminator(self)
        bot = EpicBot(token=telegram_token,
                      db=self.db,
                      twitter=self.twitter,
                      user_id=self.polling_id,
                      stop_callback=terminator)

        self.updater = Updater(bot=bot)
        self.setup_jobs()
        self.setup_commands()
        bot.updater = self.updater

    def load_options(self):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        if not os.path.isfile(App.config_file):
            logging.error('Cannot find "{}" file.', App.config_file)
            raise ConfigError
        with open(App.config_file) as f:
            content = f.read()
        return json.loads(content)

    def setup_jobs(self):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        job_queue = self.updater.job_queue
        job_queue.run_repeating(EpicBot.job_fetch, 71)
        job_queue.run_repeating(EpicBot.job_send, 17)

    def run(self):
        self.logger.info("start %s", inspect.currentframe().f_code.co_name)
        self.logger.debug(inspect.currentframe().f_code.co_name)
        self.updater.start_polling(poll_interval=1.0, clean=True)
        self.logger.info("stop %s", inspect.currentframe().f_code.co_name)

    def setup_commands(self):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(CommandHandler('ping', EpicBot.cmd_ping))
        dispatcher.add_handler(CommandHandler('start', EpicBot.cmd_start))
        dispatcher.add_handler(CommandHandler('stop', EpicBot.cmd_stop))
        dispatcher.add_handler(CommandHandler('latest', EpicBot.cmd_latest))
        dispatcher.add_handler(CommandHandler('sleep', EpicBot.cmd_sleep))
        dispatcher.add_handler(CommandHandler('wakeup', EpicBot.cmd_wakeup))
        dispatcher.add_handler(CommandHandler('today', EpicBot.cmd_today))
        dispatcher.add_handler(CommandHandler('hot', EpicBot.cmd_today))
        dispatcher.add_handler(CommandHandler('week', EpicBot.cmd_week))
        dispatcher.add_handler(CommandHandler('settings', EpicBot.cmd_settings))
        dispatcher.add_handler(CommandHandler('help', EpicBot.cmd_help))
        dispatcher.add_handler(CommandHandler('terminate', EpicBot.cmd_terminate))

        dispatcher.add_error_handler(EpicBot.error_handler)

    def close(self):
        self.logger.debug(inspect.currentframe().f_code.co_name)
        self.logger.info("full stop")
        self.updater.stop()


if __name__ == '__main__':
    app = App()
    app.run()
