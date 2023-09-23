import asyncio
import logging
import aiosqlite
import math
from config import DB

import discord
from discord import app_commands
from discord.ext import commands

allowed_users = [1031328980810350632, 270203531741495297, 231100147356925953]


class Songs(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"EmployeeBot.{self.__class__.__name__}")
        self.bot = bot

    @app_commands.command(
        name="suggest", description="Suggest a song for PoodleBoy to play on stream!"
    )
    @app_commands.describe(name="The name of the song")
    @app_commands.describe(artist="The name of the artist")
    async def suggest(self, interaction: discord.Interaction, name: str, artist: str):
        await interaction.response.defer(ephemeral=True)

        async with aiosqlite.connect(DB) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """INSERT INTO songs (name, artist) VALUES (?, ?)""",
                (name, artist),
            )
            await conn.commit()

        await interaction.followup.send(
            f'Thank you for suggesting "{name}" by {artist}!', ephemeral=True
        )

    @app_commands.command(
        name="removesong", description="Remove a song from the database"
    )
    async def removesong(self, interaction: discord.Interaction, name: str):
        if interaction.user.id not in allowed_users:
            await interaction.response.send_message(
                "Sorry, you don't have permission to run this command.", ephemeral=True
            )
            return

        async with aiosqlite.connect(DB) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """DELETE FROM songs WHERE name = ?""",
                (name,),
            )
            await conn.commit()

        await interaction.followup.send(
            f'Successfully removed "{name}" from the song list.'
        )

    @app_commands.command(
        name="songlist", description="This displays the list of suggested songs!"
    )
    async def songlist(self, interaction: discord.Interaction):
        if interaction.user.id not in allowed_users:
            await interaction.response.send_message(
                "Sorry, you don't have permission to run this command.", ephemeral=True
            )
            return
        
        async with aiosqlite.connect(DB) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """SELECT name, artist FROM songs ORDER BY name DESC""",
            )
            rows = await cursor.fetchall()

        if not rows:
            await interaction.response.send_message("There are no songs to display.", ephemeral=True)
            return

        sorted_items = sorted(rows, key=lambda x: x[1], reverse=True)
        per_page = 10

        embeds = []
        paginator = commands.Paginator(prefix="", suffix="")
        current_page = 0
        start_number = (current_page * per_page) + 1
        for i, (name, artist) in enumerate(sorted_items, 1):
            paginator.add_line(
                f"**{start_number + i - 1}.** **{name}** by *{artist}*"
            )
            if i % per_page == 0 or i == len(sorted_items):
                embed = discord.Embed(title="Songs to play on Stream", color=0x9146FF)
                embed.add_field(
                    name="Suggested Songs:", value=paginator.pages[current_page]
                )
                total_pages = math.ceil(len(sorted_items) / 10)
                embed.set_footer(text=f"Page {(current_page)+1}/{total_pages}")
                embeds.append(embed)
                paginator = commands.Paginator(prefix="", suffix="")

        if not embeds:
            await interaction.response.send_message("There are no songs to display.")
            return

        await interaction.response.send_message(embed=embeds[current_page])
        msg = await interaction.original_response()
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")

        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) in ["⬅️", "➡️"]

        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=60.0, check=check
                )
                if str(reaction.emoji) == "➡️" and current_page < len(embeds) - 1:
                    current_page += 1
                    await msg.edit(embed=embeds[current_page])
                elif str(reaction.emoji) == "⬅️" and current_page > 0:
                    current_page -= 1
                    await msg.edit(embed=embeds[current_page])

                await reaction.remove(user)
            except asyncio.TimeoutError:
                await msg.clear_reactions()
                break


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Songs(bot))