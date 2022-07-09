from datetime import datetime
import os, logging, threading, schedule, random
from time import time, sleep
from dotenv import load_dotenv
from telebot import TeleBot, custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from telebot.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException
from fetch import database_init, fetch

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
DIRECTORY = os.getenv('DIRECTORY')
TABLE_NAME = os.getenv('TABLE_NAME')
DEBUG = True

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

state_storage = StateMemoryStorage()
bot = TeleBot(TOKEN,state_storage=state_storage)

# States Group
class SearchQuery(StatesGroup):
    # Just name variables differently
    portal = State() # creating instances of State class is enough from now
    event_date = State()
    event_location = State()

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
def send_welcome(message):
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

def send_announcement_to(chat_id):
    results = fetch(engine, TABLE_NAME, 'EventDate', '<=', time() + 864000)
    results_sample = random.sample(results, 1)
    # DEBUG and logger.info(results_sample)

    for i, result in enumerate(results_sample):
        caption_msg = ''
        signup = ''
        image_url = ''
        # ['Portal', 'EventName', 'Organizer', 'EventLocation', 'EventDate', 'Vacancies', 'SignupLink', 'Suitability', 'ImageURL', 'id']
        for key, value in zip(headers, result):
            if key == 'EventDate':
                date_value = datetime.fromtimestamp(float(value)).strftime('%a, %d %b %Y')
                caption_msg += f'{announcement_key_mappings.get(key, key)}: {date_value}\n'
            elif key == 'ImageURL':
                image_url = value
            elif key != 'SignupLink':
                if value:
                    caption_msg += f'{announcement_key_mappings.get(key, key)}: {announcement_value_mappings.get(value, value)}\n'
            else:
                signup = value
        DEBUG and logger.info(f'Current Iteration: {i}\nPayload: {result}')
        announcement_link = InlineKeyboardMarkup()
        announcement_link.add(InlineKeyboardButton('Sign me up!', url=signup))
        bot.send_photo(chat_id=chat_id,photo=image_url,caption=caption_msg,reply_markup=announcement_link)

@bot.message_handler(state="*", commands='cancel')
def any_state(message):
    """
    Cancel state
    """
    bot.send_message(message.chat.id, "Your query was cancelled.")
    bot.delete_state(message.from_user.id, message.chat.id)

@bot.message_handler(commands=['search'])
def send_search(message):
    bot.set_state(message.from_user.id, SearchQuery.Portal, message.chat.id)
    bot.send_message(message.chat.id, '')

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())

bot.set_my_commands([
    BotCommand('start','Initialisation'),
])

if __name__ == '__main__':
    # CHANGE ANNOUNCEMENT INTERVAL
    send_announcement_to(CHANNEL_ID)
    schedule.every(30).seconds.do(send_announcement_to, CHANNEL_ID).tag(CHANNEL_ID)

    threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
    while True:
        schedule.run_pending()
        sleep(1)

    