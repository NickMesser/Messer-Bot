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

    def save_storage(self):
        with open('storage.json','w') as f:
            json.dump(self.data, f, sort_keys=True, indent=4)


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
                            "WebsiteUrl":'',
                            "UpVotes":0,
                            "DownVotes":0
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
            "WebsiteUrl": mod['websiteUrl'],
            "UpVotes":0,
            "DownVotes":0
        }

        self.data["Suggestions"].append(newSuggestion)
        self.save_storage()

    def remove_mod_from_database(self, mod):
        self.data['Suggestions'].remove(mod)
        self.save_storage()

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

    def get_mod_by_message_id(self, messageId):
        for x in self.data['Suggestions']:
            if x['MessageId'] == messageId:
                return x

    def get_mod_by_mod_id(self, modId):
        for x in self.data['Suggestions']:
            if x['ModId'] == int(modId):
                return x
            
        return None

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

        self.save_storage()

    @commands.guild_only()
    @commands.cooldown(1,3, commands.BucketType.user)
    @commands.command()
    async def suggest(self, ctx,* ,userInput: str = ''):

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
    @commands.has_any_role('Moderator', 'Team AOF', 'Trusted')
    async def move(self, ctx,id : str = '9999999', channelToChange : str = '', *, comments = ''):

        selectedMod = self.get_mod_by_mod_id(id)
        if selectedMod is None:
            await ctx.send('Could not find existing mod. Check input and retry.')
            return

        if '!!approve' in ctx.message.content:
            channelToChange = 'suggestions'

        if '!!testing' in ctx.message.content:
            channelToChange = 'testing'

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
            channel = self.bot.get_channel(self.data['PendingChannelId'])

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

        if channelToChange.lower() == 'suggestions':
            print('I made it into here!')
            await message.add_reaction('👍')
            await message.add_reaction('👎')

        self.update_mod(message, channelToChange.lower(), selectedMod, info)

    @commands.has_any_role('Moderator', 'Team AOF', 'Trusted')
    @commands.guild_only()
    @commands.command()
    async def deny(self, ctx, id: str = '999999999', *, reason: str = ''):

        selectedMod = self.get_mod_by_mod_id(id)
        if selectedMod is None:
            await ctx.send('Could not find existing mod. Check input and retry.')
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

    @commands.has_any_role('Moderator', 'Team AOF', 'Trusted')
    @commands.guild_only()
    @commands.command()
    async def remove(self, ctx,* ,modId: str = '999999999999'):

        mod = self.get_mod_by_mod_id(modId)

        if mod == None:
            await ctx.send('Could not find existing mod. Check input and retry.')
            return

        messageId = mod['MessageId']
        oldChannel = self.bot.get_channel(mod['ChannelId'])
        oldMsg = await oldChannel.fetch_message(messageId)
        await oldMsg.delete()

        self.remove_mod_from_database(mod)
        await ctx.message.add_reaction('👌')

    @commands.Cog.listener()
    async def on_ready(self):
        self.load_storage()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        messageId = payload.message_id

        mod = self.get_mod_by_message_id(messageId)

        if mod == None:
            return

        if payload.emoji.name == '👍':
            mod['UpVotes'] += 1
            self.save_storage()

        if payload.emoji.name == '👎':
            mod['DownVotes'] += 1
            self.save_storage()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if self.data == None:
            self.load_storage()

        messageId = payload.message_id

        mod = self.get_mod_by_message_id(messageId)

        if mod == None:
            return

        if payload.emoji.name == '👍':
            mod['UpVotes'] -= 1
            self.save_storage()

        if payload.emoji.name == '👎':
            mod['DownVotes'] -= 1
            self.save_storage()


def setup(bot):
    bot.add_cog(Suggest(bot))
