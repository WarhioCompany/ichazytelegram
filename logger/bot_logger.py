import logging
import sys
from db_data.db_session import session_scope

logger = logging.getLogger(__name__)


def logger_init():
    handlers = [logging.StreamHandler(sys.stdout),
                logging.FileHandler('log.log', encoding='utf-8')]
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', handlers=handlers)


def log_message_sent(message):

    # might not be the best idea to get username each time message is sent

    logger.info(f'{message.from_user.id} sent {message.text}')


def log_user_callback(call):
    logger.info(f'{call.from_user.id} clicked {call.data}')


def log_user_activity(user_id, log_message):
    logger.info(f'{user_id} {log_message}')


def warning_user_activity(user_id, warning_message):
    logger.warning(f'{user_id} {warning_message}')


def warning(warning_message):
    logger.warning(warning_message)


def debug_log(msg):
    logger.info(msg)