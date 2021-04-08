import discord
import json
import os
import sys
from discord.ext import commands


def json_exist(file_name):
    return os.path.exists(file_name)


def load_data_file():
    if not json_exist('data.json'):
        data = {'BotToken': '', 'BotPrefix': '!!'}
        with open('data.json', 'w') as newfile:
            json.dump(data, newfile, sort_keys=True, indent=4)
        sys.exit('Please add bot token and bot prefix to data.json')

    with open("data.json") as f:
        return json.load(f)


data = load_data_file()

bot = commands.Bot(command_prefix=data['BotPrefix'])


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


@commands.command
async def reload(ctx):
    bot.load_extension('cogs.suggest')
    ctx.send('Reloaded commands...')


bot.load_extension('cogs.suggest')

if data['BotToken'] == '':
  token = os.getenv('TOKEN')
else:
  token = data['BotToken']

print(token)

bot.run(token)
