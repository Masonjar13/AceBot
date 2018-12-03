import discord
from discord.ext import commands
from sqlalchemy import and_

from utils.database import GuildModule


class Modules:
	'''Manage modules.'''
	
	def __init__(self, bot):
		self.bot = bot
	
	async def __local_check(self, ctx):
		return (
			ctx.author.permissions_in(ctx.channel).manage_guild or
			await self.bot.is_owner(ctx.author)
		)
	
	@commands.command(aliases=['mods'])
	async def modules(self, ctx):
		'''List modules.'''
		
		mods = await GuildModule.query.where(
			GuildModule.guild_id == ctx.guild.id
		).gino.all()
		
		mod_list = []
		
		for modu in mods:
			mod_list.append(modu.module)
		
		e = discord.Embed(
			title='Modules',
			description='`.enable <module>` to enable a module.\n`.disable <module>` to disable.'
		)
		
		enabled = '\n'.join(mod_list)
		disabled = '\n'.join(filter(lambda mod: mod not in mod_list, self.bot._toggleable))
		
		e.add_field(name='Enabled', value=enabled if len(enabled) else 'None')
		e.add_field(name='Disabled', value=disabled if len(disabled) else 'None')
		
		await ctx.send(embed=e)
	
	@commands.command()
	async def modinfo(self, ctx, module: str):
		'''Show info about a module.'''
		
		lower = module.lower()
		if lower not in self.bot._toggleable:
			raise commands.CommandError(f'{lower} is not a toggleable module.')
		
		for cog in self.bot.cogs:
			if lower == cog.lower():
				module = cog
				break
		
		cog = self.bot.get_cog(module)
		cog_commands = self.bot.get_cog_commands(module)
		
		cmds = []
		cmds_brief = []
		
		for command in cog_commands:
			cmds.append(command.name)
			cmds_brief.append('-' if command.help is None else command.help)
		
		e = discord.Embed(title=cog.__class__.__name__, description=cog.__doc__)
		
		if len(cmds):
			e.add_field(name='Command', value='\n'.join(cmds))
			e.add_field(name='Description', value='\n'.join(cmds_brief))
		
		await ctx.send(embed=e)
	
	@commands.command()
	async def enable(self, ctx, module: str):
		'''Enable a module.'''
		
		module = module.lower()
		if module not in self.bot._toggleable:
			raise commands.CommandError(f'Module `{module}` is not a valid module.')
		
		if await self.bot.uses_module(ctx, module):
			return await ctx.send(f'Module `{module}` already enabled.')
		
		result = await GuildModule.create(
			guild_id=ctx.guild.id,
			module=module
		)
		
		if result is None:
			raise commands.CommandError(f'Failed enabling module `{module}`')
		
		await ctx.send(f'Module `{module}` successfully enabled.')
	
	@commands.command()
	async def disable(self, ctx, module: str):
		'''Disable a module.'''
		
		module = module.lower()
		if module not in self.bot._toggleable:
			raise commands.CommandError(f'{module} is not a valid module.')
		
		mod = await GuildModule.query.where(
			and_(
				GuildModule.guild_id == ctx.guild.id,
				GuildModule.module == module
			)
		).gino.first()
		
		if mod is None:
			return await ctx.send(f'Module `{module}` is not currently enabled.')
		
		if await mod.delete() == 'DELETE 1':
			await ctx.send(f'Module `{module}` disabled.')
		else:
			raise commands.CommandError(f'Failed disabling module `{module}`')


def setup(bot):
	bot.add_cog(Modules(bot))
