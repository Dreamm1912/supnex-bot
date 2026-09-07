"""Çekilişler: slash ile başlat, butonla katıl, otomatik çekiliş."""
import asyncio
import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from utils import db, embeds


class KatilmButonu(discord.ui.Button):
    def __init__(self, message_id: int) -> None:
        super().__init__(label="Çekilişe katıl", style=discord.ButtonStyle.success, custom_id=f"cekilis_katil_{message_id}")
        self.message_id = message_id

    async def callback(self, interaction: discord.Interaction) -> None:
        satir = db.get_giveaway(self.message_id)
        if not satir:
            await interaction.response.send_message(
                embed=embeds.uyari("Bu çekiliş çoktan bitti."), ephemeral=True
            )
            return
        db.add_entry(self.message_id, interaction.user.id)
        await interaction.response.send_message(
            embed=embeds.onay("Katıldın. Bol şans, şef."), ephemeral=True
        )


class CekilisView(discord.ui.View):
    def __init__(self, message_id: int) -> None:
        super().__init__(timeout=None)
        self.add_item(KatilmButonu(message_id))


class CekilisCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        asyncio.create_task(self._tarama_dongusu())

    async def _tarama_dongusu(self) -> None:
        try:
            await self.bot.wait_until_ready()
        except RuntimeError:
            return
        while True:
            try:
                vadesi_gelen = db.get_active_giveaways()
                for satir in vadesi_gelen:
                    await self._bitir(satir)
            except Exception:
                pass
            await asyncio.sleep(15)

    async def _bitir(self, satir) -> None:
        kanal = self.bot.get_channel(satir["channel_id"])
        db.mark_ended(satir["message_id"])
        if kanal is None:
            return
        try:
            mesaj = await kanal.fetch_message(satir["message_id"])
        except discord.NotFound:
            return
        kayitlar = [r["user_id"] for r in db.get_entries(satir["message_id"])]
        kazanan = self.bot.get_user(random.choice(kayitlar)) if kayitlar else None
        embed = embeds.taban(
            title="🎉 Çekiliş bitti!",
            description=f"Ödül: **{satir['prize']}**",
        )
        if kazanan:
            embed.description += f"\nKazanan: **{kazanan.mention}**"
            db.add_money(kazanan.id, 100)
            embed.add_field(name="Bonus", value="+🥔 100 para")
        else:
            embed.description += "\nKatılım yok. Boş çekiliş, cidden."
        try:
            await mesaj.edit(embed=embed, view=None)
            if kazanan:
                await mesaj.channel.send(f"Tebrikler {kazanan.mention}! **{satir['prize']}** kazandın", embed=embed)
        except discord.HTTPException:
            pass

    @app_commands.command(name="cekilis", description="Çekiliş başlat.")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(odul="Ödül ne?", sure="Saat cinsinden süre.")
    async def cekilis(
        self, interaction: discord.Interaction,
        odul: str, sure: float = 1.0
    ) -> None:
        if sure <= 0:
            await interaction.response.send_message(
                embed=embeds.hata("Pozitif bir süre ver."), ephemeral=True
            )
            return
        bitis = int(time.time() + sure * 3600)
        embed = embeds.taban(
            title="🎉 ÇEKİLİŞ",
            description=f"Ödül: **{odul}**\nBitiş: <t:{bitis}:R>\n\nKatılmak için butona bas.",
            color=embeds.ACCENT,
        )
        await interaction.response.defer()
        mesaj = await interaction.followup.send(embed=embed)
        db.create_giveaway(mesaj.id, interaction.channel_id, odul, bitis, interaction.user.id)
        view = CekilisView(mesaj.id)
        await mesaj.edit(view=view)