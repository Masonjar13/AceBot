import discord
from discord.ext import commands

import asyncio
import random

from datetime import datetime

from config import WOLFRAM_KEY, APIXU_KEY
from cogs.mixins import AceMixin


class General(AceMixin, commands.Cog):
	'''General commands.'''

	query_error = commands.CommandError('Query failed. Try again later.')

	@commands.command()
	async def flip(self, ctx):
		'''Flip a coin!'''

		msg = await ctx.send('\*flip\*')
		await asyncio.sleep(3)
		await msg.edit(content=random.choice(('Heads!', 'Tails!')))

	@commands.command()
	async def choose(self, ctx, *choices: commands.clean_content):
		'''Pick a random item from a list.'''

		if len(choices) < 2:
			raise commands.CommandError('At least two choices are necessary.')

		msg = await ctx.send(':thinking:')
		await asyncio.sleep(3)
		await msg.edit(content=random.choice(choices))

	@commands.command()
	@commands.cooldown(rate=3, per=10.0, type=commands.BucketType.user)
	async def number(self, ctx, number: int):
		'''Get a fact about a number!'''

		url = f'http://numbersapi.com/{number}?notfound=floor'

		async with ctx.channel.typing():
			try:
				async with self.bot.aiohttp.get(url) as resp:
					if resp.status != 200:
						raise self.query_error
					text = await resp.text()
			except asyncio.TimeoutError:
				raise self.query_error

		await ctx.send(text)

	@commands.command()
	async def fact(self, ctx):
		'''Get a random fact.'''

		fact = await self.db.fetchval('SELECT content FROM facts ORDER BY random()')
		await ctx.send(fact)

	@commands.command(name='8', aliases=['8ball'])
	async def ball(self, ctx, *, question):
		'''Classic Magic 8 Ball!'''
		responses = (
			# yes
			'It is certain', 'It is decidedly so', 'Without a doubt', 'Yes definitely', 'You may rely on it',
			'As I see it, yes', 'Most likely', 'Outlook good', 'Yes',
			# uncertain
			'Signs point to yes', 'Reply hazy try again', 'Ask again later', 'Better not tell you now',
			'Cannot predict now', 'Concentrate and ask again',
			# no
			"Don't count on it", 'My reply is no', 'My sources say no', 'Outlook not so good', 'Very doubtful'
		)

		await ctx.trigger_typing()
		await asyncio.sleep(3)
		await ctx.send(random.choice(responses))

	@commands.command(aliases=['guild'])
	@commands.bot_has_permissions(embed_links=True)
	async def server(self, ctx):
		"""Show various information about the server."""

		statuses = {
			discord.Status.online: 0,
			discord.Status.idle: 0,
			discord.Status.dnd: 0,
			discord.Status.offline: 0
		}

		for member in ctx.guild.members:
			for status in statuses:
				if member.status is status:
					statuses[status] += 1

		att = dict()

		att['Online'] = (
			f'{sum(member.status is not discord.Status.offline for member in ctx.guild.members)}'
			f'/{len(ctx.guild.members)}'
		)

		att['Owner'] = ctx.guild.owner.mention
		att['Channels'] = len(ctx.guild.text_channels) + len(ctx.guild.voice_channels)
		att['Region'] = str(ctx.guild.region)
		att['Created at'] = str(ctx.guild.created_at).split(' ')[0]

		e = discord.Embed(title=ctx.guild.name, description='\n'.join(f'**{a}**: {b}' for a, b in att.items()))
		e.set_thumbnail(url=ctx.guild.icon_url)
		e.set_footer(text=f'ID: {ctx.guild.id}')
		e.add_field(name='Status', value='\n'.join(str(status) for status in statuses))
		e.add_field(name='Users', value='\n'.join(str(count) for status, count in statuses.items()))

		await ctx.send(embed=e)

	@commands.command(aliases=['w', 'wa'])
	@commands.bot_has_permissions(embed_links=True)
	@commands.cooldown(rate=3, per=10.0, type=commands.BucketType.user)
	async def wolfram(self, ctx, *, query):
		'''Queries wolfram.'''

		if WOLFRAM_KEY is None:
			raise commands.CommandError('The host has not set up an API key.')

		params = {
			'appid': WOLFRAM_KEY,
			'i': query
		}

		async with ctx.channel.typing():
			try:
				async with self.bot.aiohttp.get('https://api.wolframalpha.com/v1/result', params=params) as resp:
					if resp.status != 200:
						raise self.query_error

					res = await resp.text()
			except asyncio.TimeoutError:
				raise self.query_error

		query = query.replace('`', '\u200b`')

		embed = discord.Embed()

		embed.add_field(name='Query', value=f'```{query}```')
		embed.add_field(name='Result', value=f'```{res}```', inline=False)

		embed.set_author(name='Wolfram Alpha', icon_url='https://i.imgur.com/KFppH69.png')
		embed.set_footer(text='wolframalpha.com')

		if len(query) + len(res) > 1200:
			raise commands.CommandError('Wolfram response too long.')

		await ctx.send(embed=embed)

	@commands.command()
	@commands.bot_has_permissions(embed_links=True)
	@commands.cooldown(rate=2, per=5.0, type=commands.BucketType.user)
	async def weather(self, ctx, *, location: str):
		'''Check the weather at a location.'''

		if APIXU_KEY is None:
			raise commands.CommandError('The host has not set up an API key.')

		url = 'http://api.apixu.com/v1/current.json'

		params = {
			'key': APIXU_KEY,
			'q': location
		}

		async with ctx.channel.typing():
			try:
				async with self.bot.aiohttp.get(url, params=params) as resp:
					if resp.status != 200:
						raise self.query_error
					data = await resp.json()
			except asyncio.TimeoutError:
				raise self.query_error

			location = data['location']

			locmsg = f'{location["name"]}, {location["region"]} {location["country"].upper()}'
			current = data['current']

			embed = discord.Embed(title=f'Weather for {locmsg}', description=f'*{current["condition"]["text"]}*')
			embed.set_thumbnail(url=f'http:{current["condition"]["icon"]}')
			embed.add_field(name='Temperature', value=f'{current["temp_c"]}°C | {current["temp_f"]}°F')
			embed.add_field(name='Feels Like', value=f'{current["feelslike_c"]}°C | {current["feelslike_f"]}°F')
			embed.add_field(name='Precipitation', value=f'{current["precip_mm"]} mm')
			embed.add_field(name='Humidity', value=f'{current["humidity"]}%')
			embed.add_field(name='Windspeed', value=f'{current["wind_kph"]} kph | {current["wind_mph"]} mph')
			embed.add_field(name='Wind Direction', value=current['wind_dir'])
			embed.timestamp = datetime.utcnow()

			await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(General(bot))
