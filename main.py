############################################################################
## Django ORM Standalone Python Template
############################################################################
""" Here we'll import the parts of Django we need. It's recommended to leave
these settings as is, and skip to START OF APPLICATION section below """

# Turn off bytecode generation
import datetime
import sys
from threading import Event

import settings

sys.dont_write_bytecode = True

# Django specific settings
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
import django

django.setup()

# Import your models for use in your script
from db.models import *

############################################################################
## START OF APPLICATION
############################################################################
from telegram.constants import MESSAGEENTITY_ALL_TYPES
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode, InlineQueryResultArticle, InputTextMessageContent
)
from telegram.ext import (
    Updater,
    Dispatcher,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    JobQueue, InlineQueryHandler
)
from db.models import Profile
import random
import logging
import operator
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

updater = Updater(token=settings.TOKEN)
dispatcher: Dispatcher = updater.dispatcher
job: JobQueue = updater.job_queue


def start(update: Update, callback: CallbackContext):
    chat_id = update.message.chat_id
    p, _ = Profile.objects.get_or_create(
        user_id=chat_id,
        defaults={
            'first_name': update.message.from_user.username,
            'last_name': update.message.from_user.last_name
        }
    )
    update.message.reply_text(f'Assalomu Alaykum Matematika sinovlariga Xush Kelibsiz\n'
                              f'Boshlash uchun /game yozing')


def generate_lv1_keyboard(a, b, chosen_op):
    operator_functions = {
        '+': operator.add(a, b),
        '-': operator.sub(a, b),
        '*': operator.mul(a, b),
        '/': operator.truediv(a, b),
    }
    operation = operator_functions[chosen_op]

    answer = operation
    first, second = a, b

    rand_list = [answer, answer + 1, answer + 2]
    random.shuffle(rand_list)
    keyboard = [
        [
            InlineKeyboardButton(f"{rand_list[0]}",
                                 callback_data=f'l1|{rand_list[0]}|{answer}|{first}|{second}|{chosen_op}'),
            InlineKeyboardButton(f"{rand_list[1]}",
                                 callback_data=f'l1|{rand_list[1]}|{answer}|{first}|{second}|{chosen_op}'),
            InlineKeyboardButton(f"{rand_list[2]}",
                                 callback_data=f'l1|{rand_list[2]}|{answer}|{first}|{second}|{chosen_op}'),
        ],
    ]
    return keyboard


def generate_question(level):
    a = random.randrange(1, 10)
    b = random.randrange(1, 10)
    LEVEL = level
    # thirty_seconds = datetime.now() + timedelta(seconds=30)
    # context.user_data.update({
    #     'level': LEVEL,
    #     # 'time': thirty_seconds
    # })
    # try:
    #
    #     thirty_seconds = context.user_data['time']
    #     # diff = round((thirty_seconds - datetime.now()).total_seconds(), 0)
    # except TypeError:
    #     pass
    print("--------------------------------------------------")
    print(LEVEL)
    print("--------------------------------------------------")
    if LEVEL == 1:
        random_operation = ['+']
    elif LEVEL == 2:
        random_operation = ['+', '-']
    elif LEVEL == 3:
        random_operation = ['+', '-', '*']
    elif LEVEL == 4:
        random_operation = ['+', '-', '*', '/']
    else:
        random_operation = ['+', '-', '*', '/']

    chosen_op = random.choice(random_operation)
    keyboard = generate_lv1_keyboard(a, b, chosen_op)
    time = 30
    left = 25

    progress = render_progressbar(time, left)
    text = f"⏳{progress}" \
           f"⏳Sizda {left} sekund vaqt bor\n\n" \
           f"<i>Savol</i>: <b>{a} {chosen_op} {b}</b> <i>necha bo'ladi</i>\n" \
           f"Quyidagilardan to'g'ri javobni tanlang:"
    return text, keyboard


