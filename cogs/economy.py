"""Buzdolabı ekonomisi: bakiye, günlük, çalış, balık tut, slot, sıralama."""
import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from utils import db, embeds

GUNLUK_ODUL = 250
GUNLUK_BEKL = 24 * 3600
CALISMA_BEKL = 5 * 60
BALIK_BEKL = 45
SLOT_SIMGELER = ["🍀", "🍟", "💎", "🥔", "💰", "🔥"]


def _bekle(last: int, sofra: int) -> int:
    return max(0, int(last + sofra - time.time()))


class EkonomiCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="bakiye", description="Buzdolabı bakiyeni gör.")
    async def bakiye(
        self, interaction: discord.Interaction, uye: discord.Member | None = None
    ) -> None:
        uye = uye or interaction.user
        bakiye = db.get_balance(uye.id)
        embed = embeds.taban(
            title=f"{uye.display_name} cüzdanı",
            description=f"🥔 **{bakiye}** patates parası",
        )
        embed.set_thumbnail(url=uye.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="gonder", description="Bir patatese para gönder.")
    async def gonder(
        self, interaction: discord.Interaction, uye: discord.Member, miktar: int
    ) -> None:
        if uye.id == interaction.user.id:
            await interaction.response.send_message(
                embed=embeds.hata("Kendine gönderemezsin, şef. Aynı patates."), ephemeral=True
            )
            return
        if miktar <= 0:
            await interaction.response.send_message(
                embed=embeds.hata("Miktar pozitif olmalı."), ephemeral=True
            )
            return
        bakiye = db.get_balance(interaction.user.id)
        if bakiye < miktar:
            await interaction.response.send_message(
                embed=embeds.hata(f"Yetmiyor. Bakiyen: 🥔 **{bakiye}**."), ephemeral=True
            )
            return
        db.add_money(interaction.user.id, -miktar)
        db.add_money(uye.id, miktar)
        await interaction.response.send_message(
            embed=embeds.onay(f"**{uye.display_name}**'e 🥔 **{miktar}** para gönderildi.")
        )

    @app_commands.command(name="gunluk", description="Günlük buzdolabı harcını al.")
    async def gunluk(self, interaction: discord.Interaction) -> None:
        now = int(time.time())
        satir = db._CONN.execute(
            "SELECT last_daily FROM users WHERE user_id = ?", (interaction.user.id,)
        ).fetchone()
        son = satir["last_daily"] if satir else 0
        kalan = _bekle(son, GUNLUK_BEKL)
        if kalan > 0:
            await interaction.response.send_message(
                embed=embeds.uyari(f"Bugün almışsın. **{kalan}**sn sonra tekrar gel."),
                ephemeral=True,
            )
            return
        db._CONN.execute(
            "INSERT INTO users (user_id, balance, last_daily) VALUES (?, ?, ?)"
            " ON CONFLICT(user_id) DO UPDATE SET last_daily = excluded.last_daily",
            (interaction.user.id, GUNLUK_ODUL, now),
        )
        db._CONN.commit()
        await interaction.response.send_message(
            embed=embeds.onay(f"🥔 **{GUNLUK_ODUL}** para aldın. Absolute potato.")
        )

    @app_commands.command(name="calis", description="Patates parası için çalış.")
    async def calis(self, interaction: discord.Interaction) -> None:
        now = int(time.time())
        satir = db._CONN.execute(
            "SELECT last_work FROM users WHERE user_id = ?", (interaction.user.id,)
        ).fetchone()
        son = satir["last_work"] if satir else 0
        kalan = _bekle(son, CALISMA_BEKL)
        if kalan > 0:
            await interaction.response.send_message(
                embed=embeds.uyari(f"Mola veriliyor. **{kalan}**sn sonra gel."),
                ephemeral=True,
            )
            return
        kazan = random.randint(30, 120)
        db.add_money(interaction.user.id, kazan)
        db._CONN.execute(
            "UPDATE users SET last_work = ? WHERE user_id = ?", (now, interaction.user.id)
        )
        db._CONN.commit()
        isler = [
            "buzdolabında patatesleri dizdi", "bozuk yahniyi debug etti",
            "ağlayana kadar soğan soydu", "patates barı için burger çevirdi",
            "sebzelik devresini yeniden bağladı",
        ]
        await interaction.response.send_message(
            embed=embeds.onay(f"{random.choice(isler)} ve 🥔 **{kazan}** para kazandın.")
        )

    @app_commands.command(name="balik", description="Buzdolabı gölüne oltanı at.")
    async def balik(self, interaction: discord.Interaction) -> None:
        now = int(time.time())
        satir = db._CONN.execute(
            "SELECT last_fish FROM users WHERE user_id = ?", (interaction.user.id,)
        ).fetchone()
        son = satir["last_fish"] if satir else 0
        kalan = _bekle(son, BALIK_BEKL)
        if kalan > 0:
            await interaction.response.send_message(
                embed=embeds.uyari(f"Sakin sular. **{kalan}**sn bekle."),
                ephemeral=True,
            )
            return
        av = random.randint(-20, 100)
        db.add_money(interaction.user.id, av)
        db._CONN.execute(
            "UPDATE users SET last_fish = ? WHERE user_id = ?", (now, interaction.user.id)
        )
        db._CONN.commit()
        if av > 70:
            ganimet = "🐟 altın ringa! Lezzetli av."
        elif av > 0:
            ganimet = "🐟 kıyak bir patates-balığı."
        else:
            ganimet = "🧦 ıslak bir çorap. Nem vergisini ödedin."
        embed = embeds.taban(description=f"Attın, bekledin, çektin: {ganimet}")
        embed.add_field(name="Paralar", value=f"{av:+d}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="slot", description="Tek kollu patates haydutu.")
    @app_commands.describe(bahis="Kaç para bastığın.")
    async def slot(self, interaction: discord.Interaction, bahis: int = 25) -> None:
        if bahis <= 0:
            bahis = 25
        bakiye = db.get_balance(interaction.user.id)
        if bakiye < bahis:
            await interaction.response.send_message(
                embed=embeds.hata(f"Yetmiyor. Cüzdan: 🥔 **{bakiye}**."), ephemeral=True
            )
            return
        makaralar = [random.choice(SLOT_SIMGELER) for _ in range(3)]
        if makaralar[0] == makaralar[1] == makaralar[2]:
            odul = bahis * 6
            db.add_money(interaction.user.id, odul)
            sonuc = f"BÜYÜK İKRAMİYE! 🥔 **+{odul}**"
        elif makaralar[0] == makaralar[1] or makaralar[1] == makaralar[2]:
            odul = round(bahis * 1.5)
            db.add_money(interaction.user.id, odul)
            sonuc = f"İkili geldi! 🥔 **+{odul}**"
        else:
            db.add_money(interaction.user.id, -bahis)
            sonuc = f"Hep gaz, dönüş yok. 🥔 **-{bahis}**"
        embed = embeds.taban(
            title=" ".join(makaralar),
            description=sonuc,
        )
        embed.add_field(name="Yeni bakiye", value=str(db.get_balance(interaction.user.id)))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="siralama", description="Sunucunun en zengin patatesleri.")
    async def siralama(self, interaction: discord.Interaction) -> None:
        satirlar = db.top_balances(10)
        satirlar = [s for s in satirlar if self.bot.get_user(s["user_id"]) or interaction.guild.get_member(s["user_id"])]
        satirlar = satirlar[:10]
        satirlar_liste = []
        madalyalar = ["🥇", "🥈", "🥉"]
        for i, satir in enumerate(satirlar):
            kullanici = self.bot.get_user(satir["user_id"]) or interaction.guild.get_member(satir["user_id"])
            isim = kullanici.display_name if kullanici else f"<@{satir['user_id']}>"
            madalya = madalyalar[i] if i < 3 else f"`{i + 1}.`"
            satirlar_liste.append(f"{madalya} **{isim}** — 🥔 {satir['balance']}")
        embed = embeds.taban(
            title="🥔 Buzdolabı Zengin Listesi",
            description="\n".join(satirlar_liste) or "Henüz kimse zengin değil.",
        )
        await interaction.response.send_message(embed=embed)