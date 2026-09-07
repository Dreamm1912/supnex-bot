"""Mesajlarda otomatik XP + /seviyem ve /xpsirala."""
import discord
from discord import app_commands
from discord.ext import commands

from utils import db, embeds


class SeviyeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="seviyem", description="Patates seviye kartın.")
    async def seviyem(
        self, interaction: discord.Interaction, uye: discord.Member | None = None
    ) -> None:
        uye = uye or interaction.user
        xp = db.get_xp(uye.id)
        seviye, mevcut, gerekli = db.level_from_xp(xp)
        yuzde = min(100, round(mevcut / gerekli * 100)) if gerekli else 100
        bar = "█" * (yuzde // 10) + "░" * (10 - yuzde // 10)
        embed = embeds.taban(
            title=f"{uye.display_name} seviyesi",
            description=f"Seviye **{seviye}** • **{xp}** toplam XP",
        )
        embed.add_field(name="İlerleme", value=f"{bar} `{mevcut}/{gerekli}` (%{yuzde})", inline=False)
        embed.set_thumbnail(url=uye.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="xpsirala", description="En yüksek XP'ler.")
    async def xpsirala(self, interaction: discord.Interaction) -> None:
        satirlar = db.top_xp(10)
        satirlar = [s for s in satirlar if self.bot.get_user(s["user_id"]) or interaction.guild.get_member(s["user_id"])][:10]
        satirlar_liste = []
        madalyalar = ["🥇", "🥈", "🥉"]
        for i, satir in enumerate(satirlar):
            kullanici = self.bot.get_user(satir["user_id"]) or interaction.guild.get_member(satir["user_id"])
            isim = kullanici.display_name if kullanici else f"<@{satir['user_id']}>"
            seviye, _, _ = db.level_from_xp(satir["xp"])
            madalya = madalyalar[i] if i < 3 else f"`{i + 1}.`"
            satirlar_liste.append(f"{madalya} **{isim}** — Lv **{seviye}** ({satir['xp']}xp)")
        embed = embeds.taban(
            title="📈 Sunucu XP sıralaması",
            description="\n".join(satirlar_liste) or "Henüz kimse XP almamış.",
        )
        await interaction.response.send_message(embed=embed)