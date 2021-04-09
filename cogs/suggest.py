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
                    'PendingChannelId':0,
                    "Suggestions": [
                        {
                            "ModId": '',
                            "CurrentStage": "suggestion",
                            "GuildId:":0,
                            "ChannelId":0,
                            "MessageId": 0,
                            "ChannelUrl": f'',
                            "Comments":''
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

    def add_mod(self, modId,guildId,channelId, messageId, comments):
        newSuggestion = {
            "ModId": modId,
            "CurrentStage": "suggestion",
            "GuildId:":guildId,
            "ChannelId":channelId,
            "MessageId": messageId,
            "Comments" : '',
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

    def update_mod(self, message, currentStage, mod, comments):
        for x in self.data:
            if x['ModId'] == mod['ModId']:
                x['MessageId'] == message.id
                x['ChannelId'] = message.channel.id
                x['ChannelUrl'] = f'https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'
                x['CurrentStage'] = currentStage.lower()
                x['Comments'] = comments

        with open('storage.json' 'w') as f:
            json.dump(self.data, f, sort_keys=True, indent=4)

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
            await ctx.send('This mod does not appear to be fabric. Mod has submitted pending approval by a Staff member.')
            channel = self.bot.get_channel(self.data['PendingChannelId'])
            newEmbed = discord.Embed(title=mod['name'])
            newEmbed.add_field(name='Link:', value=mod['websiteUrl'])
            newEmbed.add_field(name='ID:', value=mod['id'])
            message = await channel.send(embed=newEmbed)
            return

        newEmbed = discord.Embed(title=mod['name'])
        newEmbed.add_field(name='Link:', value=mod['websiteUrl'])
        newEmbed.add_field(name='ID:', value=mod['id'])
        channel = self.bot.get_channel(self.data['SuggestionChannelId'])
        message = await channel.send(embed=newEmbed)
        await message.add_reaction('👍')
        await message.add_reaction('👎')

        self.add_mod(mod['id'],message.guild.id,message.channel.id, message.id, '')

    @commands.command()
    async def move(self, ctx, *, id : str = '', channelToChange : str = '', comments : str  = ''):
        if self.data == None:
            self.load_storage()

        selectedMod = None
        for x in self.data['Suggestions']:
            if x['ModId'] == id:
                selectedMod = x

        if selectedMod is None:
            await ctx.send('Could not find exisiting mod. Check input and retry.')

        channel = None

        if channelToChange.lower() == 'suggestions':
            channel = self.bot.get_channel(self.data['SuggestionChanne;'])

        if channelToChange.lower() == 'denied':
            channel = self.bot.get_channel(self.data['DeniedChannel'])

        if channelToChange.lower() == 'testing':
            channel = self.bot.get_channel('TestingChannelId')

        if channelToChange.lower() == 'pending':
            channelToChange = self.bot.get_channel(self.data['PendingChannelId'])

        if channel == None:
            await ctx.send('Please specify a valid channel.')

        oldMsg = self.bot.get_channel(selectedMod['ChannelId']).fetch_message(selectedMod['MessageId'])
        await oldMsg.delete()

        newEmbed = discord.Embed(title=selectedMod['name'])
        newEmbed.add_field(name='Link', value=selectedMod['websiteUrl'])

        if selectedMod['CurrentStage'] == 'denied':
            newEmbed.add_field(name='Comments:', value = comments)

        message = await channel.send(embed=newEmbed)

        if channelToChange.lower == 'suggestion':
            await message.add_reaction('👍')
            await message.add_reaction('👎')

        self.update_mod(message, channelToChange.lower, selectedMod, comments)
        
            


def setup(bot):
    bot.add_cog(Suggest(bot))