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
        self.embedRed = 0xFF0000
        self.embedGreen = 0x008000
        
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
    
    
    def added_song_embed(self, ctx, song):
        title = song['title']
        link = song['link']
        thumbnail = song['thumbnail']
        author = ctx.author
        avatar = author.avatar_url

        embed = discord.Embed(
            title="Song Added To Queue!",
            description=f'[{title}]({link})',
            colour=self.embedRed,
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f'Song added by: {str(author)}', icon_url=avatar)
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
            
    
    # get youtube title
    def get_youtube_title(self, videoID):
        params = {
            "format": "json",
            "url": "https://www.youtube.com/watch?v=%s" % videoID
        }
        url = "https://www.youtube.com/oembed"
        queryString = parse.urlencode(params)
        url = url + "?" + queryString
        with request.urlopen(url) as response:
            responseText = response.read()
            data = json.loads(responseText.decode())
            return data['title']
            

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
    
    
    # play command
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
        # if there are no inputs read
        if not args:
            #if no song in queue
            if len(self.musicQueue[id]) == 0:
                await ctx.send("There are no songs in queue to be played")
                return
            elif not self.is_playing[id]:       # if there is a song in queue but not playing
                if self.musicQueue[id] == None or self.vc[id] == None:
                    await self.play_music(ctx)
                else:       # resume song
                    self.is_paused[id] = False
                    self.is_playing[id] = True
                    self.vc[id].resume()
            else:
                return
        else:       # if there is arguments read
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
                    
                    
                    
    @commands.command(
        name="search",
        aliases=["find", "sr"],
        help="Provides a list of YouTube search results"
    )
    async def search(self, ctx, *args):
        search = " ".join(args)
        id = int(ctx.guild.id)
        
        if not args:
            await ctx.send("You must specify search terms!")
            return
        
        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("You must be connected to a voice channel.")
            return

        await ctx.send("Searching...")

        try:
            songTokens = self.search_youtube(search)
            
            embedText = ""
            for i, token in enumerate(songTokens):
                url = 'https://www.youtube.com/watch?v=' + token
                try:
                    name = self.get_youtube_title(token)
                    embedText += f"{i+1}. [{name}]({url})\n"
                except:
                    embedText += f"{i+1}. [Video]({url})\n"

            searchResults = discord.Embed(
                title="Search Results",
                description=embedText + "\n\nReply with a number (1-10) to select a song, or 'cancel' to cancel.",
                colour=self.embedRed
            )
            await ctx.send(embed=searchResults)
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                
                if msg.content.lower() == 'cancel':
                    await ctx.send("Search cancelled.")
                    return
                
                try:
                    chosenIndex = int(msg.content) - 1
                    if chosenIndex < 0 or chosenIndex >= len(songTokens):
                        await ctx.send("Invalid selection. Please choose a number between 1-10.")
                        return
                    
                    songRef = self.extract_youtube(songTokens[chosenIndex])
                    if type(songRef) == type(True):
                        await ctx.send("Could not download the song. Incorrect format, try different keywords.")
                        return
                    
                    self.musicQueue[id].append([songRef, userChannel])
                    
                    embedResponse = discord.Embed(
                        title=f"Option #{chosenIndex + 1} Selected",
                        description=f"[{songRef['title']}]({songRef['link']}) added to the queue!",
                        colour=self.embedRed
                    )
                    embedResponse.set_thumbnail(url=songRef['thumbnail'])
                    await ctx.send(embed=embedResponse)
                    
                    if not self.is_playing[id]:
                        await self.play_music(ctx)
                        
                except ValueError:
                    await ctx.send("Invalid input. Please enter a number between 1-10.")
                    return
                    
            except asyncio.TimeoutError:
                await ctx.send("Search timed out. Please try again.")
                
        except:
            await ctx.send("An error occurred during search")


    # show queue list
    @commands.command(
        name = "queue",
        aliases = ["q"],
        help = ""
    )
    async def queue(self, ctx):
        id = int(ctx.guild.id)
        returnValue = ""
        if self.musicQueue[id] == []:
            await ctx.send("There are no songs in queue!")
            return
        
        for i in range(self.queueIndex[id], len(self.musicQueue[id])):
            upNextSongs = len(self.musicQueue[id]) - self.queueIndex[id]
            if i > 5 + upNextSongs:
                break
            returnIndex = i - self.queueIndex[id] + 1
            if returnIndex == 1:        # first in index is playing
                returnIndex = f"Curently Playing: \n{returnIndex} - [{self.musicQueue[id][i][0]['title']}]({self.musicQueue[id][i][0]['link']})"    # syntax
            if returnIndex == 2:
                returnIndex = f"Next: \n{returnIndex} - [{self.musicQueue[id][i][0]['title']}]({self.musicQueue[id][i][0]['link']})"
                
            returnValue += f"{returnIndex} - [{self.musicQueue[id][i][0]['title']}]({self.musicQueue[id][i][0]['link']})\n"
            
            if returnValue == "":
                await ctx.send("There are no songs in queue at this time!")
                return
        
        queue = discord.Embed(
            title = "Current Queue",
            description = returnValue,
            colour = self.embedGreen
        )
        await ctx.send(embed=queue)
    
    
    # clear queue
    @commands.command(
        name = "clearQueue",
        aliases = ["clear", "cl"],
        help = ""
    )
    async def clear(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] != None and self.is_playing[id]:
            self.is_playing = self.is_paused = False
            self.vc[id].stop()
        
        if self.musicQueue[id] != []:
            await ctx.send("The music queue has been cleared.")
            self.musicQueue[id] = []
        self.queueIndex = 0

    
    
    @commands.command(
        name = "removeSong",
        aliases = ["rm"],
        help = ""
    )
    async def remove(self, ctx, index: int = 1):
        id = int(ctx.guild.id)
        if not ctx.author.voice:
            await ctx.send("Must be in a voice channel!")
            return
        
        if self.musicQueue[id] == []:
            await ctx.send("There are no songs to remove!")
            return
        
        if index < 1 or index > len(self.musicQueue[id]):
            await ctx.send(f"Invalid input! Please choose a number between 1 and {len(self.musicQueue[id])}")
            return
        
        # skips song when currently playing is removed
        if index == 1:
            if self.is_playing and self.vc[id]:
                self.vc[id].stop()
        else:       # for other songs chosen
            self.musicQueue[id].pop(index)      # pop out song regulary

        await ctx.send("Song removed from queue!")
        
            
            
    # skip current song      
    @ commands.command(
        name="skip",
        aliases=["sk"],
        help="Skips to the next song in the queue."
    )
    async def skip(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] == None:
            await ctx.send("You need to be in a voice channel to use this command.")
        elif self.queueIndex[id] >= len(self.musicQueue[id]) - 1:
            await ctx.send("There is no next song in the queue. Replaying current song.")
            self.vc[id].pause()
            await self.play_music(ctx)  
        elif self.vc[id] != None and self.vc[id]:
            self.vc[id].pause()
            self.queueIndex[id] += 1
            await self.play_music(ctx)
    

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