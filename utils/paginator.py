"""Self-contained pagination view for multi-page command lists."""
import discord

from . import embeds


class Paginator(discord.ui.View):
    def __init__(self, pages: list[discord.Embed], author_id: int) -> None:
        super().__init__()
        self.pages = pages
        self.author_id = author_id
        self.index = 0
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.prev.disabled = self.index == 0
        self.next.disabled = self.index == len(self.pages) - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                embed=embeds.hata("Bu menü senin değil, şef."), ephemeral=True
            )
            return False
        return True

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, _) -> None:
        self.index -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, _) -> None:
        self.index += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)