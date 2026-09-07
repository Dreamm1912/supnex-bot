"""
Supnex Bot v2.1 — Türkçe, turbo fridge energy.
48 slash komut, 12 modül: bilgi, eğlence, ekonomi, seviye,
moderasyon, destek, rol menüsü, çekiliş, nitro generator, sahip.

Run with:
    python main.py          (token from .env)
"""
import asyncio
import logging
import os
import random
import time

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from cogs.economy import EkonomiCog
from cogs.extra import EkstraCog
from cogs.fun import EglenceCog
from cogs.generator import GeneratorCog
from cogs.giveaway import CekilisCog
from cogs.help import YardimCog
from cogs.info import BilgiCog
from cogs.leveling import SeviyeCog
from cogs.moderation import ModerasyonCog
from cogs.owner import SahipCog
from cogs.rolemenu import RolMenusuCog
from cogs.tickets import DestekCog

from utils import db, embeds

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s :: %(message)s",
)
log = logging.getLogger("supnex")

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    log.error("DISCORD_TOKEN missing. Set it in .env and retry.")
    raise SystemExit("Missing DISCORD_TOKEN in .env")

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

COGS = (
    BilgiCog, EglenceCog, EkonomiCog, SeviyeCog, ModerasyonCog,
    DestekCog, RolMenusuCog, CekilisCog, YardimCog, GeneratorCog,
    SahipCog, EkstraCog,
)

STATUSES = [
    ".gg/supnex",
    "/yardim • 48 komut",
    ".gg/supnex",
    "mutfak kaosu",
    ".gg/supnex",
    "XP için mesajlarını izliyor",
]


class SupnexBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix="!",
            intents=INTENTS,
            activity=discord.Activity(type=discord.ActivityType.watching, name=".gg/supnex"),
        )

    async def setup_hook(self) -> None:
        for cog in COGS:
            await self.add_cog(cog(self))
        self.loop.create_task(self._status_cycle())
        await self.tree.sync()
        log.info("Slash commands synced (%d).", len(self.tree.get_commands()))

    async def _status_cycle(self) -> None:
        await self.wait_until_ready()
        while True:
            status = random.choice(STATUSES)
            await self.change_presence(
                activity=discord.Activity(type=discord.ActivityType.watching, name=status)
            )
            await asyncio.sleep(60)


def main() -> None:
    bot = SupnexBot()
    _cooldowns: dict[int, float] = {}

    @bot.event
    async def on_ready() -> None:
        log.info("Logged in as %s (id=%s) in %d servers",
                 bot.user, bot.user.id, len(bot.guilds))
        await _ses_baglan(bot)

    @bot.event
    async def on_member_join(member: discord.Member) -> None:
        guild = member.guild
        if guild.system_channel is not None:
            embed = embeds.taban(
                title=f"{guild.name} sunucusuna hoş geldin",
                description=f"{member.mention}, buzdolabının kapısı senin için açıldı.\n\n"
                            "Neler yapabildiğimi görmek için `/yardim` yaz.",
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            try:
                await guild.system_channel.send(embed=embed)
            except discord.HTTPException:
                pass

    @bot.tree.error
    async def on_slash_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        log.error("Slash hatası %s: %s", interaction.command, error)
        embed = embeds.hata("Bu komut muz kabuğuna takıldı. Supnex'e bildir.")
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException:
            pass

    @bot.event
    async def on_message(message: discord.Message) -> None:
        if message.author.bot or not message.guild or not message.content:
            return
        now = time.time()
        if now - _cooldowns.get(message.author.id, 0) < 60:
            return
        _cooldowns[message.author.id] = now
        old_xp = db.get_xp(message.author.id)
        old_level, _, _ = db.level_from_xp(old_xp)
        new_xp = db.add_xp(message.author.id, random.randint(5, 15))
        new_level, _, _ = db.level_from_xp(new_xp)
        if new_level > old_level:
            embed = embeds.taban(
                title=f"Patatesin seviye atladı!",
                description=f"{message.author.mention} **seviye {new_level}** oldu",
                color=embeds.ACCENT,
            )
            await message.channel.send(embed=embed)

    @bot.tree.command(name="seskur", description="Botu bir ses kanalına bağlar + yayın rozetini açar.")
    async def seskur(interaction: discord.Interaction, kanal: discord.VoiceChannel) -> None:
        if interaction.user.id != int(os.getenv("OWNER_ID", "0")):
            await interaction.response.send_message(embed=embeds.hata("Bu komut yalnızca sahip içindir."), ephemeral=True)
            return
        db.set_ses(interaction.guild.id, kanal.id)
        await interaction.response.defer(ephemeral=True)
        try:
            for ses in kanal.guild.voice_channels:
                if bot.user.id in [m.id for m in ses.members]:
                    await ses.guild.voice_client.disconnect()
                    break
            await kanal.connect(self_deaf=True)
            await bot.change_presence(
                activity=discord.Streaming(name=".gg/supnex", url="https://www.twitch.tv/supnex")
            )
            await interaction.followup.send(
                embed=embeds.onay(f"🟢 {kanal.mention} kanalına bağlandım.\nRozet: **LIVE / Yayında**"), ephemeral=True
            )
        except Exception as hata:
            await interaction.followup.send(embed=embeds.hata(f"Bağlanamadım: {hata}"), ephemeral=True)

    @bot.tree.command(name="sestemizle", description="Botu sesten çıkarır ve yayın rozetini kapatır.")
    async def sestemizle(interaction: discord.Interaction) -> None:
        if interaction.user.id != int(os.getenv("OWNER_ID", "0")):
            await interaction.response.send_message(embed=embeds.hata("Bu komut yalnızca sahip içindir."), ephemeral=True)
            return
        db.set_ses(interaction.guild.id, None)
        for ses in interaction.guild.voice_channels:
            if bot.user.id in [m.id for m in ses.members]:
                await ses.guild.voice_client.disconnect()
                break
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name=".gg/supnex")
        )
        await interaction.response.send_message(embed=embeds.onay("🔴 Sesten çıktım, rozet kapalı."), ephemeral=True)

    bot.run(TOKEN)


async def _ses_baglan(bot: commands.Bot) -> None:
    """Kayıtlı ses kanalı varsa bağlan ve streaming rozetini aç."""
    for guild in bot.guilds:
        kanal_id = db.get_ses(guild.id)
        if not kanal_id:
            continue
        kanal = guild.get_channel(kanal_id)
        if not kanal:
            continue
        try:
            for ses in guild.voice_channels:
                if bot.user.id in [m.id for m in ses.members]:
                    await ses.guild.voice_client.disconnect()
                    break
            await kanal.connect(self_deaf=True)
            await bot.change_presence(
                activity=discord.Streaming(name=".gg/supnex", url="https://www.twitch.tv/supnex")
            )
            log.info("Sese bağlandı: %s/%s (streaming açık)", guild.name, kanal.name)
        except Exception as hata:
            log.error("Ses bağlantı hatası (%s): %s", guild.name, hata)


if __name__ == "__main__":
    main()