import datetime
import json
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, RegexHandler, MessageHandler
from tzlocal import get_localzone

from create_excel import export

tz = get_localzone()
logging.basicConfig(filename='main.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
                    )
logger = logging.getLogger(__name__)

morning_tea_time = datetime.time(hour=16, minute=00, second=00)
evening_tea_time = datetime.time(hour=20, minute=00, second=00)

morning_sending_time = datetime.time(hour=12, minute=40, second=0, microsecond=0)
evening_sending_time = datetime.time(hour=17, minute=00, second=0, microsecond=0)


def load_base():
    with open('db.json') as f:
        data = json.load(f)
    return dict(data)


def save_base(data):
    with open('db.json', mode='w') as f:
        json.dump(data, f, ensure_ascii=False)


def load_calls():
    with open('calls.json') as f:
        data = json.load(f)
    return dict(data)


def save_calls(data):
    with open('calls.json', mode='w') as f:
        json.dump(data, f, ensure_ascii=False)


def add_user(uid, uname, name, room):
    uid = str(uid)
    data = load_base()
    if uid in data:
        prefs = data[uid]['prefs']
    else:
        prefs = []
    data[uid] = {'uid': uid, "uname": uname, "room": room, "name": name, "prefs": prefs}
    save_base(data)


def change_room(update: Update, context: CallbackContext) -> None:
    u = update.message.from_user
    db = load_base()
    n = update.message.text
    logger.info(f'Пользователь {u.name} поменял комнату сообщением "{n}"')
    if len(n) != 3:
        update.message.reply_text(
            'Чтобы записать номер своей комнаты - просто пришли мне его.\n\nТебе придёт уведомление, когда я смогу '
            'принять заказ!')
    else:
        if u.id not in db:
            add_user(u.id, u.username, u.name, update.message.text)
        else:
            db[str(u.id)]['room'] = update.message.text
        update.message.reply_text(
            'Номер комнаты успешно сохранён! Тебе придёт уведомление, когда я смогу принять заказ! ✅')

        calls = load_calls()
        last_call = max(calls.keys(), key=lambda x: eval(x))
        if str(u.id) not in calls[last_call]['receivers']:
            lc = eval(last_call)
            tea_call(context, tea_datetime=eval(last_call), message_time=f"{lc[0]} августа в {lc[1]}")


def start(update: Update, context: CallbackContext) -> None:
    u = update.message.from_user
    db = load_base()
    if str(u.id) not in db:
        logger.info(f'Пользователь {u.name} начал переписку')
        update.message.reply_text('Чтобы начать пользоваться ботом - пришли номер своей комнаты ‼️')
    else:
        logger.info(f'Пользователь {u.name} ввёл команду start')
        update.message.reply_text(
            'Чтобы записать номер своей комнаты - просто пришли мне его.\n\nТебе придёт уведомление, когда я смогу принять заказ!')


def morning_tea_call(context: CallbackContext, uid=None):
    d, time = datetime.datetime.now().day, f'{morning_tea_time.hour}:' + str(morning_tea_time.minute).rjust(2, '0')
    message_time = f"сегодня в {time}"
    logger.info(f'Запустил приём заказов на {time} {d} августа (утренний чай)')
    tea_call(context, tea_datetime=(d, time), message_time=message_time, uid=uid)


def evening_tea_call(context: CallbackContext, uid=None):
    d, time = datetime.datetime.now().day, f'{evening_tea_time.hour}:' + str(evening_tea_time.minute).rjust(2, '0')
    message_time = f"сегодня в {time}"
    logger.info(f'Запустил приём заказов на {time} {d} августа (вечерний чай)')
    tea_call(context, tea_datetime=(d, time), message_time=message_time, uid=uid)


