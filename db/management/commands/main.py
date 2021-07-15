############################################################################
## Django ORM Standalone Python Template
############################################################################
""" Here we'll import the parts of Django we need. It's recommended to leave
these settings as is, and skip to START OF APPLICATION section below """

# Turn off bytecode generation
import datetime
import sys
from django.core.management import BaseCommand

from django.utils import timezone

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

# logging.basicConfig(level=logging.DEBUG,
#                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
PORT = int(os.environ.get('PORT', 8443))
updater = Updater(token=settings.TOKEN)
dispatcher: Dispatcher = updater.dispatcher
job: JobQueue = updater.job_queue


def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    context.chat_data.update({'has_game': 0})
    p, _ = Profile.objects.get_or_create(
        user_id=chat_id,
        defaults={
            'first_name': update.message.from_user.username,
            'last_name': update.message.from_user.last_name
        }
    )
    text = f'*Assalomu Alaykum*✋\n Matematika sinovlariga _Xush Kelibsiz_📚\n' \
           f'*_Bu bot sizning hisob\-kitob 🧮 mahoratingizni tekshiradi_*\n' \
           f'__Boshlash uchun__ `/game` yozing\n'

    update.message.reply_text(text=text, parse_mode=ParseMode.MARKDOWN_V2)


# Logic
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
    lvl_emojis = {1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣'}
    chosen_op = random.choice(random_operation)
    keyboard = generate_lv1_keyboard(a, b, chosen_op)

    text = f"_Siz hozir_ *{lvl_emojis[LEVEL]}* _bosqichdasiz_\n" \
           f"Sizda __*10 sekund*__ ⏰ vaqt bor❗️\n " \
           f"\t\t\t🤔_*Savol*_: __*{a} \{chosen_op} {b}*__ _*necha bo'ladi*_❓\n" \
           f"Quyidagilardan👇🏻 to'g'ri javobni tanlang:"
    return text, keyboard


def game(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    profile = Profile.objects.get(user_id=chat_id)
    level = profile.level
    chat_data = context.chat_data
    chat_data.update({'msg_id': update.message.message_id + 1})
    chat_data.update({'emoji': []})
    text, keyboard = generate_question(level)

    if context.chat_data['has_game'] == 0:
        context.bot.send_message(text=text, chat_id=chat_id,
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                                 parse_mode=ParseMode.MARKDOWN_V2)
    else:
        context.bot.send_message(text=f"Natijangizni yaxshilash uchun avval `/reset` buyrug'ini bering",
                                 chat_id=chat_id, parse_mode=ParseMode.MARKDOWN_V2)


def callback_query(update: Update, context: CallbackContext):
    query = update.callback_query.data
    curr_id = update.callback_query.message.chat.id
    _, inp, answer, a, b, cho = query.split("|")
    chat_data = context.chat_data
    msg_id = chat_data['msg_id']

    pressed = timezone.now()
    created = update.callback_query.message.date
    edit_date = update.callback_query.message.edit_date
    if edit_date:
        total = (pressed - edit_date).total_seconds()
    else:
        total = (pressed - created).total_seconds()
    profile = Profile.objects.get(user_id=curr_id)
    level = profile.level
    if level < 4:
        text, keyboard = generate_question(level)
        can = '✅'
        cant = '❌'
        didnt = '☑️'

        if inp == answer and total < 10:
            profile.score += 1
            if profile.score <= 2:
                profile.level = 1
            elif profile.score <= 5:
                profile.level = 2
            elif profile.score <= 7:
                profile.level = 3
            elif profile.score <= 9:
                profile.level = 4

            profile.save()
            chat_data['emoji'].append(can)
        elif inp == answer and total > 10 or inp != answer and total > 10:
            chat_data['emoji'].append(didnt)
            profile.score -= 0.5
        else:
            chat_data['emoji'].append(cant)
            profile.score -= 1
        profile.user_spend += total
        profile.save()
        s = '\t'.join(res for res in chat_data['emoji'])
        extra_info = f"{s}\n{text}"
        context.bot.edit_message_text(text=extra_info, chat_id=curr_id, message_id=msg_id,
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                                      parse_mode=ParseMode.MARKDOWN_V2)
    else:
        context.chat_data.update({'has_game': 1})
        context.bot.delete_message(chat_id=curr_id, message_id=msg_id)
        can = chat_data['emoji'].count('✅')
        cant = chat_data['emoji'].count('❌')
        didnt = chat_data['emoji'].count('☑')
        text = f"<b>🏁O'yin tugadi</b>\n" \
               f"Qatnashganingiz uchun rahmat\n\n" \
               f"\t\t\t\t\t\t\t\t📈Natijalaringiz\n" \
               f"⏱Ketgan Vaqt {round(profile.user_spend, 2)} sekund\n" \
               f"✅To'g'ri ➡️ <b>{can}</b>\n"\
               f"❌Xato ➡️ <b>{cant}</b>\n"\
               f"☑Ulgurmagan ➡️ <b>{didnt}</b>\n\n" \
               f"Faxriylar jadvalini ko'rish uchun <pre>/rank</pre>"
        context.bot.send_message(text=text, chat_id=curr_id, parse_mode=ParseMode.HTML)


def ranking(update: Update, context: CallbackContext):
    players = Profile.objects.order_by('-score')[:10]
    text = f'Bizning Faxriylarimiz \n\n'
    medals = ['🥇', '🥈', '🥉']
    for index, player in enumerate(players):
        if index < len(medals):
            text += f'{medals[index]} {player.first_name}'
        else:
            text += player.first_name
        text += '\n'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.HTML)


def callback_alarm(context: CallbackContext):
    job = context.job
    thirty_seconds = datetime.now() + timedelta(seconds=30)

    diff = round((thirty_seconds - datetime.now()).total_seconds(), 0)
    print(job, diff)
    context.bot.send_message(chat_id=403839849, text=f"{diff}")


def add_queue(update: Update, context: CallbackContext, func):
    job_id = update.effective_message.message_id + update.effective_user.id
    print('\n\n queue')
    context.job_queue.scheduler.add_job(callback_alarm, 'interval', id=job_id, minutes=1)

    print(job_id)
    return job_id


def remove_queue(context: CallbackContext):
    # context.job_queue.scheduler.remove_job(id=str(job_id))
    pass


# def stop_job_if_exists(name: str, context: CallbackContext, b:bool) -> bool:
#     """Remove job with given name. Returns whether job was removed."""
#     current_jobs = context.job_queue.get_jobs_by_name(name)
#     print(f"\n\n\n{current_jobs}")
#
#     if not current_jobs:
#         return False
#     for job in current_jobs:
#         print(f"\n\n\n------------{job} ------ {job.job.id}")
#     return True
#
#
# def delete_job_if_exists(name: str, context: CallbackContext, b:bool) -> bool:
#     """Remove job with given name. Returns whether job was removed."""
#     current_jobs = context.job_queue.get_jobs_by_name(name)
#
#     if not current_jobs:
#         return False
#     for job in current_jobs:
#         job.schedule_removal()
#     return True
#
#
# def set_timer(update: Update, context: CallbackContext):
#     chat_id = update.message.chat_id
#     message_id = update.message.message_id-1
#     try:
#         job.run_repeating(callback_alarm, interval=5, first=1, last=30, context=chat_id,
#                           name=str(chat_id))
#         context.bot.edit_message_text(text='25', chat_id=chat_id, message_id=message_id)
#         context.bot.edit_message_text(text='20', chat_id=chat_id, message_id=message_id)
#         context.bot.edit_message_text(text='15', chat_id=chat_id, message_id=message_id)
#
#     except (IndexError, ValueError):
#         update.message.reply_text('Usage /set <seconds>')

# def render_progressbar(total, iteration, prefix='', suffix='', length=6, fill='⬛', zfill='🔲'):
#     iteration = min(total, iteration)
#     percent = "{0:.1f}"
#     percent = percent.format(100 * (iteration / float(total)))
#     filled_length = int(length * iteration // total)
#     pbar = zfill * (length - filled_length) + fill * filled_length
#     return '{0} |{1}| {2}% {3}'.format(prefix, pbar, percent, suffix)


def reset(update: Update, context: CallbackContext):
    curr_id = update.message.chat_id
    profile = Profile.objects.get(user_id=curr_id)
    profile.score = 0
    profile.level = 1
    profile.user_spend = 0.0
    context.chat_data.update({'has_game': 0})
    profile.save()
    text = f"Sizning barcha erishganlaringiz  yo'qga aylantirildi\n" \
           f"Hozirgi Level {profile.level} va Hozirgi  Ballar {profile.score}"
    context.bot.send_message(curr_id, text)


class Command(BaseCommand):
    help = 'Telegram_bot'

    def handle(self, *args, **options):
        try:
            pass
        except Exception as e:
            print(e)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('game', game))
    dispatcher.add_handler(CommandHandler('rank', ranking))
    dispatcher.add_handler(CommandHandler('reset', reset))

    dispatcher.add_handler(CallbackQueryHandler(callback_query))
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=settings.TOKEN,
                          # webhook_url="https://math-bot-app.herokuapp.com/" + settings.TOKEN)
                          webhook_url="https://c6bc1322b105.ngrok.io/" + settings.TOKEN)

    updater.idle()
