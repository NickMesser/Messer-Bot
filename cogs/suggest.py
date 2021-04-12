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
    messageId = None
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
                            "Comments":'', 
                            "Name": '',
                            "WebsiteUrl":''
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

    def add_mod(self, mod, message, comments, stage : str = 'suggestion'):
        newSuggestion = {
            "ModId": mod['id'],
            "CurrentStage": stage.lower(),
            "GuildId:":message.guild.id,
            "ChannelId":message.channel.id,
            "MessageId": message.id,
            "Comments" : '',
            "ChannelUrl": f'https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}',
            "Name": mod['name'], 
            "WebsiteUrl": mod['websiteUrl']
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
        for x in self.data['Suggestions']:
            if x['ModId'] == mod['ModId']:
                x['MessageId'] = message.id
                x['ChannelId'] = message.channel.id
                x['ChannelUrl'] = f'https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'
                x['CurrentStage'] = currentStage.lower()
                x['Comments'] = comments

        with open('storage.json','w') as f:
            json.dump(self.data, f, sort_keys=True, indent=4)

    @commands.guild_only()
    @commands.cooldown(1,3, commands.BucketType.user)
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
            newEmbed = discord.Embed(title='Mod has already been suggested..')
            modId = mod['id']
            newEmbed.add_field(name='Message Link:', value=f'{self.return_message_url(modId)}')
            await ctx.send(embed=newEmbed)
            return
            
        if self.is_mod_fabric(mod) == False or mod['isAvailable'] == False or mod['gameSlug'] != 'minecraft':
            await ctx.send('This mod does not appear to be fabric. Mod has submitted pending approval by a Staff member.')
            channel = self.bot.get_channel(self.data['PendingChannelId'])
            newEmbed = discord.Embed(title=mod['name'])
            newEmbed.add_field(name='ID:', value=mod['id'],inline=False)
            newEmbed.add_field(name='Link:', value=mod['websiteUrl'], inline=False)
            message = await channel.send(embed=newEmbed)
            self.add_mod(mod,message,'','pending')
            return

        newEmbed = discord.Embed(title=mod['name'])
        newEmbed.add_field(name='ID:', value=mod['id'], inline=False)
        newEmbed.add_field(name='Link:', value=mod['websiteUrl'], inline=False)
        channel = self.bot.get_channel(self.data['SuggestionChannelId'])
        message = await channel.send(embed=newEmbed)
        await message.add_reaction('👍')
        await message.add_reaction('👎')

        await ctx.message.add_reaction('👌')

        self.add_mod(mod,message,'','pending')

    @commands.guild_only()
    @commands.command(aliases=['approve','testing'])
    async def move(self, ctx,id : str = '9999999', channelToChange : str = '', *, comments = ''):
        if self.data == None:
            self.load_storage()

        selectedMod = None
        for x in self.data['Suggestions']:
            if id.isnumeric():
                if x['ModId'] == int(id):
                    selectedMod = x

        if selectedMod is None:
            await ctx.send('Could not find exisiting mod. Check input and retry.')
            return

        if '!!approve' in ctx.message.content:
            channelToChange == 'suggestions'

        if '!!testing' in ctx.message.content:
            channelToChange == 'testing'

        info = comments[:200] + (comments[200:] and '..')

        channel = None

        if '!!approve' in ctx.message.content:
            channel = self.bot.get_channel(self.data['SuggestionChannelId'])

        if '!!testing' in ctx.message.content:
            channel = self.bot.get_channel(self.data['TestingChannelId'])

        if channelToChange.lower() == 'suggestions':
            channel = self.bot.get_channel(self.data['SuggestionChannelId'])

        if channelToChange.lower() == 'denied':
            channel = self.bot.get_channel(self.data['DeniedChannelId'])

        if channelToChange.lower() == 'testing':
            channel = self.bot.get_channel(self.data['TestingChannelId'])

        if channelToChange.lower() == 'pending':
            channelToChange = self.bot.get_channel(self.data['PendingChannelId'])

        if channel == None:
            await ctx.send('Please specify a valid channel.')
            return

        newEmbed = discord.Embed(title=selectedMod['Name'])
        newEmbed.add_field(name='Id', value=selectedMod['ModId'],inline=False)
        newEmbed.add_field(name='Link', value=selectedMod['WebsiteUrl'], inline=False)

        if channelToChange.lower() == 'denied' and info != '':
            newEmbed.add_field(name='Comments:', value = info, inline=False)

        messageId = selectedMod['MessageId']
        oldChannel = self.bot.get_channel(selectedMod['ChannelId'])
        oldMsg = await oldChannel.fetch_message(messageId)
        await oldMsg.delete()
        
        message = await channel.send(embed=newEmbed)
        await ctx.message.add_reaction('👌')

        print(channelToChange)

        if channelToChange.lower() == 'suggestions':
            await message.add_reaction('👍')
            await message.add_reaction('👎')

        self.update_mod(message, channelToChange.lower(), selectedMod, info)

    @commands.guild_only()
    @commands.command()
    async def deny(self, ctx, id: str = '999999999', *, reason: str = ''):
        if self.data == None:
            self.load_storage()

        selectedMod = None
        for x in self.data['Suggestions']:
            if id.isnumeric():
                if x['ModId'] == int(id):
                    selectedMod = x

        if selectedMod is None:
            await ctx.send('Could not find exisiting mod. Check input and retry.')
            return

        info = reason[:200] + (reason[200:] and '..')

        channel = self.bot.get_channel(self.data['DeniedChannelId'])

        messageId = selectedMod['MessageId']
        oldChannel = self.bot.get_channel(selectedMod['ChannelId'])
        oldMsg = await oldChannel.fetch_message(messageId)
        await oldMsg.delete()

        newEmbed = discord.Embed(title=selectedMod['Name'])
        newEmbed.add_field(name='Id', value=selectedMod['ModId'],inline=False)
        newEmbed.add_field(name='Link', value=selectedMod['WebsiteUrl'], inline=False)

        if reason != '':
            newEmbed.add_field(name='Comments:', value = info, inline=False)

        message = await channel.send(embed=newEmbed)
        await ctx.message.add_reaction('👌')

        self.update_mod(message, 'denied', selectedMod, info)
        

def setup(bot):
    bot.add_cog(Suggest(bot))