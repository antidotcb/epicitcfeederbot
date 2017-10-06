import inspect

from telegram.ext import CommandHandler, Updater

from tweepy import API, AppAuthHandler

import itcuabot
import os.path
import json
import logging

from itcuabot.Database import Database


class ConfigError:
    def __init__(self):
        pass


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
        self.polling_id = self.twitter.get_user(polling_id).id

        self._bot = itcuabot.EpicBot(token=telegram_token,
                                     db=self.db,
                                     twitter=self.twitter,
                                     user_id=self.polling_id)

        self.updater = Updater(bot=self._bot)
        self.setup_jobs()
        self.setup_commands()

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
        job_queue.run_repeating(itcuabot.EpicBot.job_fetch, 10)
        job_queue.run_repeating(itcuabot.EpicBot.job_send, 10)

    def run(self):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        self.updater.start_polling(poll_interval=1.0, clean=True)

    def setup_commands(self):
        self.logger.debug(inspect.currentframe().f_code.co_name)

        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(CommandHandler('ping', itcuabot.EpicBot.cmd_ping))
        dispatcher.add_handler(CommandHandler('start', itcuabot.EpicBot.cmd_start))
        dispatcher.add_handler(CommandHandler('stop', itcuabot.EpicBot.cmd_stop))
        dispatcher.add_handler(CommandHandler('latest', itcuabot.EpicBot.cmd_latest))
        dispatcher.add_handler(CommandHandler('sleep', itcuabot.EpicBot.cmd_sleep))
        dispatcher.add_handler(CommandHandler('wakeup', itcuabot.EpicBot.cmd_wakeup))
        dispatcher.add_handler(CommandHandler('today', itcuabot.EpicBot.cmd_today))
        dispatcher.add_handler(CommandHandler('hot', itcuabot.EpicBot.cmd_today))
        dispatcher.add_handler(CommandHandler('week', itcuabot.EpicBot.cmd_week))
        dispatcher.add_handler(CommandHandler('settings', itcuabot.EpicBot.cmd_settings))
        dispatcher.add_handler(CommandHandler('help', itcuabot.EpicBot.cmd_help))
        dispatcher.add_error_handler(itcuabot.EpicBot.error_handler)


if __name__ == '__main__':
    app = App()
    app.run()
