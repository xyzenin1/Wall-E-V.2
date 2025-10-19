import discord
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
import os
from yt_dlp import YoutubeDL
import traceback
import subprocess
import shutil



class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.is_playing = {}
        self.is_paused = {}
        self.musicQueue = {}
        self.queueIndex = {}
        
        # find ffmpeg path
        self.ffmpeg_path = os.getenv("FFMPEG_PATH")
        
        # ytdl options
        self.YTDL_OPTIONS = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'default_search': 'auto',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False
        }
        # ffmpeg options
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
            'options': '-vn -af "volume=0.25"'
        }       
        
        self.vc = {}
        self.embedBlue = 0x3498db
        
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            id = int(guild.id)
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.is_paused[id] = self.is_playing[id] = False
            
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        id = int(member.guild.id)
        if member.id != self.bot.user.id and before.channel != None and after.channel != before.channel:
            remainingChannelMembers = before.channel.members
            if len(remainingChannelMembers) == 1 and remainingChannelMembers[0].id == self.bot.user.id and self.vc[id].is_connected():
                self.is_playing[id] = self.is_paused[id] = False
                self.musicQueue[id] = []
                self.queueIndex[id] = 0
                await self.vc[id].disconnect()
            
            
    def now_playing_embed(self, ctx, song):
        title = song['title']
        link = song['link']
        thumbnail = song['thumbnail']
        author = ctx.author
        avatar = author.display_avatar.url
        
        embed = discord.Embed (
            title = "Now Playing",
            description=f'[{title}]({link})',       # acts like a link; {} is the text displayed for link and () is for actual link
            colour=self.embedBlue,
        )
        embed.set_thumbnail(url=thumbnail)      # thumbnail
        embed.set_footer(text=f'Song added by: {str(author)}', icon_url=avatar)     # author
        return embed
        
    
    # join vc   
    async def join_vc(self, ctx, channel):
        id = int(ctx.guild.id)
        if self.vc[id] == None or not self.vc[id].is_connected():
            self.vc[id] = await channel.connect()

            if self.vc[id] == None:
                await ctx.send("Could not connect to the voice channel.")
                return
        else:
            await self.vc[id].move_to(channel)
            

    # search youtube
    def search_youtube(self, search):
        queryString = parse.urlencode({'search_query': search})     # format
        htmContent = request.urlopen('https://www.youtube.com/results?' + queryString)   # search youtube with search string entered and return list
        searchResults = re.findall('/watch\?v=(.{11})', htmContent.read().decode())     
        return searchResults[0:10]      # return first 10
    
    def extract_youtube(self, url):
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info('https://www.youtube.com/watch?v=' + url, download=False)
            except:
                return False
        return {
            'link': 'https://www.youtube.com/watch?v=' + url,
            'thumbnail': 'https://i.ytimg.com/vi/' + url + '/hqdefault.jpg?sqp=-oaymwEcCOADEI4CSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLD5uL4xKN-IUfez6KIW_j5y70mlig',
            'video_id': url,
            'title': info['title']
        #   'source': info['formats'][0]['url']
        }
    
    
    
    # get fresh url
    def get_fresh_url(self, video_id):
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                url = 'https://www.youtube.com/watch?v=' + video_id
                info = ydl.extract_info(url, download=False)
                
                
                # find best audio format
                if 'formats' in info:
                    audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                    if audio_formats:
                        best_audio = max(audio_formats, key=lambda f: f.get('abr', 0) or 0)
                        return best_audio['url']
                
                if 'url' in info:
                    return info['url']
                
                return None
            except Exception as e:
                print(f"Error getting fresh URL: {e}")
                return None



    # play next song
    def play_next(self, ctx):
        id = int(ctx.guild.id)
        if not self.is_playing[id]:
            return
        
        # if there is another song in queue
        if self.queueIndex[id] + 1 < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.queueIndex[id] += 1            # increment queue to play next song
            
            song = self.musicQueue[id][self.queueIndex[id]][0]
            
            # get fresh url
            source_url = self.get_fresh_url(song['video_id'])
            if not source_url:
                self.play_next(ctx)  # Skip to next song
                return
            
            
            message = self.now_playing_embed(ctx, song)
            coro = ctx.send(embed=message)    # coroutine
            fut = run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass

                
            self.vc[id].play(discord.FFmpegPCMAudio(
                source_url, executable=self.ffmpeg_path, **self.FFMPEG_OPTIONS), 
                after=lambda e: self.play_next(ctx))

        else:
            self.queueIndex[id] += 1
            self.is_playing[id] = False




    # play music
    async def play_music(self, ctx):
        id = int(ctx.guild.id)
        if self.queueIndex[id] < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.is_paused[id] = False
            
            await self.join_vc(ctx, self.musicQueue[id][self.queueIndex[id]][1])    # voice channel
            
            song = self.musicQueue[id][self.queueIndex[id]][0]
            
            #get fresh url
            source_url = self.get_fresh_url(song['video_id'])
            if not source_url:
                await ctx.send(f"Error playing: {song['title']}")
                self.is_playing[id] = False
                return
            
            message = self.now_playing_embed(ctx, song)
            await ctx.send(embed=message)
            
            
            # go to voice channel, play ffmpeg audio, then play next
            self.vc[id].play(discord.FFmpegPCMAudio(
                source_url, executable=self.ffmpeg_path, **self.FFMPEG_OPTIONS), 
                after=lambda e: self.play_next(ctx))
        else:
            await ctx.send("No songs in queue to be played")
            self.queueIndex[id] += 1
            self.is_playing[id] = False
    
    
    @commands.command(
        name="play",
        aliases=["pl"],
        help=""
    )
    async def play(self, ctx, *args):
        search = " ".join(args) # merge inputs into one string
        id = int(ctx.guild.id)
        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("Must be connected to a voice channel")
            return
        
        if not args:
            if len(self.musicQueue[id]) == 0:
                await ctx.send("There are no songs in queue to be played")
                return
            elif not self.is_playing[id]:
                if self.musicQueue[id] == None or self.vc[id] == None:
                    await self.play_music(ctx)
                else:
                    self.is_paused[id] = False
                    self.is_playing[id] = True
                    self.vc[id].resume()
            else:
                return
        else:
            song = self.extract_youtube(self.search_youtube(search)[0])
            if type(song) == type(True):
                await ctx.send("Could not download song. Incorrect format")
            else:
                self.musicQueue[id].append([song, userChannel])

                if not self.is_playing[id]:
                    await self.play_music(ctx)
                else:
                    message = "added to queue"
                    await ctx.send(message)


    # pause
    @commands.command(
        name = "pause",
        aliases = ["pa"],
        help=""
    )
    async def pause(self, ctx):
        id = int(ctx.guild.id)
        if not self.vc[id]:
            await ctx.send("Waalll-eee??? (There is no audio to be paused)")
        elif self.is_playing[id]:
            await ctx.send("Beep Beep! (paused)")
            self.is_playing[id] = False
            self.is_paused[id] = True
            self.vc[id].pause()
            
    # resume
    @commands.command(
        name = "resume",
        aliases = ["ra"],
        help=""
    )
    async def resume(self, ctx):
        id = int(ctx.guild.id)
        if not self.vc[id]:
            await ctx.send("Waalll-eee??? (There is no audio to resume)")
        elif not self.is_playing[id]:
            await ctx.send("Beep Beep! (resumed)")
            self.is_playing[id] = True
            self.is_paused[id] = False
            self.vc[id].resume()


    # join
    @commands.command(
        name = "join",
        aliases = ["j"],
        help=""
    )
    async def join(self, ctx):
        if ctx.author.voice:
            userChannel = ctx.author.voice.channel
            await self.join_vc(ctx, userChannel)
            await ctx.send(f"Waaall-ee!!! (joined {userChannel})")
        else:
            await ctx.send("Waaall-ee??? (need to be in voice channel)")
    
    
    # leave
    @commands.command(
        name = "leave",
        aliases = ["l"],
        help=""
    )
    async def leave(self, ctx):
        id = int(ctx.guild.id)
        self.is_playing[id] = self.is_paused[id] = False
        self.musicQueue[id] = []
        self.queueIndex[id] = 0
        if self.vc[id] != None:
            await ctx.send("Eeeevvv...aaa???")
            await self.vc[id].disconnect()
            self.vc[id] = None
        

# setup music function for bot
async def setup(bot):
    await bot.add_cog(Music(bot))