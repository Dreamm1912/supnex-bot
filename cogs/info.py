"""Sunucu, üye ve araç bilgi komutları — dolu embed'lerle."""
import time

import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds

BASLANGIC = time.time()


def _rol_rozet(member: discord.Member) -> str:
    if member.top_role.id != member.guild.id:
        return f"{member.top_role.mention}"
    return "Varsayılan"


class BilgiCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Gecikme ölçer, şef.")
    async def ping(self, interaction: discord.Interaction) -> None:
        embed = embeds.taban(
            title="Pong",
            description=f"WebSocket gecikmesi: **{round(self.bot.latency * 1000)}ms**",
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="uptime", description="Bot ne zamandır ayakta.")
    async def uptime(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=embeds.taban(
                description=f"**{embeds.uptime(BASLANGIC)}**'dir çalışıyor"
            )
        )

    @app_commands.command(name="botbilgi", description="Supnex Bot hakkında.")
    async def botbilgi(self, interaction: discord.Interaction) -> None:
        sunucu_sayisi = len(self.bot.guilds)
        uyeler = sum(g.member_count or 0 for g in self.bot.guilds)
        embed = embeds.taban(
            title="Supnex Bot",
            description="2019'dan beri Sam'in buzdolabının arkasında pişiyor. "
                        "50 civarı slash komut, sıfır taviz.",
        )
        embed.add_field(name="Sunucular", value=str(sunucu_sayisi), inline=True)
        embed.add_field(name="Üyeler", value=str(uyeler), inline=True)
        embed.add_field(name="Uptime", value=embeds.uptime(BASLANGIC), inline=True)
        embed.add_field(name="Python", value="3.13.7", inline=True)
        embed.add_field(name="discord.py", value="2.7.1", inline=True)
        embed.add_field(name="Gecikme", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kullanicibilgi", description="Bir üyenin profil kartı.")
    async def kullanicibilgi(
        self, interaction: discord.Interaction, uye: discord.Member | None = None
    ) -> None:
        uye = uye or interaction.user
        embed = embeds.taban(
            title=uye.display_name,
            description=f"**{uye.mention}** • `{uye}`",
        )
        embed.set_thumbnail(url=uye.display_avatar.url)
        embed.add_field(name="ID", value=f"`{uye.id}`", inline=True)
        embed.add_field(name="En üst rol", value=_rol_rozet(uye), inline=True)
        embed.add_field(
            name="Sunucuya katılış",
            value=discord.utils.format_dt(uye.joined_at, style="R"),
            inline=True,
        )
        embed.add_field(
            name="Hesap açılışı",
            value=discord.utils.format_dt(uye.created_at, style="R"),
            inline=True,
        )
        roller = ", ".join(r.mention for r in uye.roles[1:][:8]) or "Yok"
        embed.add_field(name=f"Roller ({len(uye.roles) - 1})", value=roller, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sunucubilgi", description="Bu sunucunun istatistik kartı.")
    async def sunucubilgi(self, interaction: discord.Interaction) -> None:
        sunucu = interaction.guild
        embed = embeds.taban(title=sunucu.name)
        embed.set_thumbnail(url=sunucu.icon.url if sunucu.icon else None)
        embed.add_field(name="ID", value=f"`{sunucu.id}`", inline=True)
        embed.add_field(name="Sahip", value=str(sunucu.owner), inline=True)
        embed.add_field(name="Üyeler", value=str(sunucu.member_count), inline=True)
        embed.add_field(name="Kanallar", value=str(len(sunucu.channels)), inline=True)
        embed.add_field(name="Roller", value=str(len(sunucu.roles)), inline=True)
        embed.add_field(name="Emojiler", value=str(len(sunucu.emojis)), inline=True)
        if sunucu.banner:
            embed.set_image(url=sunucu.banner.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Bir üyenin avatarını büyük göster.")
    async def avatar(
        self, interaction: discord.Interaction, uye: discord.Member | None = None
    ) -> None:
        uye = uye or interaction.user
        embed = embeds.taban(
            description=f"**{uye.mention}** avatarı",
        )
        embed.set_image(url=uye.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sunucuikon", description="Sunucu ikonu, kocaman.")
    async def sunucuikon(self, interaction: discord.Interaction) -> None:
        sunucu = interaction.guild
        if not sunucu.icon:
            await interaction.response.send_message(
                embed=embeds.hata("Bu sunucunun ikonu yok."), ephemeral=True
            )
            return
        embed = embeds.taban(description=f"**{sunucu.name}** ikonu")
        embed.set_image(url=sunucu.icon.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="tekrarla", description="Botun söylediğini tekrar etsin.")
    async def tekrarla(self, interaction: discord.Interaction, mesaj: str) -> None:
        await interaction.response.send_message(mesaj)

    @app_commands.command(name="renk", description="Bir hex rengi önizle.")
    async def renk(self, interaction: discord.Interaction, hexkod: str) -> None:
        hexkod = hexkod.strip("#")
        try:
            deger = int(hexkod, 16)
            if not (0 <= deger <= 0xFFFFFF):
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                embed=embeds.hata("Bana `ff8800` gibi bir hex ver."), ephemeral=True
            )
            return
        embed = embeds.taban(title=f"#{hexkod.upper()}", color=deger)
        embed.set_footer(text="Renk makinesi")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="embed", description="Stilleri embed oluştur.")
    @app_commands.describe(baslik="Embed başlığı.", aciklama="Embed gövdesi.")
    async def embed(
        self, interaction: discord.Interaction, baslik: str, aciklama: str
    ) -> None:
        await interaction.response.send_message(
            embed=embeds.taban(title=baslik, description=aciklama)
        )

    @app_commands.command(name="roller", description="Sunucudaki tüm rolleri listele.")
    async def roller(self, interaction: discord.Interaction) -> None:
        roller = interaction.guild.roles[1:]
        if not roller:
            await interaction.response.send_message(
                embed=embeds.hata("Burada rol yok."), ephemeral=True
            )
            return
        aciklama = "\n".join(
            f"{r.mention} • {len(r.members)} üye" for r in sorted(
                roller, key=lambda r: r.position, reverse=True
            )[:20]
        )
        await interaction.response.send_message(
            embed=embeds.taban(
                title=f"{interaction.guild.name} rolleri",
                description=aciklama,
            )
        )