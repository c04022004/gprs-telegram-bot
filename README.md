# gprs-telegram-bot
Interact with GPRS module via telegram bot. Inspired by a spare SIM card at home, I start experimenting with inexpensive [AliExpress](https://www.aliexpress.com/item/mini-A6-GPRS-GSM-Kit-Wireless-Extension-Module-Board-Antenna-Tested-Worldwide-Store-for-SIM800L/32710017861.html)/[Taobao](https://item.taobao.com/item.htm?id=536604770041) Chinese GPRS module (called GA6 mini). This is what I get so far reading through repositories and documentations.

## Hardware setup
I used an OrangePi as the host but you can change it to a RaspberryPi or PC or whatsoever:

<img src="https://i1.wp.com/oshlab.com/wp-content/uploads/2016/11/Orange-Pi-Zero-Pinout-banner2.jpg?fit=1200%2C628\&ssl=1" width="70%">

UART connections:

<img src="https://github.com/c04022004/gprs-telegram-bot/blob/master/docs/uart.jpg?raw=true" width="70%">

Be careful: some GPRS module (e.g. GA6 mini) requires a maximum of 5V 3A power input, please read through the datasheet before you begin.

## Software setup
- To start the script, make sure the machine can access the internet and do `sudo python GA6.py`, as controlling the GPIO pins on OrangePi requires root privileges. 
- You may consider putting the script in `/etc/rc.local`, so that it will run at root privileges on machine start up.
- If you are using a external UART-to-USB converter, you might want to write custom [udev rules](https://wiki.archlinux.org/index.php/udev) to make your device name consistent even after reboot.

## User parameters
In `config.txt`, we have the following key-value pairs:
1. **TELEGRAM_TOKEN**
  - This is where your Telegram Bot API token should be stored.
2. **LIST_OF_ADMINS**
  - This uses a [decorator](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#restrict-access-to-a-handler-decorator) to restrict access to a bot function.
  - The list of "admins" here is represented by `chat_id`, or `effective_user.id`. You can find it out by examining the result of the following code snippets.
``` python
>>> updates = bot.get_updates()
>>> print([u for u in updates])
>>> #print([u.message.chat_id for u in updates])

```
  - All function in this bot have restricted access so that only **you** can access the service.
3. **LIST_OF_CHATS**
  - When the bot recieve a call, a notification will be sent to this list of chats. This could be a chat with an individual, or groups.

## Usage
All telegram bot commands starts with a `/`
- `/start`: Check for availablility
- `/call <phone num>`: Call the number for 30s
- `/alarm_on"`: Start the alarm
- `/alarm_off` : Stop the alarm
- `/reset_jobs` : Not implemented
- `/help` : Print help message

When phone calls comes in, the a message with phone number will be sent to converstions in the `LIST_OF_CHATS`. Followed by a link to check junkcall online.

<img src="https://github.com/c04022004/gprs-telegram-bot/blob/master/docs/screenshot.jpg?raw=true" width="70%">


## Prototype
<img src="https://github.com/c04022004/gprs-telegram-bot/blob/master/docs/demo.jpg?raw=true" width="70%">

## Future development
This is just a side project to make my life esaier with a spare SIM card at home. I will implement more funtions if I have any real application. 

Here are some ideas:
- Integrate with my spare [thermal](https://www.aliexpress.com/item/JP-5890K-58mm-Thermal-Printer-for-Supermarket-Thermal-Receipt-Printer-for-POS-System-Thermal-Billing-Printer/32816249732.html) [printer](https://detail.tmall.com/item.htm?id=527613210422), printing a to-do list everyday
- Scheluded alarms to wake me up at the morning

## Credits and liks
- https://github.com/duxingkei33/orangepi_PC_gpio_pyH3
- http://pyserial.readthedocs.io
- https://en.wikipedia.org/wiki/Hayes_command_set
- https://docs.python.org/2/library/thread.html#module-thread
- https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot2.py
- https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#restrict-access-to-a-handler-decorator