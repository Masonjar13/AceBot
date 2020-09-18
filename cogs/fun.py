import asyncio
import logging
from random import choice
from datetime import date, datetime

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands

from cogs.mixins import AceMixin
from config import APIXU_KEY, THECATAPI_KEY, WOLFRAM_KEY
from utils.time import pretty_timedelta

QUERY_ERROR = commands.CommandError('Query failed, try again later.')

WOOF_URL = 'https://random.dog/'
WOOF_HEADERS = dict(filter='mp4')

MEOW_URL = 'https://api.thecatapi.com/v1/images/search'
MEOW_HEADERS = {'x-api-key': THECATAPI_KEY}
MEOW_BREEDS = [
	'abys', 'aege', 'abob', 'acur', 'asho', 'awir', 'amau', 'amis', 'bali', 'bamb', 'beng', 'birm', 'bomb', 'bslo', 'bsho', 'bure', 'buri', 'cspa',
	'ctif', 'char', 'chau', 'chee', 'csho', 'crex', 'cymr', 'cypr', 'drex', 'dons', 'lihu', 'emau', 'ebur', 'esho', 'hbro', 'hima', 'jbob', 'java',
	'khao', 'kora', 'kuri', 'lape', 'mcoo', 'mala', 'manx', 'munc', 'nebe', 'norw', 'ocic', 'orie', 'pers', 'pixi', 'raga', 'ragd', 'rblu', 'sava',
	'sfol', 'srex', 'siam', 'sibe', 'sing', 'snow', 'soma', 'sphy', 'tonk', 'toyg', 'tang', 'tvan', 'ycho'
]

QUACK_URL = 'https://random-d.uk/api/v1/random'

FLOOF_URL = 'https://randomfox.ca/floof/'

COMPLIMENT_URL = 'https://complimentr.com/api'

log = logging.getLogger(__name__)


