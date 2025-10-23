import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os



load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()         # intents
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix='!', 
    intents=intents,
    reconnect=True  # Enable automatic reconnection
)

# setup music player function
async def setup_hook():
    await bot.load_extension('music')

bot.setup_hook = setup_hook


base_role = os.getenv("POPCORN_ROLE")           # role from env
master_role = os.getenv("MASTER_ROLE")

announcement_channel = os.getenv("ANNOUNCEMENT_CHANNEL_ID") # server announcement channel

@bot.event
async def on_ready():
    print(f"{bot.user.name} has booted up!")


# for when a member joins a server
@bot.event
async def on_member_join(member):
    if announcement_channel:
        await member.send(f"{member.name} has joined the server!")
    

@bot.event
async def on_message(message):
    if message.author == bot.user:      # prevent replying to own bot's message
        return

    # if "shit" in message.content.lower():
    #     await message.delete()
    #     await message.channel.send(f"{message.author.mention}, naughty naughty!")     # ping author with mention

    await bot.process_commands(message)     # continue handling all other messages being sent


# !hello
# @bot.command()
# async def hello(ctx):
#     await ctx.send(f"Hello {ctx.author.mention}!")
    

# assign role to user
@bot.command()
@commands.has_role(master_role)
async def assign(ctx, *, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=base_role)
    if role:
        await member.add_roles(role)
        await ctx.send(f"{member.mention} is now one of the {role}!")
    else:
        await ctx.send("Role does not exist")


@assign.error
async def assign_error(ctx, error):
    if isinstance(error, commands.MissingRole):          # if user is missing role
        await ctx.send("You do not have permission to use this command")


# remove role from user
@bot.command()
@commands.has_role(master_role)
async def remove(ctx, *, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=base_role)
    if role:
        await member.remove_roles(role)
        await ctx.send(f"{member.mention} is no longer one of the {role}!")
    else:
        await ctx.send("Role does not exist")
        
        
@remove.error
async def assign_error(ctx, error):
    if isinstance(error, commands.MissingRole):          # if user is missing role
        await ctx.send("You do not have permission to use this command")





        
        
@bot.command()
async def dm(ctx, member: discord.Member, *, msg):      # use *, message to get user input
    await member.send(f"{ctx.author.mention} said {msg}")
    await ctx.send(f"Message sent to {member.mention}!")



# reply command
# @bot.command()
# async def reply(ctx):
#     await ctx.reply("Wall-E says hi")
    
# poll
@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="New Poll", description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")



# run bot
def run_bot():
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)