#importing required modules
import os
import discord
from discord.ext import commands
 
#enabling all intents 
intent = discord.Intents().all()
#deciding when the bot responds
bot = commands.Bot(command_prefix="!", intents=intent)
  
#first event :logging in
@bot.event
async def on_ready():
  #displaying that the bot has logged in
  print("successful login as {0.user}".format(bot))
 
#defining the class for creating a button
class Invitebutton(discord.ui.View):
  #creating the button function
  def __init__(self, inv: str):
    super().__init__()
    #collecting the url of the current server
    self.inv=inv
    self.add_item(discord.ui.Button(label="Invite link", url=self.inv))
  #features of the button
  @discord.ui.button(label="Invite", style=discord.ButtonStyle.blurple)
  async def invite(self, interaction: discord.Interaction , button : discord.ui.Button):
    await interaction.response.send_message(self.inv,ephemeral=True)
 
#defining command of the bot
@bot.command()
async def invite(ctx: commands.Context):
  inv=await ctx.channel.create_invite()
  await ctx.send("click to invite!", view=Invitebutton(str(inv)))
  
#getting the secret token
bot.run(os.getenv('token'))