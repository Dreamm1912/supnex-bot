"""Tater-independent formatting is cringe. Shared embed styling lives here."""
import time

import discord

BRAND = discord.Color.from_rgb(90, 200, 255)
ACCENT = discord.Color.from_rgb(168, 85, 247)
BAD = discord.Color.from_rgb(239, 68, 68)
GOOD = discord.Color.from_rgb(34, 197, 94)
WARN = discord.Color.from_rgb(245, 158, 11)

VERSION = "2.1"
FOOTER_ICON = "https://cdn.discordapp.com/attachments/0/0/supnex.png"


def taban(title: str | None = None, description: str | None = None,
          color: discord.Color = BRAND) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f"Supnex Bot v{VERSION} • buzdolabının arkasında pişti",
                     icon_url=FOOTER_ICON)
    embed.timestamp = discord.utils.utcnow()
    return embed


def onay(desc: str) -> discord.Embed:
    return taban(description=desc, color=GOOD)


def hata(desc: str) -> discord.Embed:
    return taban(description=desc, color=BAD)


def uyari(desc: str) -> discord.Embed:
    return taban(description=desc, color=WARN)


def stat(title: str, value: str, inline: bool = True) -> dict:
    return {"name": title, "value": value, "inline": inline}


def uptime(started: float) -> str:
    s = max(0, int(time.time() - started))
    d, rem = divmod(s, 86400)
    h, rem = divmod(rem, 3600)
    m, sec = divmod(rem, 60)
    return f"{d}d {h}h {m}m {sec}s"