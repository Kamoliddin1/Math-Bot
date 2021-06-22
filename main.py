############################################################################
## Django ORM Standalone Python Template
############################################################################
""" Here we'll import the parts of Django we need. It's recommended to leave
these settings as is, and skip to START OF APPLICATION section below """

# Turn off bytecode generation
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
    ParseMode
)
from telegram.ext import (
    Updater,
    Dispatcher,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    JobQueue
)
from db.models import Profile
import random
import logging
import operator

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
    update.message.reply_text(f'Assalomu Alaykum Matematika sinovlariga Xush Kelibsiz'
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


def callback_alarm(bot, job):
    bot.send_message(chat_id=job.context, text='BEEP')


def callback_timer(bot, update, job_queue):
    bot.send_message(chat_id=update.message.chat_id,
                     text='Setting a timer for 1 minute!')

    job_queue.run_once(callback_alarm, 60, context=update.message.chat_id)


def game(update: Update, context: CallbackContext):
    a = random.randrange(1, 10)
    b = random.randrange(1, 10)
    random_operation = ['+', '-', '*']
    chosen_op = random.choice(random_operation)

    keyboard = generate_lv1_keyboard(a, b, chosen_op)
    # text = f"⏳Sizda 26 sekund vaqt bor\n\n" \
    #        f"_Savol_: *{a} \{chosen_op} {b}* _necha_ _bo'ladi_\n" \
    #        f"Quyidagilardan to'g'ri javobni tanlang:"
    # update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    #                           parse_mode=ParseMode.MARKDOWN_V2)

    text = f"⏳Sizda 26 sekund vaqt bor\n\n" \
           f"<i>Savol</i>: <b>{a} {chosen_op} {b}</b> <i>necha bo'ladi</i>\n" \
           f"Quyidagilardan to'g'ri javobni tanlang:"
    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                              parse_mode=ParseMode.HTML)


def callback_query(update: Update, context: CallbackContext):
    query = update.callback_query.data
    print('\n------\n---------')
    curr_id = update.callback_query.message.chat.id
    print(curr_id)
    print('\n------\n---------')
    print(query)
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
    players = Profile.objects.order_by('-score')
    res = dict()
    text = f'Bizning Faxriylarimiz \n\n'
    medal = ['🏅','🥇', '🥈', '🥉']
    for player in players:
        res[player] = player.score
    sorted_score = {k: v for k, v in sorted(res.items(), key=lambda item: item[1], reverse=True)}
    for k in sorted_score:
        text += f'{medal[0]}<i>@{k}</i> - <b>{sorted_score[k]}</b>'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.HTML)


dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('game', game))
dispatcher.add_handler(CommandHandler('rank', ranking))
dispatcher.add_handler(CommandHandler('timer', callback_timer, pass_job_queue=True))
dispatcher.add_handler(CallbackQueryHandler(callback_query))
updater.start_polling()
updater.idle()
