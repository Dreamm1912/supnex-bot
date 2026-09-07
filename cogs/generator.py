"""Nitro generator: /gen <adet> canlı kod panosu + buton.

Sadece demo (sahte) kod üretir. Gerçek kod, token, ağ çağrısı yok.
Owner'a özel komuttur.
"""
import random
import string

import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds
from cogs.owner import OWNER_ID

SAHTE_KARAKTERLER = string.ascii_uppercase + string.digits
HEDİYE_ON_EKLER = ("discord.gift/", "dsc.gg/", "discord.com/gifts/")
MAKS_GENERATOR = 300


def sahte_kod(uzunluk: int = 16) -> str:
    return "".join(random.choice(SAHTE_KARAKTERLER) for _ in range(uzunluk))


class GeneratorPanosu(discord.ui.View):
    timeout = None

    def __init__(self, etiketler: list[str], sahip_id: int) -> None:
        super().__init__()
        self.etiketler = etiketler
        self.sahip_id = sahip_id
        self.dalga = 1

    def durum_embed(self) -> discord.Embed:
        embed = embeds.taban(
            title="Supnex Nitro Generator",
            description=f"{len(self.etiketler)} generator çevrimiçi — dalga `{self.dalga}`.",
        )
        embed.add_field(
            name="Canlı pano",
            value=self.dalga_metni(),
            inline=False,
        )
        embed.set_footer(text="Yeni dalga için butona bas.")
        embed.timestamp = discord.utils.utcnow()
        return embed

    def dalga_metni(self) -> str:
        satirlar = []
        for etiket in self.etiketler:
            on_ek = random.choice(HEDİYE_ON_EKLER)
            kod = sahte_kod(random.randint(12, 18))
            satirlar.append(f"[{etiket}] https://{on_ek}{kod}")
        return "\n".join(satirlar)

    @discord.ui.button(label="Dalga çevir", style=discord.ButtonStyle.primary)
    async def cevir(self, interaction: discord.Interaction, _) -> None:
        if interaction.user.id != self.sahip_id:
            await interaction.response.send_message(
                embed=embeds.hata("Bu panoya yalnızca komutu açan sürebilir."),
                ephemeral=True,
            )
            return
        self.dalga += 1
        embed = self.durum_embed()
        embed.title = f"Dalga {self.dalga}"
        await interaction.response.edit_message(embed=embed)


class GeneratorCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="gen", description="Nitro generator panosu kur (1-300). Sadece sahip.")
    @app_commands.describe(adet="Kaç generator kurulsun (1-300).")
    async def gen(self, interaction: discord.Interaction, adet: int) -> None:
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                embed=embeds.hata("Sadece sahibe özel, şef. Bu düğme Supnex'in elinde."),
                ephemeral=True,
            )
            return
        if not 1 <= adet <= MAKS_GENERATOR:
            await interaction.response.send_message(
                embed=embeds.hata(f"1 ile {MAKS_GENERATOR} arası seç."),
                ephemeral=True,
            )
            return
        await interaction.response.defer()
        etiketler = [f"GEN-{i + 1:03d}" for i in range(adet)]
        view = GeneratorPanosu(etiketler, interaction.user.id)
        await interaction.followup.send(embed=view.durum_embed(), view=view)