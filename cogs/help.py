"""//yardim — kategori seçici + sayfalı komut rehberi."""
import random

import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds
from utils.paginator import Paginator

CATEGORIES: dict[str, tuple[str, tuple[str, ...]]] = {
    "bilgi": (
        "ℹ️ Bilgi",
        ("ping", "uptime", "botbilgi", "kullanicibilgi", "sunucubilgi",
         "avatar", "sunucuikon", "tekrarla", "renk", "embed", "roller"),
    ),
    "eglence": (
        "🎉 Eğlence",
        ("zar", "zarlar", "yazitura", "8top", "sec", "tas_makas", "saka", "soz", "meme"),
    ),
    "ekonomi": (
        "🥔 Ekonomi",
        ("bakiye", "gonder", "gunluk", "calis", "balik", "slot", "siralama"),
    ),
    "seviye": (
        "📈 Seviye",
        ("seviyem", "xpsirala"),
    ),
    "moderasyon": (
        "🛠️ Moderasyon",
        ("at", "banla", "banikaldir", "sustur", "uyar", "uyarilar", "uyartemizle", "temizle"),
    ),
    "servis": (
        "🎫 Servis",
        ("destek", "rolmenusu", "cekilis"),
    ),
    "ekstra": (
        "✨ Ekstra",
        ("anket", "hesap", "afk"),
    ),
    "sahip": (
        "👑 Sahip",
        ("gen", "sunucular", "kapat", "sahip"),
    ),
}

HELP_FLAVOR = [
    "buzdolabının arkasında 2019'dan beri pişiyor",
    "absolute potato enerjisi",
    "üç kelime gir, üç yüz satır çıksın",
    "turbo mod: açık",
]


class KategoriSecici(discord.ui.Select):
    def __init__(self, author_id: int) -> None:
        options = [
            discord.SelectOption(
                label=key,
                description=title,
                emoji=title.split()[0],
            )
            for key, (title, _) in CATEGORIES.items()
        ]
        super().__init__(
            placeholder="Bir kategori seç...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="yardim_kategori",
        )
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                embed=embeds.hata("Bu menü senin değil, şef."), ephemeral=True
            )
            return
        key = self.values[0]
        title, komutlar = CATEGORIES[key]
        metin = "\n".join(f"`/{k}`" for k in komutlar)
        embed = embeds.taban(
            title=f"{title} • /{key}",
            description=metin,
        )
        embed.add_field(
            name="İpucu",
            value="Tüm komutlar slash tabanlı, Discord sana seçenekleri zaten gösterir.",
            inline=False,
        )
        await interaction.response.edit_message(embed=embed)


class YardimCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="yardim", description="Supnex bot komut rehberini açar.")
    async def yardim(self, interaction: discord.Interaction) -> None:
        embed = embeds.taban(
            title="Supnex Bot • Komut Panosu",
            description=f"**{random.choice(HELP_FLAVOR)}**\n\n"
                        "Aşağıdan bir kategori seç, tüm komutları gör.",
        )
        embed.add_field(
            name="Hızlı başlangıç",
            value="`/yardim` • `/kullanicibilgi` • `/gunluk` • `/seviyem`",
            inline=False,
        )

        sayfalar = []
        for key, (title, komutlar) in CATEGORIES.items():
            sayfa = embeds.taban(
                title=f"{title} — {len(komutlar)} komut",
                description="\n".join(f"`/{k}`" for k in komutlar),
            )
            sayfalar.append(sayfa)

        view = KategoriView(interaction.user.id, sayfalar)
        view.yerlestir()
        await interaction.response.send_message(embed=embed, view=view)


class KategoriView(discord.ui.View):
    def __init__(self, author_id: int, sayfalar: list[discord.Embed]) -> None:
        super().__init__(timeout=120)
        self.author_id = author_id
        self.sayfalar = sayfalar
        self.sayfalayici = Paginator(sayfalar, author_id)

    def yerlestir(self) -> None:
        self.add_item(KategoriSecici(self.author_id))
        self.add_item(self.sayfalayici.prev)
        self.add_item(self.sayfalayici.next)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                embed=embeds.hata("Bu menü senin değil, şef."), ephemeral=True
            )
            return False
        return True