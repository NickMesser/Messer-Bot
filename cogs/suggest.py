import discord
from discord.ext import commands
import requests
import json
import os
import time

class Suggest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    data = None
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
                    "DiscussionChannelId":0,
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

    def get_mod_data_by_id(self,ctx, modId):
        header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15'}
        url = f'https://addons-ecs.forgesvc.net/api/v2/addon/{modId}'
        response = requests.get(url, headers=header)

        if response.status_code != 200:
            return None

        return response.json()

    def get_mod_data_by_url(self, ctx, url):
        split = url.split('mc-mods/')
        searchString = split[1]
        header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Safari/605.1.15'}
        responce = requests.get(f'https://addons-ecs.forgesvc.net/api/v2/addon/search?categoryId=0&gameId=432&gameVersion=&index=0&pageSize=255&searchFilter={searchString}&sectionId=0&sort=0', headers=header)
        
        if responce.status_code != 200:
            return None

        data = responce.json()
        for x in data:
            if x['slug'] == searchString:
                return x

        return None

    @commands.command()
    async def suggest(self, ctx,* ,userInput: str = ''):
        if self.data == None:
            self.load_storage()

        if ctx.message.channel.id != self.data['DiscussionChannelId']:
            return

        if self.is_suggestion_url(userInput):
            mod = self.get_mod_data_by_url(ctx, userInput)
        else:
            mod = self.get_mod_data_by_id(ctx, userInput)

        if mod is None:
            await ctx.send('Please check input and try again. If problem persist please use the mods project id found on the mods homepage.')
            return

        if self.mod_exists(mod['id']):
            newEmbed = discord.Embed(title='Mod has already been suggested..See below')
            modId = mod['id']
            newEmbed.add_field(name='Message:', value=f'{self.return_message_url(modId)}')
            await ctx.send(embed=newEmbed)
            return
            
        if self.is_mod_fabric(mod) == False:
            await ctx.send('Eww... Forge mods are gross...')
            return

        newEmbed = discord.Embed(title=mod['name'])
        newEmbed.add_field(name='Link', value=mod['websiteUrl'])
        channel = self.bot.get_channel(self.data['SuggestionChannelId'])
        message = await channel.send(embed=newEmbed)
        await message.add_reaction('👍')
        await message.add_reaction('👎')

        self.add_mod(mod['id'],message.guild.id,message.channel.id, message.id)

    @commands.command
    async def set_channel(self, ctx, *, channelToChange : str = '', id : str = ''):
        await ctx.send('set channel command')
        

def setup(bot):
    bot.add_cog(Suggest(bot))