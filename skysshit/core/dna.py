import os
import discord as discord
from discord.ext import commands




class Bot(commands.Bot):

	def __init__(self, *args, **kwargs):
		super().__init__(command_prefix="_", *args, **kwargs)
		self.token = os.environ["TOKEN"]
	
	def run(self):
		client = discord.Client()
		token="NTczNzEzMjgzMDYwNTk2NzM2.XWWb_w.NwDtvLfv88Qr97pYH4dGylPB2YA"
		client.run(token)
