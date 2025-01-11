from backuper import backuper
from bot import start_bot
from logger.bot_logger import logger_init
logger_init()

bot_token = input('Bot token: ')
if bot_token:
    admin_token = input('Admin token: ')
    backuper.backuper_start()
    start_bot(bot_token, admin_token, 'database/database.sqlite')
else:
    print(f'{"TEST " * 10}\nWarhioTestBot, WarhioDevDebBot')
    start_bot('6098601821:AAHmo_e03absU9-1eFoTwsoJs0GX2_koLPk', '7487435849:AAGZ_3NXNyFvwNXhBFI38idHOXPIjS5M1Vw', 'db/database.sqlite')