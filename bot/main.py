import datetime as dt
import os, logging, threading, schedule, random
from time import time, sleep
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from fetch import database_init, fetch

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
DIRECTORY = os.getenv('DIRECTORY')
TABLE_NAME = os.getenv('TABLE_NAME')
DEBUG = False

announcement_key_mappings = {
    'Portal': 'Website',
    'EventName': 'Event Title',
    'Organizer': 'Organiser',
    'EventLocation': 'Event Location',
    'EventDate': 'Event Date',
}

announcement_value_mappings = {
    'GIVING_SG': 'giving.sg',
    'VOLUNTEER_SG': 'volunteer.gov.sg',
    'None': 'Open to All',
}

engine, headers = database_init(DIRECTORY,TABLE_NAME)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

bot = TeleBot(TOKEN)

# States Group
class SearchQuery:
    def __init__(self):
        self.reset()
    def reset(self):
        self.portal = ''
        self._event_start = dt.date(2000, 1, 1)
        self._event_end = dt.date(2000, 1, 1)
        self.event_start_date = 0
        self.event_end_date = 0
    def get_all_values(self):
        return [self.portal, self.event_start_date, self.event_end_date]

global_query = SearchQuery()


def is_subscribed(channel_id, user_id):
    try:
        response = bot.get_chat_member(channel_id, user_id)
        DEBUG and logger.info(response)
        return response.status not in ['left', 'banned']
    except ApiTelegramException as error:
        if error.result_json['description'] == 'Bad Request: user not found':
            return False
        else:
            raise error

@bot.message_handler(commands=['start'])
def command_welcome(message):
    user_id = message.from_user.id

    if not is_subscribed(CHANNEL_ID, user_id):
        invite = bot.create_chat_invite_link(CHANNEL_ID, member_limit=1, expire_date=int(time()) + 300) # 5 minute invite link
        InviteLink = invite.invite_link # Get the actual invite link from 'invite' class
        
        link = InlineKeyboardMarkup() # Created Inline Keyboard Markup
        link.add(InlineKeyboardButton("Join the channel", url=InviteLink)) # Added Invite Link to Inline Keyboard
        
        bot.send_message(
            chat_id=message.chat.id,
            text=f"Hey there {message.from_user.first_name}, Click the link below to join our announcements channel",
            reply_markup=link)
    else:
        bot.send_message(chat_id=message.chat.id,text="Welcome!")

def send_message_to(chat_id, results):
    DEBUG and logger.info(results)
    for i, result in enumerate(results):
        title_msg = ''
        caption_msg = ''
        signup = ''
        image_url = ''
        # ['Portal', 'EventName', 'Organizer', 'EventLocation', 'EventDate', 'Vacancies', 'SignupLink', 'Suitability', 'ImageURL', 'id']
        for key, value in zip(headers, result):
            if key == 'EventDate':
                date_value = dt.datetime.fromtimestamp(float(value)).strftime('%a, %d %b %Y')
                caption_msg += f'{announcement_key_mappings.get(key, key)}: {date_value}\n'
            elif key == 'EventName':
                title_msg += f'<b>{value}</b>\n'
            elif key == 'Organizer':
                title_msg += f'<em>{value}</em>\n\n'
            elif key == 'ImageURL':
                image_url = value
            elif key != 'SignupLink':
                if value:
                    caption_msg += f'{announcement_key_mappings.get(key, key)}: {announcement_value_mappings.get(value, value)}\n'
            else:
                signup = value
        main_msg = title_msg + caption_msg

        DEBUG and logger.info(f'Current Iteration: {i}\nPayload: {result}')
        announcement_link = InlineKeyboardMarkup()
        announcement_link.add(InlineKeyboardButton('Sign me up!', url=signup))
        bot.send_photo(chat_id=chat_id,photo=image_url,caption=main_msg,reply_markup=announcement_link,parse_mode='HTML')

