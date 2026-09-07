"""Destek talebi: /destek modal ile özel kanal açar."""
import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds


class DestekModal(discord.ui.Modal, title="Destek talebi aç"):
    konu = discord.ui.TextInput(
        label="Neye ihtiyacın var?",
        style=discord.TextStyle.paragraph,
        placeholder="Sorunu 500 karakteri geçmeden anlat.",
        max_length=500,
    )

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction) -> None:
        sunucu = interaction.guild
        uye = interaction.user
        izinler = {
            sunucu.default_role: discord.PermissionOverwrite(view_channel=False),
            uye: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            sunucu.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        try:
            kanal = await sunucu.create_text_channel(
                name=f"talep-{uye.display_name[:20]}".replace(" ", "-").lower(),
                topic=f"{uye} tarafından açıldı",
                overwrites=izinler,
            )
        except discord.Forbidden as exc:
            await interaction.response.send_message(
                embed=embeds.hata(f"Kanal oluşturamıyorum: {exc}"), ephemeral=True
            )
            return
        embed = embeds.taban(
            title="Yeni talep",
            description=f"{uye.mention}, ekip yolda.\n\n> {self.konu.value}",
        )
        view = TalepKapatView(uye.id)
        await kanal.send(embed=embed, view=view)
        await interaction.response.send_message(
            embed=embeds.onay(f"Talep açıldı: {kanal.mention}"), ephemeral=True
        )


class TalepKapatView(discord.ui.View):
    def __init__(self, sahip_id: int) -> None:
        super().__init__(timeout=None)
        self.sahip_id = sahip_id

    @discord.ui.button(label="Talebi kapat", style=discord.ButtonStyle.danger)
    async def kapat(self, interaction: discord.Interaction, _) -> None:
        if interaction.user.id != self.sahip_id and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                embed=embeds.hata("Yalnızca ekip veya talep sahibi kapatabilir."), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=embeds.onay("Talep 5 saniye içinde kapanıyor...")
        )
        await interaction.channel.delete(reason="Talep kapatıldı.")


class DestekCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="destek", description="Destek talebi aç.")
    async def destek(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(DestekModal(self.bot))