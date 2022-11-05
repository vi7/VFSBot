
VFS Appointment Bot
===================

Telegram bot which automatically checks the available VFS appointments and notifies about the earliest openings.

How to use
----------

1. Clone the repo.
2. Enable virtualenv: `virtualenv venv`
3. Install the dependencies: `pip install -r requirements.txt`
4. Download the latest Chromedriver from [here](https://chromedriver.chromium.org/).
5. Move the chromedriver executable file somewhere in the `PATH`
6. Create a Telegram bot using [BotFather](https://t.me/BotFather) and save the auth token.
7. Make a Telegram channel to notify the appointment updates.
8. Use [this bot](https://t.me/username_to_id_bot) to find the channel id and your own account id.
9. Create and update the `config.ini` file with your VFS URL, account info, telegram token, and ids.
10. Run the script!

Description
-----------

This script was initially made for the BY visa center. However, it can also be used for other centers around the world. You might have to change the XPATH (available through inspect element) addresses in the `check_appointment()` function to your desired values.

### Telegram
The created bot should have two default commands:
1. /start: Starts the bot.
2. /quit: Stops the bot. (It can be started again using /start as long as the Python script is running.)

Next, add the created bot in the channel you want to post updates to and make sure it has admin priviliges. In order to prevent repitition of messages, the script will keep a record of updates in the record.txt file. Furthermore, by specifying your account id as admin_id in the config.ini, you can prevent others from using the bot, which might cause unexpected behaivor. If you want multiple accounts to access the bot, you can enter multiple ids in the config file separated by space.
