import event_handler
import user_sub_checker
from db_data.db_session import session_scope
from db_data.models import Prize, Challenge, User
from messages_handler import messages
from timer import Timer

# когда юзер будет смотреть статус барьеров призов, то проверять все барьеры заново может быть оч долго, поэтому возможно нужна меморизация, но тогда юзер, подписавшись на канал, не увидит актуальное значание барьера



timer = None
__admin_notifier = None
def start(admin_notifier):
    global timer, __admin_notifier
    if timer:
        raise Exception('prize barrier checker has already been started')
    timer = Timer(prize_barriers_check, event_handler.hour())
    __admin_notifier = admin_notifier



def get_prizes_with_barrier():
    with session_scope() as session:
        return session.query(Prize).filter(Prize.barrier_type.isnot(None)).all()

# check is performed each hour
def prize_barriers_check():
    prizes_with_active_barrier = get_prizes_with_barrier()
    for prize in prizes_with_active_barrier:
        if prize.barrier_value <= get_prize_barrier_value(prize):
            __admin_notifier.prize_barrier_suffice(prize)


def get_barrier_type_text(barrier_type):
    match barrier_type:
        case 'referrals':
            return 'Количество приглашенных друзей'
        case 'subscribers':
            return 'Челлендж выйдет, когда подписчиков на [Чейзи](https://t.me/ChazyChannel) будет {barrier_value}'
        case 'promocodes':
            return 'Количество активированных промокодов'


def send_prize_barrier_message(bot, chat_id):
    bot.send_message(chat_id, get_prize_barrier_text(), parse_mode='MarkdownV2', disable_web_page_preview=True)


def send_actual_prizes_message(bot, chat_id):
    bot.send_message(chat_id, get_actual_prize_text())


def get_prize_barrier_text():
    prizes_with_active_barrier = get_prizes_with_barrier()
    lines = []
    for num, prize in enumerate(prizes_with_active_barrier, start=1):
        cur_barrier_value = get_prize_barrier_value(prize)
        lines.append(messages['future_prize_line'].format(
            num=num,
            name=prize.name,
            current_barrier_value=cur_barrier_value,
            barrier_value=prize.barrier_value,
            type_explanation=get_barrier_type_text(prize.barrier_type).format(
                current_barrier_value=cur_barrier_value,
                barrier_value=prize.barrier_value,
            )
        ))
    if not lines:
        return messages['no_future_prizes']

    return '\n'.join(lines)


def get_actual_prize_text():
    lines = []
    with session_scope() as session:
        hard_challenges = session.query(Challenge).filter(Challenge.is_hard).all()
        for num, challenge in enumerate(hard_challenges, start=1):
            if not challenge.prizes: continue
            lines.append(messages['actual_prize_line'].format(
                num=num,
                name=challenge.prizes[0].name,
                desc=challenge.prizes[0].description,
                challenge=challenge.name
            ))
    if not lines:
        return messages['no_actual_prizes']

    return '\n'.join(lines)



def get_prize_barrier_value(prize):
    match prize.barrier_type:
        case 'promocodes':
            return get_number_of_promocodes_associated_with_prize(prize)
        case 'subscribers':
            return get_number_of_subscribers()
        case 'referrals':
            return get_number_of_referrals()
    raise Exception(f'unknown barrier type: {prize.barrier_type}')


def get_number_of_promocodes_associated_with_prize(prize): # prize -> challenges -> promocodes
    res = 0
    with session_scope() as session:
        challenges = session.query(Challenge).filter(Challenge.prizes.contains(prize.id)).all()
        for challenge in challenges:
            promocode_sum = 0
            for promocode in challenge.promocodes:
                promocode_sum += len(promocode.users_used)
            res += promocode_sum
        return res


def get_number_of_subscribers():
    return user_sub_checker.get_chat_member_count()


def get_number_of_referrals():
    with session_scope() as session:
        invited_users = session.query(User).filter(User.invited_by.isnot(None))
        return sum(1 for user in invited_users if user_sub_checker.is_subscribed(user.telegram_id))