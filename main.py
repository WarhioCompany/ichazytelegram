from bot import start_bot
from logger.bot_logger import logger_init
logger_init()

if input('Test? (Enter if no): ') == '':
    start_bot(input('Bot token: '), input('Admin token: '), 'database/database.sqlite')
else:
    print('WarhioTestBot, WarhioDevDebBot')
    start_bot('6098601821:AAHmo_e03absU9-1eFoTwsoJs0GX2_koLPk', '7487435849:AAGZ_3NXNyFvwNXhBFI38idHOXPIjS5M1Vw', 'db/database.sqlite')