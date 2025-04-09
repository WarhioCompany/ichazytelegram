from db_data.db_session import session_scope, global_init
from db_data.models import Promocode, Brand, BoostPromocode

global_init('db/database.sqlite')
with session_scope() as session:
    boost_promocode = BoostPromocode(
        promo='boost',
        promocode_type='count',
        coefficient=2,
        absolute_value=1,
        need_confirmation=False,
        is_expired=False
    )
    session.add(boost_promocode)
    session.commit()