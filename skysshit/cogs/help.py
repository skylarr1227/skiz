import typing
from random import choice
from typing import Iterable

import discord
from discord.ext import commands as _commands

import libneko
from libneko import embeds, strings, other
from libneko.pag import navigator

ZERO_WIDTH_SPACE = "\N{ZERO WIDTH SPACE}"
EM_SPACE = "\N{EM SPACE}"
EM_DASH = "\N{EM DASH}"


class Help(_commands.Cog):
    """
    Parameters:
        dm:
            Defines if the help message should be send thought dm or not. Default is set to False
        colour:
            Defines the list of colors that the help command will cycle through when making the
            command list or randomly choose from when making a specific help page.
        color:
            An alias for the :attr:`colour` for the 'americans'
        commands_per_page:
            Number of commands to show per page.
        no_brief_default:
            A function that takes a command as an argument and outputs the value to use for the brief
            field if no actual brief is specified. By default, it outputs ``Usage: <command usage string>``.

    Note:
        If the command in executed in dm, the command will act as if the dm value is set to True
    """

    def __init__(
        self,
        dm: bool = False,
        colors: Iterable[int] = None,
        colours: Iterable[int] = None,
        commands_per_page: int = 10,
        no_brief_default: typing.Callable[
            [_commands.Command], str
        ] = lambda p, c: f"Usage: `{p}{c.qualified_name} {c.signature}`",
    ):
        self.dm = dm
        self.commands_per_page = commands_per_page
        self.no_brief_default = no_brief_default

        if colours and colors:
            raise TypeError("You must only provide either one of the colour parameters!")
        if colors:
            colours = colors
        if colours:
            self.hex_values = []
            for c in colours:
                try:
                    if c.startswith("#"):
                        c = c[1:]
                    self.hex_values.append(int(c, 16))
                except ValueError:
                    continue
        else:
            self.hex_values = None

    def make_help_page(self, cmd: typing.Union[_commands.Command, _commands.Group], prefix: str):
        """
        Makes a help page for the given command with the given prefix.
        """

        if self.hex_values:
            colour = choice(self.hex_values)
        else:
            colour = other.random_colour()

        title = f"`{cmd.qualified_name}` help page"
        if isinstance(cmd, _commands.Group):
            title = f"**[GROUP]** `{cmd.qualified_name}` help page"

        em = embeds.Embed(title=title, description=cmd.brief, colour=colour, timestamp=None)

        em.add_field(name="Usage", value=f"```md\n{prefix}{cmd.qualified_name} {cmd.signature}```")

        em.add_field(name="Full Description", value=f"{cmd.help or '`No description set yet`'}")
        em.add_field(name="Category", value=f"`{cmd.cog_name}`" or "`Unsorted`")

        if isinstance(cmd, _commands.Group):
            child_commands_short_info = {
                f"\N{BULLET} `{c.name}` - {c.brief}"
                for c in sorted(cmd.commands, key=str)
                if isinstance(c, _commands.Command)
            }
            child_groups_short_info = {
                f"\N{BULLET} `{c.name}` - {c.brief}"
                for c in sorted(cmd.commands, key=str)
                if isinstance(c, _commands.Group)
            }
            if child_groups_short_info:
                em.add_field(
                    name="Subgroups", value=strings.pretty_list(child_groups_short_info, sep="\n")
                )
            em.add_field(
                name="Subcommands", value=strings.pretty_list(child_commands_short_info, sep="\n")
            )
        return em

    def make_help_pages(self, ctx: _commands.Context, commands: list, pages: list, cog: str = None, step: int = 10):
        """
        Makes pages (sorted by cogs) for the command iterable given.
        """

        cursor = 0

        title = "**Unsorted** Category"
        if cog:
            title = f"**{cog}** Category"

        for i in range(0, len(commands), step):
            if self.hex_values:
                if cursor <= len(self.hex_values) - 1:
                    colour = self.hex_values[cursor]
                else:
                    colour = other.random_color()
                    cursor = 0
            else:
                colour = other.random_colour()

            quest = "\N{BLACK QUESTION MARK ORNAMENT}"

            page = embeds.Embed(title=title, colour=colour, timestamp=None)
            page.set_author(
                name=f"{quest} {ctx.bot.user.name}'s Commands {quest}",
                icon_url=str(ctx.bot.user.avatar_url),
            )
            page.set_footer(
                icon_url=str(ctx.bot.user.avatar_url), text="Only commands you can run are visible"
            )

            next_commands = commands[i : i + 10]
            for cmd in next_commands:
                name = cmd.name
                if isinstance(cmd, _commands.Group):
                    name = "**[GROUP]** " + cmd.name

                brief = cmd.brief or self.no_brief_default(ctx.prefix, cmd)

                page.add_field(name=name, value=f"{ZERO_WIDTH_SPACE}{EM_SPACE}{brief.lstrip()}")
            pages.append(page)

            cursor += 1

    @libneko.command(aliases=["h"], brief="Shows this page")
    async def help(self, ctx: _commands.Context, *, query: str = None):
        """
        Shows a brief paginated list of all commands available in this bot.
        You can also specify a command to see more indepth details about it.
        """

        channel = ctx.channel
        if self.dm:
            if ctx.guild is not None:
                await ctx.send(
                    embed=embeds.Embed(
                        description="Commands have been sent to your DM", timestamp=None
                    )
                )
                channel = ctx.author

        all_commands: typing.List[_commands.Command] = [*sorted(ctx.bot.commands, key=str)]
        filtered_commands: typing.List[typing.Union[_commands.Command, _commands.Group]] = []

        for cmd in all_commands:
            try:
                if await cmd.can_run(ctx) and not cmd.hidden and cmd.enabled:
                    filtered_commands.append(cmd)
            except Exception:
                continue
        if not query:
            pages = []
            if ctx.bot.cogs:
                for cog in ctx.bot.cogs:
                    filtered_cog_cmds = [
                        c for c in ctx.bot.get_cog(cog).get_commands() if c in filtered_commands
                    ]
                    self.make_help_pages(
                        ctx,
                        sorted(filtered_cog_cmds, key=str),
                        pages,
                        cog=cog,
                        step=self.commands_per_page,
                    )
                filtered_unsorted_cmds = [c for c in filtered_commands if not c.cog_name]
                self.make_help_pages(
                    ctx, filtered_unsorted_cmds, pages, step=self.commands_per_page
                )
            else:
                self.make_help_pages(ctx, filtered_commands, pages, step=self.commands_per_page)
            nav = navigator.EmbedNavigator(pages=pages, ctx=ctx)
            nav.channel = channel
            nav.start()

        else:
            searched_command = ctx.bot.get_command(query)
            if searched_command is None or (
                searched_command.root_parent is not None
                and searched_command.root_parent not in filtered_commands
            ):
                return await ctx.send(
                    embed=embeds.Embed(
                        description=":octagonal_sign: That isn't a valid command!",
                        colour=discord.Colour.red(),
                        timestamp=None,
                    )
                )

            nav = navigator.EmbedNavigator(
                pages=[self.make_help_page(cmd=searched_command, prefix=ctx.prefix)], ctx=ctx
            )
            nav.channel = channel
            nav.start()


def setup(bot):
    """Add the cog to the bot directly. Enables this to be loaded as an extension."""
    try:
        bot.remove_command("help")
    finally:
        bot.add_cog(Help())

def teardown(bot):
    """Remove the cog and load the default help on extension unload"""
    try:
        bot.remove_cog("Help")
    finally:
        bot.help_command = _commands.DefaultHelpCommand()
