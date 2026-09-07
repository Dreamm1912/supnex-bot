# Supnex Bot v2.0

Turbo fridge energy. 50+ slash commands.

## Setup

1. Create a bot at <https://discord.com/developers/applications>.
   - Enable **Message Content Intent** and **Server Members Intent**.
2. Copy your token into `.env`:
   ```
   DISCORD_TOKEN=your_token_here
   ```
3. Install:
   ```
   pip install -r requirements.txt
   ```
4. Run: `python main.py`, or press **F5** in VS Code.

## Command board

| Category | Commands |
|---|---|
| Info | `/ping` `/uptime` `/botinfo` `/userinfo` `/serverinfo` `/avatar` `/servericon` `/echo` `/color` `/embed` `/roles` |
| Fun | `/roll` `/dice` `/coinflip` `/8ball` `/choose` `/rps` `/joke` `/quote` `/meme` |
| Economy | `/balance` `/pay` `/daily` `/work` `/fish` `/slots` `/top` |
| Levels | `/rank` `/xplb` — auto XP on every message, level-up cards |
| Moderation | `/kick` `/ban` `/unban` `/timeout` `/warn` `/warns` `/unwarn` `/clear` |
| Service | `/ticket` — private ticket + close button. `/rolemenu` — self-serve roles. `/giveaway` — button draws |
| Nitro | `/gen <1-300>` — live generation board (demo codes) |

## Extras

- **Welcome embed** on member join.
- **Automatic leveling** with a 60s cooldown per user, level-up announcements.
- **Rotating presence** so the bot never looks dead.
- **Styled embeds** everywhere: brand color, footer, timestamp.
- **SQLite persistence** — economy, XP, warns and giveaways survive restarts.
- `/help` — category dropdown + paginated page navigator.

## Structure

```
supnex-bot/
  main.py            # bootstrap: cogs, intents, status cycle, events
  cogs/
    info.py          # /ping /userinfo /serverinfo /avatar ...
    fun.py           # /8ball /rps /joke /meme ...
    economy.py       # /daily /work /slots /top ...
    leveling.py      # /rank /xplb
    moderation.py    # /kick /ban /timeout /warn /clear ...
    tickets.py       # /ticket
    rolemenu.py      # /rolemenu
    giveaway.py      # /giveaway
    generator.py     # /gen (demo Nitro board)
    help.py          # /help navigator
  utils/
    db.py            # sqlite3 layer
    embeds.py        # brand styling
    paginator.py     # paginated views
  requirements.txt
  .env.example       # copy to .env
  .gitignore
```