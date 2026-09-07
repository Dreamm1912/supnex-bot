"""Kendi kendine rol seçici: /rolmenusu <rol> [rol...]."""
import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds


class RolMenusu(discord.ui.View):
    def __init__(self, roller: list[discord.Role]) -> None:
        super().__init__(timeout=None)
        self.roller = roller
        self.add_item(RolSecici(roller))

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        await interaction.response.send_message(
            embed=embeds.hata(f"Rol menüsü hatası: {error}"), ephemeral=True
        )


class RolSecici(discord.ui.Select):
    def __init__(self, roller: list[discord.Role]) -> None:
        secenekler = [
            discord.SelectOption(
                label=rol.name[:80],
                value=str(rol.id),
                description=f"{rol.name[:50]} rolünü aç/kapat",
            )
            for rol in roller[:25]
        ]
        super().__init__(
            placeholder="Rol seçmek için tıkla...",
            min_values=0,
            max_values=len(secenekler),
            options=secenekler,
        )
        self.roller = roller

    async def callback(self, interaction: discord.Interaction) -> None:
        secilen = {int(v) for v in self.values}
        eklenecek = []
        silinecek = []
        uye = interaction.user
        for rol in self.roller:
            if rol.id in secilen:
                if rol not in uye.roles:
                    eklenecek.append(rol)
            else:
                if rol in uye.roles:
                    silinecek.append(rol)
        try:
            await uye.add_roles(*eklenecek)
            await uye.remove_roles(*silinecek)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=embeds.hata("Bazı rollere dokunamıyorum."), ephemeral=True
            )
            return
        parcalar = []
        if eklenecek:
            parcalar.append(f"Eklendi: {', '.join(r.mention for r in eklenecek)}")
        if silinecek:
            parcalar.append(f"Çıkarıldı: {', '.join(r.mention for r in silinecek)}")
        await interaction.response.send_message(
            embed=embeds.onay("\n".join(parcalar) or "Hiçbir şey değişmedi, şef."),
            ephemeral=True,
        )


class RolMenusuCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="rolmenusu", description="Kendi kendine rol paneli kur.")
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(roller="Virgülle ayrılmış rol adları veya etiketleri.")
    async def rolmenusu(self, interaction: discord.Interaction, roller: str) -> None:
        istenen = [r.strip().lstrip("<@&").rstrip(">") for r in roller.split(",") if r.strip()]
        havuz = {r.name.lower(): r for r in interaction.guild.roles}
        havuz.update({str(r.id): r for r in interaction.guild.roles})
        eslesen = []
        for isim in istenen:
            rol = havuz.get(isim.lower()) or havuz.get(isim)
            if rol and rol not in eslesen:
                eslesen.append(rol)
        if not eslesen:
            await interaction.response.send_message(
                embed=embeds.hata("Listenle eşleşen rol yok."), ephemeral=True
            )
            return
        view = RolMenusu(eslesen)
        embed = embeds.taban(
            title="Rol menüsü",
            description="Açılır menüden rolleri aç/kapat.",
        )
        await interaction.response.send_message(embed=embed, view=view)