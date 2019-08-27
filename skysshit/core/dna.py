import os

from discord.ext import commands




class Bot(commands.Bot):

	def __init__(self, *args, **kwargs):
		super().__init__(command_prefix="s!", *args, **kwargs)
		self.token = os.environ["TOKEN"]
	
	def run(self):
		super().run(token=self.token)
