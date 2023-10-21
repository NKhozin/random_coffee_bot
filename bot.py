import logging
import pickle
from itertools import combinations
from typing import Optional, Tuple
from telegram.constants import ParseMode
from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ChatMemberHandler
from db_commands import *
from itertools import combinations
import psycopg2
import sqlalchemy.exc
from datetime import datetime
import pandas as pd
import random
import re
import configparser
from tabulate import tabulate

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

config_obj = configparser.ConfigParser()
config_obj.read("configfile.ini")

tg_bot = config_obj["tg_bot"]

token = tg_bot["token"]

def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member

async def start_coffee_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_free_time_and_pairs()

    if not data.empty:
        for index, row in data.iterrows():
            member_id_1 = row.member_id_1
            member_id_2 = row.member_id_2
            free_time = row.free_time.strftime('%Y-%m-%d %H:%M')

            if will_be_a_meeting(member_id_1, member_id_2):
                #print('Встреча будет')
                continue
            elif will_be_a_meeting_person(member_id_1, free_time) or will_be_a_meeting_person(member_id_2, free_time):
                #print('Время занято')
                continue
            elif was_a_meeting(member_id_1, member_id_2):
                #print('Встреча уже была')
                continue
            else:
                insert_pairs(member_id_1, member_id_2)
                pair_id = get_last_pair_id()

                quot = '"'
                href_1 = f"<a href={quot}tg://user?id={member_id_1}{quot}>{get_first_name(member_id_1)}</a>"
                href_2 = f"<a href={quot}tg://user?id={member_id_2}{quot}>{get_first_name(member_id_2)}</a>"

                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Следующие участники Fandom-coffee {href_1} и {href_2} выбраны для встречи 😎", parse_mode=ParseMode.HTML)

                free_random_room = choose_free_room(free_time)

                if free_random_room:
                    pre_text = f"Встреча успешно забронирована! ☕\n"
                    text = insert_room(free_random_room, free_time, pair_id, member_id_1, member_id_2)
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=pre_text+'<pre>'+text+'</pre>'+'\n Приятного общения! ❤️', parse_mode=ParseMode.HTML)

                    pre_text = f"⭐ У вас предстощая встреча! ⭐\n"
                    try:
                        await context.bot.send_message(chat_id=member_id_1, text=pre_text+'<pre>'+text+'</pre>'+'\n Приятного общения! ❤️', parse_mode=ParseMode.HTML)
                    except Exception as e:
                        print(e)

                    try:
                        await context.bot.send_message(chat_id=member_id_2, text=pre_text+'<pre>'+text+'</pre>', parse_mode=ParseMode.HTML)
                    except Exception as e:
                        print(e)

                    #Изменение статусов встреч как будто они успешно прошли
                    #text = change_meeting_status(pair_id, member_id_1, member_id_2)
                    #await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

        await start_coffee_time(update, context)
    elif if_all_meets_completed_or_booked():
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Все возможные встречи забронированы или прошли! 😥")
    else:
        data = get_pairs_without_rooms()
        if not data.empty:
            members_id = list(set(data.member_id_1.to_list()+data.member_id_2.to_list()))
            members_name = [get_first_name(i) for i in members_id]
            quot = '"'
            hrefs = [f"<a href={quot}tg://user?id={member_id}{quot}>{member_name}</a>" for member_id, member_name in zip(members_id, members_name)]
            text = ', '.join(hrefs) + ' выберите, пожалуйста, другое время. Все свободные комнаты сейчас, к сожалению, заняты. 😫'
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Все возможные встречи прошли!😥')

async def greet_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветствие новых пользователей, уведомление других пользователей о том, что кто-то покинул чат"""
    result = extract_status_change(update.chat_member)

    if result is None:
        return

    was_member, is_member = result
    user = update.chat_member.from_user
    first_name=user.first_name
    member_id=user.id
    username=user.username
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()

    if not was_member and is_member:
        await update.effective_chat.send_message(
            f"{member_name} добавился в наш чатик. Добро пожаловать! 🤩 \nВведите удобное время для встречи.\nНапример, '17:30-19:00, 20:00-20:30'\nДля получения уведомлений о встрече в личных сообщениях начните чат с https://t.me/tulahack_random_coffee_bot",
            parse_mode=ParseMode.HTML,
        )
        insert_members(member_id, first_name, username)
    elif was_member and not is_member:
        await update.effective_chat.send_message(
            f"{member_name} покинул наш чатик 😭",
            parse_mode=ParseMode.HTML,
        )
        delete_members(member_id)

def extract_free_time(time_string):
    """Обработка строки удобного времени для встречи от пользователя из чата"""
    now = datetime.now().strftime('%Y-%m-%d')
    times = re.findall(r'\d\d:\d\d-\d\d:\d\d', fr'{time_string}')
    all_time_range = []

    for time in times:
        time_list = [now+' '+i for i in time.split('-')]
        time_range = pd.date_range(time_list[0], time_list[1], freq='30min')[:-1]
        time_range = [i.strftime('%Y-%m-%d %H:%M') for i in time_range.to_list()]
        all_time_range.extend(time_range)
    return all_time_range

async def time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений из чата. Предполагается, что пользователи могут писать только удобное время для встречи в чат. Обработка других значений не предполагается"""
    user = update.message.from_user
    first_name=user.first_name
    member_id=user.id
    username=user.username
    html = user.mention_html()

    extract_time = extract_free_time(update.message.text)
    if extract_time:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{html}, спасибо! Время успешно выбрано!", parse_mode=ParseMode.HTML)
        for time in extract_time:
            insert_members_free_time(member_id, time)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{html}, выбранное время некорректно!", parse_mode=ParseMode.HTML)
    
async def update_meetings_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для обновления статусов встреч в БД, которые уже прошли"""
    change_meeting_status_by_time()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Статусы встреч обновлены!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для приветствия в личных сообщениях"""
    await context.bot.send_message(chat_id=update.message.from_user.id, text="Привет! Здесь ты будешь получать уведомления о предстоящих встречах!")

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для администратора, чтобы очистить прошедшие встречи"""
    truncate_table('pairs')
    truncate_table('rooms')
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Данные по прошедшим встречам удалены!")

if __name__ == '__main__':
    application = ApplicationBuilder().token(token).build()
    application.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    choose_handler = CommandHandler('start', start)
    application.add_handler(choose_handler)

    choose_handler = CommandHandler('clear_history', clear_history)
    application.add_handler(choose_handler)

    choose_handler = CommandHandler('start_coffee_time', start_coffee_time)
    application.add_handler(choose_handler)

    choose_handler = CommandHandler('update_meetings_status', update_meetings_status)
    application.add_handler(choose_handler)

    time_handler = MessageHandler(filters.TEXT, time)
    application.add_handler(time_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
