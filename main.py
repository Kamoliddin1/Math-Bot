############################################################################
## Django ORM Standalone Python Template
############################################################################
""" Here we'll import the parts of Django we need. It's recommended to leave
these settings as is, and skip to START OF APPLICATION section below """

# Turn off bytecode generation
import datetime
import sys

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
    print(chat_id)
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
    # if chosen_op:
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


def generate_question():
    a = random.randrange(1, 10)
    b = random.randrange(1, 10)
    random_operation = ['+', '-', '*']
    chosen_op = random.choice(random_operation)
    keyboard = generate_lv1_keyboard(a, b, chosen_op)
    text = f"⏳Sizda 26 sekund vaqt bor\n\n" \
           f"<i>Savol</i>: <b>{a} {chosen_op} {b}</b> <i>necha bo'ladi</i>\n" \
           f"Quyidagilardan to'g'ri javobni tanlang:"
    return text, keyboard


def game(update: Update, context: CallbackContext):
    # a = random.randrange(1, 10)
    # b = random.randrange(1, 10)
    # random_operation = ['+', '-', '*']
    # chosen_op = random.choice(random_operation)

    # keyboard = generate_lv1_keyboard(a, b, chosen_op)
    # text = f"⏳Sizda 26 sekund vaqt bor\n\n" \
    #        f"<i>Savol</i>: <b>{a} {chosen_op} {b}</b> <i>necha bo'ladi</i>\n" \
    #        f"Quyidagilardan to'g'ri javobni tanlang:"
    text, keyboard = generate_question()
    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                              parse_mode=ParseMode.HTML)


def callback_query(update: Update, context: CallbackContext):
    query = update.callback_query.data
    curr_id = update.callback_query.message.chat.id
    _, inp, answer, a, b, cho = query.split("|")
    print(query.split('|'))
    if inp == answer:
        p = Profile.objects.get(user_id=curr_id)
        p.score += 1
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


def render_progressbar(total, iteration, prefix='', suffix='', length=30, fill='█', zfill='░'):
    iteration = min(total, iteration)
    percent = "{0:.1f}"
    percent = percent.format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    pbar = fill * filled_length + zfill * (length - filled_length)
    return '{0} |{1}| {2}% {3}'.format(prefix, pbar, percent, suffix)


def callback_alarm(context: CallbackContext):
    job = context.job

    thirty_seconds = datetime.now() + timedelta(seconds=30)
    diff = round((thirty_seconds - datetime.now()).total_seconds(), 0)

    context.bot.send_message(chat_id=job.context, text=f"{diff}")


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_timer(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    try:
        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_repeating(callback_alarm, interval=1, first=1, last=30, context=chat_id,
                                        name=str(chat_id))

        text = 'Timer successfully set!'
        if job_removed:
            text += ' Old one was removed.'
        update.message.reply_text(text)
    except (IndexError, ValueError):
        update.message.reply_text('Usage /set <seconds>')


def unset(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Job was removed' if job_removed else 'No active timer was set'
    update.message.reply_text(text)


dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('game', game))
dispatcher.add_handler(CommandHandler('rank', ranking))

dispatcher.add_handler(CommandHandler("set", set_timer))
dispatcher.add_handler(CommandHandler("unset", unset))

dispatcher.add_handler(CallbackQueryHandler(callback_query))
updater.start_polling()
updater.idle()
