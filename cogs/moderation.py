"""Moderasyon takımı: at, banla, banikaldir, sustur, uyar, uyarilar, temizle."""
import datetime

import discord
from discord import app_commands
from discord.ext import commands

from utils import db, embeds


def _mod_only():
    return app_commands.default_permissions(
        kick_members=True, ban_members=True
    )


class ModerasyonCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="at", description="Bir üyeyi sunucudan at.")
    @_mod_only()
    async def at(
        self, interaction: discord.Interaction, uye: discord.Member, sebep: str = "Sebep belirtilmedi"
    ) -> None:
        try:
            await uye.kick(reason=sebep)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=embeds.hata("O patatesi atacak gücüm yok."), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=embeds.onay(f"**{uye.mention}** atıldı. Sebep: `{sebep}`")
        )

    @app_commands.command(name="banla", description="Bir üyeyi Gölge Diyarına yolla.")
    @_mod_only()
    async def banla(
        self, interaction: discord.Interaction, uye: discord.Member, sebep: str = "Sebep belirtilmedi"
    ) -> None:
        try:
            await uye.ban(reason=sebep)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=embeds.hata("Onu banlayamıyorum, şef."), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=embeds.onay(f"**{uye.mention}** banlandı. Sebep: `{sebep}`")
        )

    @app_commands.command(name="banikaldir", description="Bir ruhu geri al.")
    @_mod_only()
    async def banikaldir(
        self, interaction: discord.Interaction, kullanici: str, sebep: str = "İtiraz kabul"
    ) -> None:
        try:
            kullanici_nesne = await self.bot.fetch_user(int(kullanici))
            await interaction.guild.unban(kullanici_nesne, reason=sebep)
        except (ValueError, discord.NotFound, discord.Forbidden) as exc:
            await interaction.response.send_message(
                embed=embeds.hata(f"Ban kaldırma başarısız: {exc}"), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=embeds.onay(f"`{kullanici_nesne}` banı kaldırıldı.")
        )

    @app_commands.command(name="sustur", description="Bir üyeyi bir süre sustur.")
    @_mod_only()
    @app_commands.describe(sure="Dakika cinsinden süre.")
    async def sustur(
        self, interaction: discord.Interaction, uye: discord.Member,
        sure: int = 10, sebep: str = "Sebep belirtilmedi"
    ) -> None:
        if not 1 <= sure <= 40320:
            await interaction.response.send_message(
                embed=embeds.hata("Süre 1 dakika ile 28 gün arasında olmalı."),
                ephemeral=True,
            )
            return
        sure_saniye = sure * 60
        bitis = discord.utils.utcnow() + datetime.timedelta(seconds=sure_saniye)
        await uye.timeout(bitis, reason=sebep)
        await interaction.response.send_message(
            embed=embeds.onay(f"**{uye.mention}** `{sure}dakika` susturuldu. Sebep: `{sebep}`")
        )

    @app_commands.command(name="uyar", description="Bir üyeye uyarı yaz.")
    @_mod_only()
    async def uyar(
        self, interaction: discord.Interaction, uye: discord.Member,
        sebep: str = "Sebep belirtilmedi"
    ) -> None:
        uyar_id = db.add_warn(interaction.guild.id, uye.id, interaction.user.id, sebep)
        toplam = len(db.get_warns(interaction.guild.id, uye.id))
        embed = embeds.uyari(
            f"⚠️ **{uye.mention}** uyarıldı.\n"
            f"Uyarı **#{toplam}** *(id `{uyar_id}`)*\nSebep: `{sebep}`"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="uyarilar", description="Bir üyenin uyarılarını listele.")
    async def uyarilar(
        self, interaction: discord.Interaction, uye: discord.Member
    ) -> None:
        satirlar = db.get_warns(interaction.guild.id, uye.id)
        if not satirlar:
            await interaction.response.send_message(
                embed=embeds.onay(f"**{uye.display_name}** temiz. Kayıtlı uyarı yok."),
                ephemeral=True,
            )
            return
        liste = "\n".join(
            f"`#{r['id']}` <t:{r['created_at']}:d> <@{r['moderator_id']}> — {r['reason']}"
            for r in satirlar[:10]
        )
        embed = embeds.taban(
            title=f"⚠️ {uye.display_name} için {len(satirlar)} uyarı",
            description=liste,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="uyartemizle", description="Bir üyenin uyarılarını sil.")
    @_mod_only()
    async def uyartemizle(
        self, interaction: discord.Interaction, uye: discord.Member
    ) -> None:
        silinen = db.clear_warns(interaction.guild.id, uye.id)
        await interaction.response.send_message(
            embed=embeds.onay(f"**{uye.display_name}** için **{silinen}** uyarı silindi.")
        )

    @app_commands.command(name="temizle", description="Toplu mesaj sil.")
    @_mod_only()
    @app_commands.describe(adet="Kaç mesaj silinecek (1-100).")
    async def temizle(self, interaction: discord.Interaction, adet: int = 10) -> None:
        adet = max(1, min(adet, 100))
        try:
            silinen = await interaction.channel.purge(limit=adet)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=embeds.hata("Burada temizleme yetkim yok."), ephemeral=True
            )
            return
        embed = embeds.onay(f"**{len(silinen)}** mesaj silindi. Zemin tertemiz.")
        await interaction.response.send_message(embed=embed)