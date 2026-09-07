"""Saf kaos: zar, fal, yazı-tura, taş-makas, şaka, söz, meme."""
import random

import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds

SAKALAR = [
    "Patates neden karşıdan karşıya geçti? Buzdolabından kaçmak için. Yine.",
    "CPU'ma fıkra anlattım... şimdi sorunu var.",
    "Programcılar neden karanlık modu sever? Çünkü ışık böcekleri çeker.",
    "On çeşit insan vardır: binary bilenler ve bilmeyenler.",
    "Geliştirici neden iflas etti? Çok fazla önbellek masrafı.",
    "Bir SQL sorgusu bara girer, iki masa görür ve 'Size katılabilir miyim?' der.",
    "Neden JavaScript'i programcı üzüldü? `null` hislerini bilmiyordu.",
    "Sana bir UDP fıkrası anlatırdım ama anlamayabilirsin.",
    "Pythoncu neden gözlük takar? C'yi göremez.",
    "Kırık kalemler anlamsız.",
]

SOZLER = [
    "absolute potato sana, Sam.",
    "Buzdolabı kapalı. Mutfak bizim.",
    "üç kelime gir, üç yüz satır çıksın.",
    "no cap, sadece çalışıyor.",
    "herkes pişirdi, kimse yanmadı.",
    "2019'dan beri çürüyorum, bunu bile ben bilirim.",
    "şef patates derse? patates. ",
    "kod bir araçtır, bir beyan değil.",
    "inşa et, gönder, sıradakini söyle.",
]

SEKIZTOP = [
    "Kesinlikle.", "Şüphesiz.", "Evet — absolute potato.",
    "Büyük ihtimalle.", "İyi görünüyor.", "Sonra tekrar sor.",
    "Şu an tahmin edemem.", "Kaynaklarım hayır diyor.", "Buna güvenme.",
    "Çok şüpheli.", "Kanka, hayır.", "Kesinlikle hayır, şef.",
]


class EglenceCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="zar", description="N yüzlü bir zar at.")
    async def zar(self, interaction: discord.Interaction, yuz: int = 6) -> None:
        yuz = max(2, min(yuz, 1_000_000))
        sonuc = random.randint(1, yuz)
        await interaction.response.send_message(
            embed=embeds.taban(
                title="🎲",
                description=f"Attın: **{sonuc}** / {yuz}",
            )
        )

    @app_commands.command(name="zarlar", description="5 klasik zar at.")
    async def zarlar(self, interaction: discord.Interaction) -> None:
        zarlar = [random.randint(1, 6) for _ in range(5)]
        await interaction.response.send_message(
            embed=embeds.taban(
                title="🎲 " + " ".join(f"`{z}`" for z in zarlar),
                description=f"Toplam: **{sum(zarlar)}**",
            )
        )

    @app_commands.command(name="yazitura", description="Yazı mı tura mı.")
    async def yazitura(self, interaction: discord.Interaction) -> None:
        sonuc = random.choice(["Yazı", "Tura"])
        await interaction.response.send_message(
            embed=embeds.taban(description=f"🪙 **{sonuc}**")
        )

    @app_commands.command(name="8top", description="Bilge patatese sor.")
    async def sekiztop(self, interaction: discord.Interaction, soru: str) -> None:
        await interaction.response.send_message(
            embed=embeds.taban(
                title="🎱 Bilge Patates",
                description=f"> {soru}\n\n**{random.choice(SEKIZTOP)}**",
            )
        )

    @app_commands.command(name="sec", description="Birçok seçenekten birini seç.")
    async def sec(
        self, interaction: discord.Interaction, secenekler: str
    ) -> None:
        parcalar = [p.strip() for p in secenekler.split(",") if p.strip()]
        if len(parcalar) < 2:
            await interaction.response.send_message(
                embed=embeds.hata("Bana virgülle ayrılmış 2+ seçenek ver."),
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=embeds.taban(
                description=f"🤔 Ben **{random.choice(parcalar)}** seçiyorum"
            )
        )

    @app_commands.command(name="tas_makas", description="Taş, makas, kağıt.")
    async def tas_makas(self, interaction: discord.Interaction, secim: str) -> None:
        secim = secim.lower().strip()
        if secim not in {"tas", "makas", "kagit"}:
            await interaction.response.send_message(
                embed=embeds.hata("tas, makas veya kagit yaz."), ephemeral=True
            )
            return
        bot_secimi = random.choice(["tas", "makas", "kagit"])
        yener = {"tas": "makas", "kagit": "tas", "makas": "kagit"}
        if secim == bot_secimi:
            sonuc = "Berabere. Buzdolabı enerjisi."
        elif yener[secim] == bot_secimi:
            sonuc = "Kazandın. Absolute potato."
        else:
            sonuc = "Kazandım. Patates üstünlüğü."
        await interaction.response.send_message(
            embed=embeds.taban(
                title=f"🤜 {secim} vs {bot_secimi} 🤛",
                description=f"**{sonuc}**",
            )
        )

    @app_commands.command(name="saka", description="Taze buzdolabı mizahı.")
    async def saka(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=embeds.taban(description=random.choice(SAKALAR))
        )

    @app_commands.command(name="soz", description="Bilge patatesten kelamlar.")
    async def soz(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=embeds.taban(
                description=f"“{random.choice(SOZLER)}”",
            )
        )

    @app_commands.command(name="meme", description="Hattan taze bir meme (internet gerek).")
    async def meme(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        try:
            import requests
        except ImportError:
            await interaction.followup.send(
                embed=embeds.hata("Bu sistemde `requests` yok."), ephemeral=True
            )
            return
        try:
            r = requests.get(
                "https://meme-api.com/gimme",
                params={"nsfw": "false", "sub": "memes"},
                timeout=8,
                headers={"User-Agent": "SupnexBot/2.1"},
            )
            r.raise_for_status()
            veri = r.json()
            embed = embeds.taban(title=veri.get("title", "taze meme"), description=veri.get("postLink", ""))
            embed.set_image(url=veri.get("url", ""))
            embed.set_author(name=f"r/{veri.get('subreddit', 'memes')}")
        except Exception:
            embed = embeds.hata("Meme hattı kapalı. Bir saniye sonra tekrar dene.")
        await interaction.followup.send(embed=embed)