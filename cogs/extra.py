"""Ekstra özellikler: /anket buton oylaması, /afk otomatik yanıt, /hesap güvenli aritmetik."""
import ast
import operator
import time

import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds

EMOJILER = ("1️⃣", "2️⃣", "3️⃣", "4️⃣")
_AFK: dict[int, tuple[str, float]] = {}

_IKILI_OP = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_TEKLI_OP = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _guvenli_eval(ifade: str):
    """Sadece beyaz listeli aritmetik dilbilgisi ağacı düğümlerini işle."""
    try:
        dugum = ast.parse(ifade, mode="eval").body
    except SyntaxError:
        raise ValueError("Geçerli bir ifade değil.")
    _Kontrolcu().visit(dugum)
    return eval(compile(ast.Expression(dugum), "<hesap>", "eval"), {"__builtins__": {}})


class _Kontrolcu(ast.NodeVisitor):
    def visit(self, dugum):
        if isinstance(dugum, ast.Constant) and isinstance(dugum.value, (int, float)):
            return
        if isinstance(dugum, ast.BinOp) and type(dugum.op) in _IKILI_OP:
            self.visit(dugum.left); self.visit(dugum.right)
            return
        if isinstance(dugum, ast.UnaryOp) and type(dugum.op) in _TEKLI_OP:
            self.visit(dugum.operand)
            return
        raise ValueError("Sadece sayılar ve + - * / % ** ( ) kullanılır.")


class AnketButonu(discord.ui.Button):
    def __init__(self, indeks: int, etiket: str, anket) -> None:
        super().__init__(label=f"{EMOJILER[indeks]} {etiket[:24]}", style=discord.ButtonStyle.secondary)
        self.indeks = indeks
        self.anket = anket

    async def callback(self, interaction: discord.Interaction) -> None:
        self.anket.oylar[interaction.user.id] = self.indeks
        await self.anket.yeniden_ciz(interaction)


class AnketView(discord.ui.View):
    def __init__(self, soru: str, secenekler: list[str], sahip_id: int) -> None:
        super().__init__(timeout=None)
        self.soru = soru
        self.secenekler = secenekler
        self.sahip_id = sahip_id
        self.oylar: dict[int, int] = {}
        for i, secenek in enumerate(secenekler):
            self.add_item(AnketButonu(i, secenek, self))

    def sayim(self) -> list[int]:
        sayilar = [0] * len(self.secenekler)
        for oy in self.oylar.values():
            sayilar[oy] += 1
        return sayilar

    def kur(self) -> discord.Embed:
        sayilar = self.sayim()
        toplam = len(self.oylar)
        satirlar = []
        for i, secenek in enumerate(self.secenekler):
            oy = sayilar[i]
            yuzde = round(oy / toplam * 100) if toplam else 0
            bar = "█" * (yuzde // 10) + "░" * (10 - yuzde // 10)
            satirlar.append(f"{EMOJILER[i]} **{secenek}** — {oy} oy (%{yuzde})\n`{bar}`")
        embed = embeds.taban(
            title=f"📊 {self.soru}",
            description="\n\n".join(satirlar),
        )
        embed.add_field(name="Toplam oy", value=str(toplam), inline=False)
        return embed

    async def yeniden_ciz(self, interaction: discord.Interaction) -> None:
        embed = self.kur()
        await interaction.response.edit_message(embed=embed)
        await interaction.followup.send(
            embed=embeds.onay("Oyun kaydedildi, şef."), ephemeral=True
        )


class EkstraCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="anket", description="Butonlu oylama başlat (2-4 seçenek).")
    @app_commands.describe(soru="Anket sorusu.", secenek1="Birinci seçenek", secenek2="İkinci seçenek", secenek3="Üçüncü seçenek (isteğe bağlı)", secenek4="Dördüncü seçenek (isteğe bağlı)")
    async def anket(self, interaction: discord.Interaction, soru: str, secenek1: str,
                    secenek2: str, secenek3: str | None = None, secenek4: str | None = None) -> None:
        secenekler = [secenek1, secenek2]
        if secenek3:
            secenekler.append(secenek3)
        if secenek4:
            secenekler.append(secenek4)
        secenekler = secenekler[:4]
        await interaction.response.defer()
        view = AnketView(soru, secenekler, interaction.user.id)
        await interaction.followup.send(embed=view.kur(), view=view)

    @app_commands.command(name="hesap", description="Güvenli aritmetik. Deneme: /hesap 2*(3+4)**2")
    async def hesap(self, interaction: discord.Interaction, ifade: str) -> None:
        try:
            sonuc = _guvenli_eval(ifade)
        except (ValueError, ZeroDivisionError) as exc:
            await interaction.response.send_message(
                embed=embeds.hata(str(exc)), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=embeds.taban(
                title="🧮",
                description=f"`{ifade}` = **{sonuc}**",
            )
        )

    @app_commands.command(name="afk", description="AFK mesajı kur. Etiketlenince otomatik cevap verir.")
    async def afk(self, interaction: discord.Interaction, sebep: str = "AFK, hemen dönüyorum.") -> None:
        _AFK[interaction.user.id] = (sebep, time.time())
        await interaction.response.send_message(
            embed=embeds.onay(f"AFK kuruldu: {interaction.user.mention} — *{sebep}*"),
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_message(self, mesaj: discord.Message) -> None:
        if mesaj.author.bot or not mesaj.guild:
            return
        if mesaj.author.id in _AFK:
            sebep, zaman = _AFK.pop(mesaj.author.id)
            embed = embeds.onay(
                f"Hoş geldin {mesaj.author.mention}. **{sebep}** sebebiyle "
                f"<t:{int(zaman)}:R>'den beri AFK'ydin."
            )
            await mesaj.channel.send(embed=embed)
            return
        for etiket in mesaj.mentions:
            if not etiket.bot and etiket.id in _AFK:
                sebep, zaman = _AFK[etiket.id]
                embed = embeds.uyari(
                    f"**{etiket.display_name}** <t:{int(zaman)}:R>'den beri AFK:\n> {sebep}"
                )
                await mesaj.channel.send(embed=embed)
                return