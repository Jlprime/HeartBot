import os, logging, threading, schedule, random
from time import time, sleep
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException
from fetch import database_init, fetch

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
DIRECTORY = os.getenv('DIRECTORY')
TABLE_NAME = os.getenv('TABLE_NAME')
DEBUG = True

engine, headers = database_init(DIRECTORY,TABLE_NAME)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

bot = TeleBot(TOKEN)

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
    results_sample = random.sample(results, 10)
    # DEBUG and logger.info(results_sample)

    for result in results_sample:
        DEBUG and logger.info(result)
        DEBUG and logger.info(headers)
        caption_msg = ''
        signup = ''
        for key, value in zip(headers, result):
            if key != 'SignupLink' and value != 'None':
                caption_msg += f'{key}: {value}\n'
            else:
                signup = value
        DEBUG and logger.info(caption_msg)
        announcement_link = InlineKeyboardMarkup()
        announcement_link.add(InlineKeyboardButton('Sign me up!', url=signup))
        bot.send_message(chat_id=chat_id,text=caption_msg,reply_markup=announcement_link)

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

    