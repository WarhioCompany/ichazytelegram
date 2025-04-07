from db_data.db_session import session_scope, global_init
from db_data.models import Promocode, Brand

global_init('db/database.sqlite')
with session_scope() as session:
    promocode = Promocode(
        brand = Brand(),
        promo='promocode',
        coins=100,
        need_confirmation=True,
        telegram_contact='@durov'
    )
    session.add(promocode)
    session.commit()