class Fun(AceMixin, commands.Cog):
	'''Fun commands!'''

	QUERY_EXCEPTIONS = (discord.HTTPException, aiohttp.ClientError, asyncio.TimeoutError, commands.CommandError)
	QUERY_ERROR = commands.CommandError('Query failed. Try again later.')

	@commands.command()
	async def flip(self, ctx):
		'''Flip a coin!'''

		msg = await ctx.send('*Flipping...*')
		await asyncio.sleep(3)
		await msg.edit(content=choice(('Heads!', 'Tails!')))

	@commands.command(aliases=['choice'])
	async def choose(self, ctx, *choices: commands.clean_content):
		'''Pick a random item from a list.'''

		choose_prompts = (
			'I have chosen',
			'I have a great feeling about',
			'I\'ve decided on',
			'Easy choice',
			'I think',
		)

		if len(choices) < 2:
			raise commands.CommandError('At least two choices are necessary.')

		selected = choice(choices)

		e = discord.Embed(
			description=selected
		)

		e.set_author(name=choice(choose_prompts) + ':', icon_url=self.bot.user.avatar_url)

		msg = await ctx.send(':thinking:')

		await asyncio.sleep(3)
		await msg.edit(content=None, embed=e)

	def _create_embed(self, url=None):
		e = discord.Embed(color=0x36393E)
		if url is not None:
			e.set_image(url=url)
		log.info(url)
		return e

	@commands.command(aliases=['dog'])
	@commands.cooldown(rate=6, per=10.0, type=commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def woof(self, ctx):
		'''Get a random doggo!'''

		async with ctx.typing():
			try:
				async with ctx.http.get(WOOF_URL + 'woof', params=WOOF_HEADERS) as resp:
					if resp.status != 200:
						raise QUERY_ERROR
					file = await resp.text()

				if file.lower().endswith('.webm'):
					log.info('woof got webm, reinvoking...')
					await ctx.reinvoke()
					return

				await ctx.send(WOOF_URL + file)
			except self.QUERY_EXCEPTIONS:
				raise QUERY_ERROR

	@commands.command(aliases=['cat'])
	@commands.cooldown(rate=6, per=10.0, type=commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def meow(self, ctx):
		'''Get a random cat image!'''

		if THECATAPI_KEY is None:
			raise commands.CommandError('The host has not set up an API key.')

		async with ctx.typing():
			try:
				async with ctx.http.get(MEOW_URL, headers=MEOW_HEADERS) as resp:
					if resp.status != 200:
						raise QUERY_ERROR
					json = await resp.json()

				data = json[0]
				img_url = data['url']

				await ctx.send(img_url)
			except self.QUERY_EXCEPTIONS:
				raise QUERY_ERROR

	@commands.command()
	@commands.cooldown(rate=6, per=10.0, type=commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def breed(self, ctx):
		'''Get an image and info about a random cat breed!'''

		if THECATAPI_KEY is None:
			raise commands.CommandError('The host has not set up an API key.')

		async with ctx.typing():
			try:
				async with ctx.http.get(MEOW_URL, params=dict(breed_ids=choice(MEOW_BREEDS)), headers=MEOW_HEADERS) as resp:
					if resp.status != 200:
						raise QUERY_ERROR
					json = await resp.json()

				data = json[0]

				img_url = data['url']

				e = self._create_embed(img_url)

				breed = data['breeds'][0]

				e.set_author(name=breed['name'], url=breed.get('wikipedia_url', None))
				e.description = breed['description']

				e.add_field(name='Origin', value=breed['origin'])
				e.add_field(name='Weight', value=breed['weight']['metric'] + ' kg')
				e.add_field(name='Life span', value=breed['life_span'] + ' years')

				await ctx.send(embed=e)
			except self.QUERY_EXCEPTIONS:
				raise QUERY_ERROR

	@commands.command(aliases=['duck'])
	@commands.cooldown(rate=6, per=10.0, type=commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def quack(self, ctx):
		'''Get a random duck image!'''

		async with ctx.typing():
			try:
				async with ctx.http.get(QUACK_URL) as resp:
					if resp.status != 200:
						raise QUERY_ERROR
					json = await resp.json()

				img_url = json['url']

				await ctx.send(img_url)
			except self.QUERY_EXCEPTIONS:
				raise QUERY_ERROR

	@commands.command(aliases=['fox'])
	@commands.cooldown(rate=6, per=10.0, type=commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def floof(self, ctx):
		'''~floooof~'''

		async with ctx.typing():
			try:
				async with ctx.http.get(FLOOF_URL) as resp:
					if resp.status != 200:
						raise QUERY_ERROR
					json = await resp.json()

				img_url = json['image']

				await ctx.send(img_url)
			except self.QUERY_EXCEPTIONS:
				raise QUERY_ERROR

	@commands.command()
	@commands.cooldown(rate=3, per=10.0, type=commands.BucketType.user)
	async def number(self, ctx, number: int):
		'''Get a fact about a number!'''

		url = f'http://numbersapi.com/{number}?notfound=floor'

		async with ctx.channel.typing():
			try:
				async with ctx.http.get(url) as resp:
					if resp.status != 200:
						raise QUERY_ERROR
					text = await resp.text()
			except asyncio.TimeoutError:
				raise QUERY_ERROR

		await ctx.send(text)

	@commands.command()
	async def fact(self, ctx):
		'''Get a random fact.'''

		fact = await self.db.fetchrow('SELECT * FROM facts ORDER BY random()')

		e = discord.Embed(
			title='Fact #{}'.format(fact.get('id')),
			description=fact.get('content')
		)

		await ctx.send(embed=e)

	@commands.command()
	async def compliment(self, ctx):
		'''Get a random compliment.'''
		
		async with ctx.channel.typing():
			try:
				async with ctx.http.get(COMPLIMENT_URL) as resp:
					if resp.status != 200:
						raise QUERY_ERROR
					json = await resp.json()
				
				text = json['compliment']
				
				await ctx.send(text)
			except self.QUERY_EXCEPTIONS:
				raise QUERY_ERROR

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
		await ctx.send('\N{BILLIARDS} ' + choice(responses))

	@commands.command(aliases=['guild'])
	@commands.bot_has_permissions(embed_links=True)
	async def server(self, ctx):
		"""Show various information about the server."""

		guild = ctx.guild

		desc = dict(
			ID=guild.id,
		)

		e = discord.Embed(
			title=guild.name,
			description='\n'.join('**{}**: {}'.format(key, value) for key, value in desc.items()),
			timestamp=guild.created_at
		)

		e.add_field(
			name='Owner',
			value=guild.owner.mention
		)

		e.add_field(
			name='Region',
			value=str(guild.region)
		)

		# CHANNELS

		channels = {
			discord.TextChannel: 0,
			discord.VoiceChannel: 0,
		}

		for channel in guild.channels:
			for channel_type in channels:
				if isinstance(channel, channel_type):
					channels[channel_type] += 1

		channel_desc = '{} {}\n{} {}'.format(
			'<:text_channel:635021087247171584>',
			channels[discord.TextChannel],
			'<:voice_channel:635021113134546944>',
			channels[discord.VoiceChannel]
		)

		e.add_field(
			name='Channels',
			value=channel_desc
		)

		# FEATURES

		if guild.features:
			e.add_field(
				name='Features',
				value='\n'.join('• ' + feature.replace('_', ' ').title() for feature in guild.features)
			)

		# MEMBERS

		statuses = dict(
			online=0,
			idle=0,
			dnd=0,
			offline=0
		)

		total_online = 0

		for member in guild.members:
			status_str = str(member.status)
			if status_str != "offline":
				total_online += 1
			statuses[status_str] += 1

		member_desc = '{} {} {} {} {} {} {} {}'.format(
			'<:online:635022092903120906>',
			statuses['online'],
			'<:idle:635022068290813952>',
			statuses['idle'],
			'<:dnd:635022045952081941>',
			statuses['dnd'],
			'<:offline:635022116462264320>',
			statuses['offline']
		)

		e.add_field(
			name='Members ({}/{})'.format(total_online, len(guild.members)),
			value=member_desc, inline=False
		)

		# SERVER BOOST

		boost_desc = 'Level {} - {} Boosts'.format(guild.premium_tier, guild.premium_subscription_count)

		if guild.premium_subscribers:
			# actually get the last premium subscriber. this list is always fucked
			booster = sorted(guild.premium_subscribers, key=lambda m: m.premium_since)[-1]
			boost_desc += '\nLast boost by {} {} ago'.format(
				booster.mention, pretty_timedelta(datetime.utcnow() - booster.premium_since)
			)

		e.add_field(
			name='Server boost',
			value=boost_desc
		)

		e.set_thumbnail(url=guild.icon_url)
		e.set_footer(text='Created')

		await ctx.send(embed=e)

	@commands.command(aliases=['w', 'wa'])
	@commands.cooldown(rate=3, per=10.0, type=commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
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
				async with ctx.http.get('https://api.wolframalpha.com/v1/result', params=params) as resp:
					if resp.status != 200:
						raise QUERY_ERROR

					res = await resp.text()
			except asyncio.TimeoutError:
				raise QUERY_ERROR

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
	@commands.cooldown(rate=2, per=5.0, type=commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def weather(self, ctx, *, location: str):
		'''Check the weather at a location.'''

		if APIXU_KEY is None:
			raise commands.CommandError('The host has not set up an API key.')

		url = 'http://api.weatherstack.com/current'

		params = {
			'access_key': APIXU_KEY,
			'query': location
		}

		async with ctx.channel.typing():
			try:
				async with ctx.http.get(url, params=params) as resp:
					if resp.status != 200:
						raise QUERY_ERROR
					data = await resp.json()
			except asyncio.TimeoutError:
				raise QUERY_ERROR

			if data.get('success', True) is False:
				raise commands.CommandError('Unable to find a location match.')

			location = data['location']
			current = data['current']

			observation_time = datetime.strptime(current['observation_time'], '%I:%M %p').time()

			e = discord.Embed(
				title='Weather for {}, {} {}'.format(location['name'], location['region'], location['country'].upper()),
				description='*{}*'.format(' / '.join(current["weather_descriptions"])),
				timestamp=datetime.combine(date.today(), observation_time),
			)

			e.set_footer(text='Observed')

			if current['weather_icons']:
				e.set_thumbnail(url=current['weather_icons'][0])

			e.add_field(name='Temperature', value='{}°C'.format(current['temperature']))
			e.add_field(name='Feels Like', value='{}°C'.format(current['feelslike']))
			e.add_field(name='Precipitation', value='{} mm'.format(current['precip']))
			e.add_field(name='Humidity', value='{}%'.format(current['humidity']))
			e.add_field(name='Wind Speed', value='{} kph'.format(current['wind_speed']))
			e.add_field(name='Wind Direction', value=current['wind_dir'])

			await ctx.send(embed=e)

	@commands.command()
	@commands.cooldown(rate=3, per=10.0, type=commands.BucketType.user)
	async def bill(self, ctx):
		'''Get a random Bill Wurtz video from his website.'''

		url = 'https://billwurtz.com/'

		async with ctx.typing():
			async with ctx.http.get(url + 'videos.html') as resp:
				if resp.status != 200:
					raise commands.CommandError('Request failed.')

				content = await resp.text()

			bs = BeautifulSoup(content, 'html.parser')
			tag = choice(bs.find_all('a'))

			await ctx.send(url + tag['href'])

	@commands.command()
	@commands.cooldown(rate=3, per=10.0, type=commands.BucketType.user)
	@commands.bot_has_permissions(embed_links=True)
	async def xkcd(self, ctx, *, id: int = None):
		'''Get a random or specified xkcd comic.'''

		if id is None:
			url = 'https://c.xkcd.com/random/comic/'
		else:
			url = 'https://xkcd.com/{}'.format(id)

		async with ctx.typing():
			async with ctx.http.get(url) as resp:
				if resp.status != 200:
					raise commands.CommandError('Request failed.')

				content = await resp.text()

				comic_url = str(resp.url)

			bs = BeautifulSoup(content, 'html.parser')
			brs = bs.find('div', attrs=dict(id='middleContainer'))
			img = brs.find('img')

			if img is None:
				await ctx.send(url)
				return

			e = discord.Embed(
				title=img['alt'],
				description=img['title']
			)

			e.set_image(url='https:' + img['src'])
			e.set_footer(text=comic_url.lstrip('https://').rstrip('/'), icon_url='https://i.imgur.com/onzWnfd.png')

			await ctx.send(embed=e)


def setup(bot):
	bot.add_cog(Fun(bot))