def send_announcement_to(samples):
    results = fetch(engine, TABLE_NAME, 'EventDate', '<=', time() + 864000)
    results_sample = random.sample(results, samples)
    send_message_to(CHANNEL_ID,results_sample)

@bot.callback_query_handler(func=lambda call: 'portal' in call.data)
def handle_callback(call):
    DEBUG and logger.info(call)
    action, option = call.data.split()

    if action == 'portal':
        bot.answer_callback_query(call.id)
        global_query.portal = option
        search_event_start_date(call.message)
        return
    return

@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=0))
def handle_start_calendar(call):
    result, key, step = DetailedTelegramCalendar(calendar_id=0,min_date=dt.date.today()).process(call.data)
    if not result and key:
        bot.edit_message_text(f"Select the starting date: {LSTEP[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"You selected {result} as the starting date",
                              call.message.chat.id,
                              call.message.message_id)
        global_query._event_start = result + dt.timedelta(days=1)
        global_query.event_start_date = int(dt.datetime.combine(result, dt.time.min).timestamp())
        search_event_end_date(call.message)

@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def handle_end_calendar(call):
    result, key, step = DetailedTelegramCalendar(calendar_id=1, min_date=global_query._event_start).process(call.data)
    if not result and key:
        bot.edit_message_text(f"Select the end date: {LSTEP[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        success = bot.edit_message_text(f"You selected {result} as the end date",
                              call.message.chat.id,
                              call.message.message_id)
        global_query._event_end = result
        global_query.event_end_date = int(dt.datetime.combine(result, dt.time.min).timestamp())
        search_fetch(call.message)

@bot.message_handler(commands=['search'])
def command_search(message):
    global_query.reset()
    row_one, row_two, row_three = [], [], []
    row_one.append(InlineKeyboardButton('giving.sg',callback_data='portal giving'))
    row_two.append(InlineKeyboardButton('volunteer.gov.sg',callback_data='portal volunteer'))
    row_three.append(InlineKeyboardButton('Both', callback_data='portal both'))
    reply_markup = InlineKeyboardMarkup([row_one,row_two,row_three])

    bot.send_message(message.chat.id,text='Filter by Website:',reply_markup=reply_markup)


def search_event_start_date(message):
    DEBUG and logger.info(global_query.portal)
    calendar, step = DetailedTelegramCalendar(calendar_id=0, min_date=dt.date.today()).build()
    bot.send_message(message.chat.id,
                     f"Select the starting date: {LSTEP[step]}",
                     reply_markup=calendar)
 
def search_event_end_date(message):
    DEBUG and logger.info(global_query.event_start_date)
    calendar, step = DetailedTelegramCalendar(calendar_id=1, min_date=global_query._event_start).build()
    bot.send_message(message.chat.id,
                     f"Select the end date: {LSTEP[step]}",
                     reply_markup=calendar)

def convert_portal_to_fetch_query(portal):
    if portal == 'both':
        return "'%'"
    elif portal == 'giving':
        return "'GIVING_SG'"
    elif portal == 'volunteer':
        return "'VOLUNTEER_SG'"

def search_fetch(message):
    portal, start, end = global_query.get_all_values()
    portal = convert_portal_to_fetch_query(portal)
    results = fetch(engine, TABLE_NAME, ['Portal', 'EventDate', 'EventDate'], ["LIKE", ">=", "<="], [portal, start, end])
    if len(results) == 0:
        bot.send_message(message.chat.id,text="No opportunities found!")
        return
    results_sample = random.sample(results, min(len(results), 3))
    send_message_to(message.chat.id,results_sample)

bot.set_my_commands([
    BotCommand('start','Start up the bot'),
    BotCommand('search', 'Find specific opportunities')
])

if __name__ == '__main__':
    # CHANGE ANNOUNCEMENT INTERVAL
    # schedule.every(30).seconds.do(send_announcement_to, 2).tag(CHANNEL_ID)

    threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
    while True:
        schedule.run_pending()
        sleep(1)

    