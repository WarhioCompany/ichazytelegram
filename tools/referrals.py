from db_data.db_session import session_scope
from db_data.models import User
from user_sub_checker import is_subscribed, MAIN_CHANNEL_ID


def count_referrals_of_user(telegram_id):
    with session_scope() as session:
        users_invited_by = session.query(User).filter(User.invited_by == telegram_id).all()
        referral_count = sum(1 for user in users_invited_by if is_subscribed(user.telegram_id))
        return referral_count