import asyncio
import logging
import os
import aiohttp
import sys
from typing import Literal, Optional

import discord
from discord.ext import commands, tasks


class Stream:
    def __init__(self, title, streamer, game, stream_url):
        self.title = title
        self.streamer = streamer
        self.game = game  
        self.stream_url = stream_url

async def getOAuthToken():
    params = {
        'client_id': "trbgvg3l30bsinc3glldwyafbe2jwc",
        'client_secret': "5hk8z0jlwwv476t447vtaz3kjppvul",
        'grant_type': 'client_credentials'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post('https://id.twitch.tv/oauth2/token', params=params) as response:
            keys = await response.json()

    if 'access_token' in keys:
        return keys['access_token']
    else:
        print("Access token not found")
        return None


async def checkIfLive(channel):
    url = f"https://api.twitch.tv/helix/streams?user_login={channel}"
    token = await getOAuthToken()

    headers = {
        'Client-ID': "trbgvg3l30bsinc3glldwyafbe2jwc",
        'Authorization': 'Bearer ' + token
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                res = await response.json()

        if 'data' in res and len(res['data']) > 0:
            data = res['data'][0]
            title = data['title']
            streamer = data['user_name']
            game = data['game_name']
            stream_url = f"https://www.twitch.tv/{channel}"
            stream = Stream(title, streamer, game, stream_url)
            return stream
        else:
            return None
    except Exception as e:
        return None



class Streams(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"EmployeeBot.{self.__class__.__name__}")
        self.bot = bot
        self.is_live = False
        self.game_cache = None
    
    async def cog_load(self) -> None:
        self.twitch_notifs.start()

    def cog_unload(self) -> None:
        self.twitch_notifs.cancel()

    @tasks.loop(seconds=30)
    async def twitch_notifs(self):
        print(self.game_cache)
        ping_channel = self.bot.get_channel(997151061007671367)
        channel = "PoodleBoyY"
        stream = await checkIfLive(channel)
        ping = ping_channel.guild.get_role(1109653383608029194)
        
        if stream is not None and self.is_live is False:
            self.is_live = True
            livestatement = f"**Hey {ping.mention},\n{channel} is NOW LIVE ON TWITCH, playing: {stream.game}**\nGo watch the stream!\nStream URL: {stream.stream_url}"
            self.game_cache = stream.game
            await ping_channel.send(livestatement)
        
        elif stream is None and self.is_live is not None:
            self.is_live = False
            endstatement = f"{channel}'s stream has now ended, thank you all so much for watching! :purple_heart:"
            await ping_channel.send(endstatement)
        
        elif stream is not None and self.is_live is True and self.game_cache != stream.game:
            gamechange = f"**Playing a New Game!**,\n{channel} is NOW PLAYING: **{stream.game}**\nGo watch the stream!\nStream URL: <{stream.stream_url}>"
            await ping_channel.send(gamechange)
            self.game_cache = stream.game

    @twitch_notifs.before_loop
    async def before_twitch_notifs(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Streams(bot))