import time
import os
import sys
import errno

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO, filename='/home/pi/telebot.log')

logger = logging.getLogger(__name__)

# https://github.com/duxingkei33/orangepi_PC_gpio_pyH3
from time import sleep
from pyA20.gpio import gpio
from pyA20.gpio import port
gpio.init()
gpio.setcfg(port.PA6, gpio.OUTPUT)
gpio.setcfg(port.PA7, gpio.OUTPUT)
gpio.output(port.PA7, 1)
sleep(0.1)
gpio.output(port.PA7, 0)
logger.info("Resetting the SIM module...")

# http://pyserial.readthedocs.io
# https://en.wikipedia.org/wiki/Hayes_command_set
import serial
ser = serial.Serial(port="/dev/ttyS1", baudrate="115200", timeout=1)

while(ser.in_waiting<80):
	sleep(1)

in_txt = ""
while(not "+CREG:" in in_txt):
	in_txt = ser.readline().rstrip()

if(in_txt!="+CREG: 1"):
	logger.info("Failed to register the network.")
	logger.info("Error: "+in_txt)
	exit(1)

ser.write("AT+CLIP=1\r")
ser.readline().rstrip()
if(ser.readline().rstrip()!="OK"):
	logger.info("Failed to register caller display.")
	logger.info("Error: "+in_txt)
	exit(1)

logger.info("Device ready.")

# https://docs.python.org/2/library/threading.html
# https://docs.python.org/2/library/thread.html#module-thread
import thread
sim_lock = thread.allocate_lock()

# https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot2.py
# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#restrict-access-to-a-handler-decorator
# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Examples
# https://github.com/eugenio412/PogomBOT/blob/master/pogobot.py
import telegram
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from functools import wraps
import json


logger.info("Reading config...")
config_path = os.path.join(os.path.dirname(sys.argv[0]), "config.txt")
global config
try:
	with open(config_path, "r") as f:
		config = json.loads(f.read())
except Exception as e:
	logger.error('%s' % (repr(e)))
	config = {}

admin_list = config.get('LIST_OF_ADMINS', [])
def restricted(func):
	@wraps(func)
	def wrapped(bot, update, *args, **kwargs):
		user_id = update.effective_user.id
		chat_id = update.message.chat_id
		if user_id not in admin_list:
			logger.info("Unauthorized access denied for {}.".format(user_id))
			bot.send_message(chat_id=chat_id, text="Unauthorized access")
			return
		return func(bot, update, *args, **kwargs)
	return wrapped

@restricted
def cmd_start(bot, update):
	chat_id = update.message.chat_id
	logger.info('[%s] Starting.' % (chat_id))
	update.message.reply_text("You are authorized!")

@restricted
def cmd_help(bot, update):
	chat_id = update.message.chat_id
	logger.info('[%s] Help.' % (chat_id))
	response = " The following commands are available:\n"
	commands = [["/start", "Check for availablility"],
				["/call <phone num>", "Call the number for 30s"],
				["/alarm_on", "Start the alarm"],
				["/alarm_off", "Stop the alarm"],
				["/reset_jobs", "Not implemented"],
				["/help", "Get this message"]
				]
	for command in commands:
		response += command[0] + " " + command[1] + "\n"
	update.message.reply_text(response)

@restricted
def cmd_alarm_on(bot, update):
	chat_id = update.message.chat_id
	logger.info('[%s] Alarm_on.' % (chat_id))
	gpio.output(port.PA6, 1)
	update.message.reply_text("Alarm set.")

@restricted
def cmd_alarm_off(bot, update):
	chat_id = update.message.chat_id
	logger.info('[%s] Alarm_off.' % (chat_id))
	gpio.output(port.PA6, 0)
	update.message.reply_text("Alarm cleared.")

@restricted
def cmd_call(bot, update, args):
	chat_id = update.message.chat_id
	if len(args) <= 0:
		logger.info('[%s] Calling with no phone number.' % (chat_id))
		update.message.reply_text("No phone number provided!")
		return
	with sim_lock:
		phone_no = args[0]
		logger.info('[%s] Calling' % (chat_id))
		update.message.reply_text("Calling "+ phone_no)
		ser.write(("ATD"+phone_no+"\r").encode())
		logger.info(ser.readline().rstrip())
		ret = ser.readline().rstrip()
		logger.info(ret)
		if(ret !="OK"):
			update.message.reply_text("Call failed.")
		else:
			sleep(30)
			ser.write("ATH\r")
			update.message.reply_text("Call ended.")
		while(ser.in_waiting):
			buf = ser.readline().rstrip()
			if(buf != ""):
				logger.info(buf)

while(ser.in_waiting):
	print(ser.readline().rstrip())


def error(bot, update, error):
	logger.warn('Update "%s" caused error "%s"' % (update, error))
	
logger.info('TELEGRAM_TOKEN: <%s>' % (config.get('TELEGRAM_TOKEN', None)))
token = config.get('TELEGRAM_TOKEN', None)
updater = Updater(token)
b = Bot(token)
logger.info("BotName: <%s>" % (b.name))
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", cmd_start))
dp.add_handler(CommandHandler("help", cmd_help))
dp.add_handler(CommandHandler("alarm_on", cmd_alarm_on))
dp.add_handler(CommandHandler("alarm_off", cmd_alarm_off))
dp.add_handler(CommandHandler("call", cmd_call, pass_args=True))
dp.add_error_handler(error)
updater.start_polling()
logger.info("Telegram bot has started...")

# https://docs.python.org/2/howto/regex.html
import re
def match_num(in_txt):
	p = re.compile("[0-9]{8,}")
	m = p.search(in_txt)
	if m:
		return m.group()
	else:
		return ""

chat_list = config.get('LIST_OF_CHATS', [])
while(1):
	with sim_lock:
		in_txt = ser.readline().rstrip()
		if(in_txt == "" or in_txt == "RING"):
			continue
		logger.info(in_txt)
		if("+CLIP:" in in_txt):
			for chat_id in chat_list:
				# b.send_message(chat_id=chat_id, text=in_txt)
				phone_no = match_num(in_txt)
				b.send_message(chat_id=chat_id, text=in_txt)
				noti_txt = "[Check for junkcall](https://m.hkjunkcall.com/?ft="
				noti_txt += phone_no + "&s=on)"
				b.send_message(chat_id=chat_id, text=noti_txt, parse_mode=telegram.ParseMode.MARKDOWN)

ser.close()

