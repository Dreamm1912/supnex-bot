"""Sahip komutları. OWNER_ID (sahip ID) ile korunur."""
import os

import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds

OWNER_ID = int(os.getenv("OWNER_ID", "0"))


class SahipCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _sahip_mi(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == OWNER_ID

    @app_commands.command(name="sunucular", description="Botun olduğu sunucuları listele. (sahip)")
    async def sunucular(self, interaction: discord.Interaction) -> None:
        if not self._sahip_mi(interaction):
            await interaction.response.send_message(
                embed=embeds.hata("Sadece sahibe özel, şef."), ephemeral=True
            )
            return
        satirlar = "\n".join(
            f"`{g.id}` • {g.name} ({g.member_count} üye)"
            for g in sorted(self.bot.guilds, key=lambda x: x.member_count, reverse=True)
        ) or "Henüz hiçbir sunucuda değil."
        await interaction.response.send_message(
            embed=embeds.taban(title="Sunucular", description=satirlar)
        )

    @app_commands.command(name="kapat", description="Botu kapat. (sahip)")
    async def kapat(self, interaction: discord.Interaction) -> None:
        if not self._sahip_mi(interaction):
            await interaction.response.send_message(
                embed=embeds.hata("Sadece sahibe özel, şef."), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=embeds.onay("Buzdolabı kapanıyor. İyi geceler, şef.")
        )
        await self.bot.close()

    @app_commands.command(name="sahip", description="Sahip kartını göster.")
    async def sahip(self, interaction: discord.Interaction) -> None:
        sahip = self.bot.get_user(OWNER_ID)
        embed = embeds.taban(title=f"Run by {sahip.display_name if sahip else OWNER_ID}")
        embed.set_footer(text="Supnex Bot v2.1")
        await interaction.response.send_message(embed=embed)