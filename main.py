import os
import logging
from time import time
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHANNEL_ID = -1001656350099
DEBUG = False

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
    except ApiTelegramException as e:
        if e.result_json['description'] == 'Bad Request: user not found':
            return False

def send_announcement():
    announcement_link = InlineKeyboardMarkup()
    announcement_link.add(InlineKeyboardButton('Sign me up!'))
    bot.send_message(chat_id=CHANNEL_ID,text=f"bot test {time()}")

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

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    pass

bot.set_my_commands([
    BotCommand('start','Initialisation'),
])

bot.infinity_polling()