def game(context: CallbackContext):
    # a = random.randrange(1, 10)
    # b = random.randrange(1, 10)
    # random_operation = ['+', '-', '*']
    # chosen_op = random.choice(random_operation)

    # keyboard = generate_lv1_keyboard(a, b, chosen_op)
    # text = f"⏳Sizda 26 sekund vaqt bor\n\n" \
    #        f"<i>Savol</i>: <b>{a} {chosen_op} {b}</b> <i>necha bo'ladi</i>\n" \
    #        f"Quyidagilardan to'g'ri javobni tanlang:"
    try:
        context.user_data.update({
            'level': 4,
        })
        level = context.user_data['level']
    except AttributeError:
        level = 1
    text, keyboard = generate_question(level)

    # update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    #                           parse_mode=ParseMode.HTML)

    # job = context.job

    context.bot.send_message(text=text, chat_id=context.job.context,
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                             parse_mode=ParseMode.HTML)
    stop_job_if_exists(str(403839849), context, b=False)


def callback_query(update: Update, context: CallbackContext):
    query = update.callback_query.data
    curr_id = update.callback_query.message.chat.id
    _, inp, answer, a, b, cho = query.split("|")
    print(query.split('|'))
    if query:
        stop_job_if_exists(str(403839849), context, b=True)

    if inp == answer:
        p = Profile.objects.get(user_id=curr_id)
        p.score += 1
        print(context.user_data)
        p.save()
        text = f"Sizning javobingiz to'g'ri\n" \
               f'<b>{a} {cho} {b}</b> = {answer} ✅\n😁'
    else:
        text = f"Sizning javobingiz noto'g'ri\n" \
               f'<b>{a} {cho} {b}</b> = {inp} ❌\n😱'
    text = f'{update.callback_query.message.text}  \n\n{text}'
    context.bot.edit_message_text(text=text,
                                  chat_id=update.callback_query.message.chat.id,
                                  message_id=update.callback_query.message.message_id,
                                  parse_mode=ParseMode.HTML)
    # Event().wait(5)
    # context.bot.edit_message_text(text=text+"\nhello world",
    #                               chat_id=update.callback_query.message.chat.id,
    #                               message_id=update.callback_query.message.message_id,
    #                               parse_mode=ParseMode.HTML)


def ranking(update: Update, context: CallbackContext):
    players = Profile.objects.order_by('-score')[:10]
    res = dict()
    text = f'Bizning Faxriylarimiz \n\n'
    medal = ['🏅', '🥇', '🥈', '🥉']
    for player in players:
        res[player] = player.score
    sorted_score = {k: v for k, v in sorted(res.items(), key=lambda item: item[1], reverse=True)}
    for k in sorted_score:
        text += f'{medal[0]}<i>@{k}</i> - <b>{sorted_score[k]}</b>'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.HTML)


def render_progressbar(total, iteration, prefix='', suffix='', length=6, fill='⬛', zfill='🔲'):
    iteration = min(total, iteration)
    percent = "{0:.1f}"
    percent = percent.format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    pbar = zfill * (length - filled_length) + fill * filled_length
    return '{0} |{1}| {2}% {3}'.format(prefix, pbar, percent, suffix)


def callback_alarm(context: CallbackContext):
    job = context.job
    thirty_seconds = datetime.now() + timedelta(seconds=30)

    diff = round((thirty_seconds - datetime.now()).total_seconds(), 0)
    print(job, diff)

    context.bot.send_message(chat_id=403839849, text=f"{diff}")


def stop_job_if_exists(name: str, context: CallbackContext, b: bool) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    print(f"\n\n\n{current_jobs}")
    if not current_jobs:
        return False
    for job in current_jobs:
        print(f"\n\n\n{job}")
        job.enabled = b
    return True


def set_timer(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    try:
        job_min = job.run_repeating(game, interval=5, first=1, last=30, context=chat_id,
                                    name=str(chat_id))
        stop_job_if_exists(str(update.message.chat_id), context, b=True)

        # job_min.enabled = False
        game(context)
    except (IndexError, ValueError):
        update.message.reply_text('Usage /set <seconds>')


dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('game', set_timer))
dispatcher.add_handler(CommandHandler('rank', ranking))

# dispatcher.add_handler(CommandHandler("set", set_timer))

dispatcher.add_handler(CallbackQueryHandler(callback_query))
updater.start_polling()
updater.idle()
