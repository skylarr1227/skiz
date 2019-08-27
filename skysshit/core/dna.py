from discord.ext import commands




class Bot(commands.Bot):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
	
	def run(self):
		super().run()