def tea_call(context, tea_datetime, message_time, uid=None):
    calls = load_calls()
    if str(tea_datetime) not in calls:
        calls[str(tea_datetime)] = {'receivers': []}

    message = f"Какой чай тебе принести {message_time}? 🍃"
    tea_datetime_f = f"{tea_datetime[0]};{tea_datetime[1]}"

    db = load_base()
    keyboard = [
        [
            InlineKeyboardButton("Чёрный чай", callback_data=f"{tea_datetime_f};b"),
            InlineKeyboardButton("Зелёный чай", callback_data=f'{tea_datetime_f};g'),
        ],
        [InlineKeyboardButton("Кипяток", callback_data=f'{tea_datetime_f};h')],
        [InlineKeyboardButton("Я ничего не буду", callback_data=f'{tea_datetime_f};n')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if uid is None:
        for id in db:
            if str(id) not in calls[str(tea_datetime)]['receivers']:
                context.bot.send_message(chat_id=id, reply_markup=reply_markup, text=message)
                logger.info(f'Сообщение с выбором чая ({tea_datetime}) отправлено {uid}')
                calls[str(tea_datetime)]['receivers'] += [str(id)]
        save_calls(calls)
    else:
        if str(uid) not in calls[str(tea_datetime)]['receivers']:
            logger.info(f'Сообщение с выбором чая ({tea_datetime}) отправлено {uid}')
            context.bot.send_message(chat_id=uid, reply_markup=reply_markup, text=message)
            calls[str(tea_datetime)]['receivers'] += [str(uid)]
        save_calls(calls)


def send_excel(update: Update, context: CallbackContext):
    logger.info(f"Файл с базой данных экспортирован {update.message.from_user.name}")
    export('tea.xlsx')
    update.message.reply_document(
        document=open("tea.xlsx", "rb"),
        filename="TeaData.xlsx",
        caption="`Пожелания всех участников смены в Калиниграде.\n\nБот разработан @a_rassk`",
        parse_mode='markdown'
    )


def send_logs(update: Update, context: CallbackContext):
    logger.info(f"Лог экспортирован {update.message.from_user.name}")
    update.message.reply_document(
        document=open("main.log", "rb"),
        filename="TeaLogs.log",
        caption="`Технические логи бота.\n\nБот разработан @a_rassk`",
        parse_mode='markdown'
    )


def button(update: Update, context: CallbackContext) -> None:
    try:
        query = update.callback_query
        query.answer()
        uid = query.from_user.id

        db = load_base()
        db[str(uid)]['prefs'] += [query.data]
        save_base(db)

        order_day, order_time, selection = query.data.split(';')
        today = datetime.datetime.now().day
        order_day = int(order_day)

        if order_day == today:
            f_day = 'Сегодня'
        elif order_day + 1 == today:
            f_day = 'Завтра'
        else:
            f_day = f"{order_day} августа"
        f_day += f' в {order_time}'
        if selection == 'n':
            query.edit_message_text(text=f"Хорошо, принял")
        else:
            selection_d = {'b': 'чёрный чай', 'g': 'зелёный чай', 'h': 'кипяток'}
            logger.info(query.from_user.name + " выбрал/а " + selection_d[selection])
            query.edit_message_text(text=f"{f_day} в комнату {db[str(uid)]['room']} будет доставлен {selection_d[selection]}.")

    except Exception as e:
        logger.exception(f"{e, update.callback_query.from_user.id, update.callback_query.data }")


def help_command(update: Update, context: CallbackContext) -> None:
    logger.error(f"Пользователь {update.message.from_user.name} прислал сообщение, "
                 f"которое никак не обработалось - '{update.message.text}'")
    update.message.reply_text(
        "Чтобы изменить номер своей комнаты - просто пришли мне его.\n\nТебе придёт уведомление, когда я смогу принять заказ!")


def main():
    logger.info(f"Бот запущен")
    updater = Updater(os.environ.get('BOT_KEY'))

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(RegexHandler(callback=change_room, pattern=r"\d{3}"))
    updater.dispatcher.add_handler(CommandHandler('file', send_excel))
    updater.dispatcher.add_handler(CommandHandler('logs', send_logs))
    updater.dispatcher.add_handler(MessageHandler(callback=help_command, filters=None))

    j = updater.job_queue
    j.scheduler.configure(timezone=tz)

    morning_tea = j.run_daily(morning_tea_call, time=morning_sending_time)
    evening_tea = j.run_daily(evening_tea_call, time=evening_sending_time)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
