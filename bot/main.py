from telebot import apihelper
import telebot
import utils

with open("data/token.txt", "r") as token:
    bot = telebot.TeleBot(token.read())


@bot.message_handler(commands=["start"])
def send_startup_message(message):
    if message.chat.type != "private":
        utils.add_group_to_table(message.chat.id)
        with open("message_strings/start_command.txt", "r") as f:
            bot.send_message(message.chat.id, f.read())


@bot.message_handler(commands=["help"])
def send_help_message(message):
    if message.chat.type != "private":
        utils.add_group_to_table(message.chat.id)
        with open("message_strings/help_command.txt", "r") as f:
            bot.send_message(message.chat.id, f.read())


@bot.message_handler(commands=["config"])
def send_config_message(message):
    if message.chat.type != "private":
        sent_msg = False
        for obj in apihelper.get_chat_administrators(bot.token, message.chat.id):
            if obj["user"]["id"] == message.from_user.id:
                with open("message_strings/config_command.txt", "r") as f:
                    bot.send_message(message.chat.id, f.read())
                    sent_msg = True
        if not sent_msg:
            bot.send_message(message.chat.id, "It seems like you're not the group administrator!")


@bot.message_handler(commands=["conf_edit"])
def conf_edit_handler(message):
    text = message.text.split(" ")
    sent_msg = False
    for obj in apihelper.get_chat_administrators(bot.token, message.chat.id):
        if obj["user"]["id"] == message.from_user.id:
            if len(text) == 1:
                bot.send_message(message.chat.id, "Specify the parameter!")
                sent_msg = True
            elif text[1] in ["report_system", "max_reports", "default_mute_time"]:
                if len(text) > 2:
                    utils.edit_preset(message.chat.id, text[1], text[2])
                    utils.set_group_preset(message.chat.id, str(message.chat.id))
                    bot.send_message(message.chat.id, "Done!")
                    sent_msg = True
                else:
                    bot.send_message(message.chat.id, "Specify the value!")
                    sent_msg = True
            else:
                bot.send_message(message.chat.id, "This parameter doesn't exist!")
    if not sent_msg:
        bot.send_message(message.chat.id, "It seems like you're not the group administrator!")


@bot.message_handler(commands=["mute"])
def mute_user(message):
    text = message.text.split(" ")
    sent_msg = False
    for obj in apihelper.get_chat_administrators(bot.token, message.chat.id):
        if obj["user"]["id"] == message.from_user.id:
            if len(text) == 1:
                bot.send_message(message.chat.id, "Specify the username!")
                sent_msg = True
            else:
                if len(text) > 2:
                    utils.mute_user(text[1], message.chat.id, text[2])
                    bot.send_message(message.chat.id, f"Muted {text[1]} for {text[2]} minutes!")
                    sent_msg = True
                else:
                    utils.mute_user(text[1], message.chat.id, utils.get_from_config_preset(message.chat.id, "default_mute_time"))
                    bot.send_message(message.chat.id, f"Muted {text[1]}! They will be unmuted after your group's config preset 'default_mute_time' passes!")
                    sent_msg = True
    if not sent_msg:
        bot.send_message(message.chat.id, "It seems like you're not the group administrator!")


@bot.message_handler(commands=["unmute"])
def unmute_user(message):
    text = message.text.split(" ")
    sent_msg = False
    for obj in apihelper.get_chat_administrators(bot.token, message.chat.id):
        if obj["user"]["id"] == message.from_user.id:
            if len(text) == 1:
                bot.send_message(message.chat.id, "Specify the username!")
                sent_msg = True
            else:
                utils.unmute_user(text[1], message.chat.id)
                bot.send_message(message.chat.id, f"Unmuted {text[1]}!")
                sent_msg = True
    if not sent_msg:
        bot.send_message(message.chat.id, "It seems like you're not the group administrator!")


@bot.message_handler(commands=["report"])
def report(message):
    text = message.text.split(" ")
    if len(text) == 1:
        bot.send_message(message.chat.id, "Specify the username!")
    else:
        utils.report_user(text[1], message.chat.id)
        bot.send_message(message.chat.id, f"Reported {text[1]}! They may or may not be muted now! If they are muted, they will be unmuted after your group's config preset 'default_mute_time' passes!")



@bot.message_handler(func=lambda message: True)
def check_msg(message):
    if utils.check_if_user_muted(message.from_user.id, message.chat.id):
        if not utils.unmute_user_if_mute_passed_else_return_false(message.from_user.username, message.chat.id):
            bot.delete_message(message.chat.id, message.message_id)


if __name__ == "__main__":
    bot.polling(none_stop=True)
