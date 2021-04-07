import discord
from discord.ext import commands
import requests
import json
import os
import time

class Suggest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    data = {}
    def json_exist(self, file_name):
        return os.path.exists(file_name)

    def load_storage(self):
        if os.path.exists('storage.json'):
            with open('storage.json') as f:
                self.data = json.load(f)
                return
        else:
            newData = {
                    "DeniedChannelId": 0,
                    "SuggestionChannelId": 0,
                    "TestingChannelId":0,
                    "Suggestions": [
                        {
                            "ModId": '',
                            "CurrentStage": "Voting",
                            "GuildId:":0,
                            "ChannelId":0,
                            "MessageId": 0,
                            "ChannelUrl": f''
                        }
                    ]
            }
            with open('storage.json', 'w') as f:
                json.dump(newData, f, sort_keys=True, indent=4)
            return

    def is_mod_fabric(self, jsonFile):
        for x in jsonFile['categories']:
            if x['name'] == 'Fabric':
                return True

        return False

    def mod_exists(self, modId):
        for x in self.data['Suggestions']:
            if x['ModId'] == modId:
                return True

        return False

    def add_mod(self, modId,guildId,channelId, messageId):
        newSuggestion = {
            "ModId": modId,
            "CurrentStage": "Voting",
            "GuildId:":guildId,
            "ChannelId":channelId,
            "MessageId": messageId,
            "ChannelUrl": f'https://discord.com/channels/{guildId}/{channelId}/{messageId}'
        }

        self.data["Suggestions"].append(newSuggestion)
        with open("storage.json", "w") as f:
            json.dump(self.data, f, sort_keys=True, indent=4)

    def return_message_url(self, modId):
        for x in self.data['Suggestions']:
            if x['ModId'] == modId:
                return x['ChannelUrl']

    def is_suggestion_url(self, suggestion):
        if 'curseforge.com' in suggestion:
            return True
        else:
            return False

    def search_mod(self, suggestion):
        split = suggestion.split('mc-mods/')
        searchString = split[1]

        header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15'}
        url = f'https://addons-ecs.forgesvc.net/api/v2/addon/{suggestion}'
        response = requests.get(url, headers=header)





    @commands.command()
    async def suggest(self, ctx,* ,suggestion: str):
        if self.data == {}:
            print('Loading storage...')
            self.load_storage()

        if self.mod_exists(suggestion):
            newEmbed = discord.Embed(title='Mod has already been suggested..See below')
            newEmbed.add_field(name='', value=f'{self.return_message_url(suggestion)}')
            await ctx.send(embed=newEmbed)
            return

        header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15'}
        url = f'https://addons-ecs.forgesvc.net/api/v2/addon/{suggestion}'
        response = requests.get(url, headers=header)

        if response.status_code != 200:
            await ctx.send('Please input a valid project ID.')
            return

        mod = response.json()
            
        if self.is_mod_fabric(mod) == False:
            await ctx.send('Eww... Forge mods are gross...')
            return

        newEmbed = discord.Embed(title=mod['name'])
        newEmbed.add_field(name='Link', value=mod['websiteUrl'])
        message = await ctx.send(embed=newEmbed)
        await message.add_reaction('👍')
        await message.add_reaction('👎')

        self.add_mod(suggestion,message.guild.id,message.channel.id, message.id)

def setup(bot):
    bot.add_cog(Suggest(bot))