from telebot import types
import json

config_file_path = 'commands_config.json'


def set_commands(message, bot):
    data = json.load(open(config_file_path, 'r'))
    commands = []
    for com in data:
        commands.append(types.BotCommand(command=com, description=data[com]))
    bot.set_my_commands(commands)
    bot.set_chat_menu_button(message.chat.id, types.MenuButtonCommands('commands'))