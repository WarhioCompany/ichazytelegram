import telebot
import logging
import traceback

from telebot.apihelper import ApiTelegramException


logger = logging.getLogger(__name__)


class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        if isinstance(exception, ApiTelegramException):
            if 'bot was blocked by the user' in exception.description:
                logger.info("Can't send the message, bot was blocked")
                return True
            elif 'Bad Request: chat not found' in exception.description:
                logger.info("Can't send the message, chat not found, probably user has not used the bot yet")
                return True
        logger.error(traceback.format_exc())
        return True
