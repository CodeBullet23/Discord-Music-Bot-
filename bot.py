import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import random
import aiohttp

# ---------------- CONFIG ----------------

TOKEN = "YOUR_BOT_TOKEN_HERE_1234567890"   # <-- PUT YOUR DISCORD BOT TOKEN HERE

DEFAULT_VOLUME = 2
MAX_VOLUME = 10
MIN_VOLUME = 0

FADE_DURATION = 2.5
DELAY_MIN = 1
DELAY_MAX = 5

SUPPORTED_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".ogg", ".mp4")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_FOLDER = os.path.join(BASE_DIR, "music")
INCOMING_FOLDER = os.path.join(BASE_DIR, "incoming")

def ensure_folders():
    os.makedirs(MUSIC_FOLDER, exist_ok=True)
    os.makedirs(INCOMING_FOLDER, exist_ok=True)

# ---------------- FFMPEG ----------------

FFMPEG_PATH = r"FFmpeg path here "

FFMPEG_OPTIONS = {
    "before_options": "-loglevel quiet -hide_banner -nostats",
    "options": "-vn",
    "executable": FFMPEG_PATH
}

# ---------------- SECURITY SETTINGS ----------------

REQUIRED_ROLE_ID = 111111111111111111
BOT_ADMIN_ROLE_ID = 222222222222222222

WEBHOOK_URL = "https://discord.com/api/webhooks/000000000000000000/REPLACE_ME_WITH_YOUR_WEBHOOK"

SESSION_OWNER = {}  # guild_id -> user_id

# ---------------- BOT SETUP ----------------

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

music_states = {}  # guild_id -> MusicState

# ---------------- TRACK + STATE CLASSES ----------------

class Track:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.title = os.path.basename(filepath)
        self.requested_by = "Radio"

class MusicState:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.tracks: list[Track] = []
        self.current_index: int = 0
        self.current: Track | None = None
        self.voice: discord.VoiceClient | None = None
        self.volume: int = DEFAULT_VOLUME
        self.panel_message: discord.Message | None = None
        self.playing: bool = False
        self.fading: bool = False

    def get_effective_volume(self) -> float:
        return max(MIN_VOLUME, min(MAX_VOLUME, self.volume)) / 10.0

    def has_tracks(self) -> bool:
        return len(self.tracks) > 0
# ---------------- SECURITY HELPERS ----------------

def has_control_role(member: discord.Member) -> bool:
    # Server owner ALWAYS allowed
    if member == member.guild.owner:
        return True

    # Admins always allowed
    if member.guild_permissions.administrator:
        return True

    # Bot admin override role
    if any(role.id == BOT_ADMIN_ROLE_ID for role in member.roles):
        return True

    # Required DJ role
    return any(role.id == REQUIRED_ROLE_ID for role in member.roles)


def is_session_owner(member: discord.Member) -> bool:
    return SESSION_OWNER.get(member.guild.id) == member.id


def can_control_session(member: discord.Member) -> bool:
    # Server owner override
    if member == member.guild.owner:
        return True

    # Admin override
    if member.guild_permissions.administrator:
        return True

    # Bot admin override
    if any(role.id == BOT_ADMIN_ROLE_ID for role in member.roles):
        return True

    # Session owner
    return is_session_owner(member)


# ---------------- TRACK LOADING ----------------

def load_local_tracks() -> list[Track]:
    ensure_folders()
    files = []

    for name in sorted(os.listdir(MUSIC_FOLDER)):
        if name.lower().endswith(SUPPORTED_EXTS):
            full = os.path.join(MUSIC_FOLDER, name)
            files.append(Track(full))

    return files


def get_state(guild: discord.Guild) -> MusicState:
    if guild.id not in music_states:
        state = MusicState(guild)
        state.tracks = load_local_tracks()
        music_states[guild.id] = state
    return music_states[guild.id]


# ---------------- EMBED + CONTROL PANEL UI ----------------

async def build_panel_embed(state: MusicState) -> discord.Embed:
    if state.current:
        title = f"🎵 Now Playing: {state.current.title}"
        desc = f"Source: **Local file**\n\n"
    else:
        title = "🎵 Music Controls (Local Radio)"
        desc = "Radio is idle.\n\n"

    if state.has_tracks():
        desc += "**Playlist (local files):**\n"
        for i, t in enumerate(state.tracks, start=1):
            mark = "▶" if state.current and state.tracks.index(state.current) == i - 1 else " "
            desc += f"`{i}.` {mark} {t.title}\n"
    else:
        desc += "_No audio files found in the music folder._\n"

    desc += f"\n**Volume:** {state.volume}/10\n"
    desc += (
        "**Song Requests:** Use `/requestlink <url>` to submit a link.\n"
        "Links are logged with your Discord account."
    )

    return discord.Embed(title=title, description=desc, color=0x5865F2)


async def update_panel(state: MusicState):
    if not state.panel_message:
        return
    try:
        embed = await build_panel_embed(state)
        await state.panel_message.edit(embed=embed, view=MusicControlView(state))
    except discord.NotFound:
        state.panel_message = None


# ---------------- CONTROL PANEL VIEW ----------------

class MusicControlView(discord.ui.View):
    def __init__(self, state: MusicState):
        super().__init__(timeout=None)
        self.state = state

    async def _check(self, interaction: discord.Interaction) -> bool:
        if not can_control_session(interaction.user):
            await interaction.response.send_message(
                "You cannot control the radio.",
                ephemeral=True
            )
            return False
        return True

    # ---------------- PLAY / RESUME ----------------
    @discord.ui.button(label="Play / Resume", style=discord.ButtonStyle.green)
    async def play_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check(interaction):
            return

        state = self.state
        voice = await ensure_voice(interaction, state)
        if not voice:
            return

        if not state.has_tracks():
            await interaction.response.send_message("No tracks found.", ephemeral=True)
            return

        # Resume
        if state.voice and state.voice.is_paused():
            state.voice.resume()
            state.playing = True
            await update_panel(state)
            await interaction.response.send_message("Resumed.", ephemeral=True)
            return

        # Start fresh
        state.playing = True
        await interaction.response.send_message("Starting radio...", ephemeral=True)
        await update_panel(state)
        await play_next_local(state.guild.id)

    # ---------------- PAUSE ----------------
    @discord.ui.button(label="Pause", style=discord.ButtonStyle.secondary)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check(interaction):
            return

        state = self.state
        if state.voice and state.voice.is_playing():
            state.voice.pause()
            state.playing = False
            await update_panel(state)
            await interaction.response.send_message("Paused.", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)

    # ---------------- VOLUME UP ----------------
    @discord.ui.button(label="Vol +", style=discord.ButtonStyle.blurple)
    async def vol_up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check(interaction):
            return

        state = self.state
        state.volume = min(MAX_VOLUME, state.volume + 1)
        await apply_volume(state)
        await update_panel(state)
        await interaction.response.send_message(f"Volume: {state.volume}/10", ephemeral=True)

    # ---------------- VOLUME DOWN ----------------
    @discord.ui.button(label="Vol -", style=discord.ButtonStyle.blurple)
    async def vol_down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check(interaction):
            return

        state = self.state
        state.volume = max(MIN_VOLUME, state.volume - 1)
        await apply_volume(state)
        await update_panel(state)
        await interaction.response.send_message(f"Volume: {state.volume}/10", ephemeral=True)

    # ---------------- SKIP ----------------
    @discord.ui.button(label="Skip", style=discord.ButtonStyle.gray)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check(interaction):
            return

        state = self.state
        if state.voice and (state.voice.is_playing() or state.voice.is_paused()):
            await interaction.response.send_message("Skipping...", ephemeral=True)
            await fade_out_and_next(state)
        else:
            await interaction.response.send_message("Nothing to skip.", ephemeral=True)

    # ---------------- STOP & LEAVE ----------------
    @discord.ui.button(label="Stop & Leave", style=discord.ButtonStyle.red)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check(interaction):
            return

        state = self.state
        state.playing = False

        # Clear session owner
        SESSION_OWNER.pop(state.guild.id, None)

        await fade_out_and_stop(state)

        # Delete panel
        try:
            if state.panel_message:
                await state.panel_message.delete()
        except:
            pass

        state.panel_message = None

        await interaction.response.send_message("Stopped and disconnected.", ephemeral=True)
# ---------------- VOICE CONNECTION + AUDIO ENGINE ----------------

async def ensure_voice(interaction_or_ctx, state: MusicState):
    """Ensures the bot joins the user's voice channel."""
    if isinstance(interaction_or_ctx, discord.Interaction):
        user = interaction_or_ctx.user
        send = interaction_or_ctx.response.send_message
    else:
        user = interaction_or_ctx.author
        send = interaction_or_ctx.send

    if not isinstance(user, discord.Member):
        await send("This can only be used in a server.")
        return None

    voice_state = user.voice
    if not voice_state or not voice_state.channel:
        await send("You must be in a voice channel.")
        return None

    channel = voice_state.channel

    # Move or connect
    if state.voice and state.voice.channel != channel:
        await state.voice.move_to(channel)
    elif not state.voice:
        state.voice = await channel.connect()

    return state.voice


async def apply_volume(state: MusicState):
    """Applies volume to the current audio source."""
    if state.voice and state.voice.source and isinstance(state.voice.source, discord.PCMVolumeTransformer):
        state.voice.source.volume = state.get_effective_volume()


# ---------------- FADE LOGIC ----------------

async def fade_volume(state: MusicState, start: float, end: float, duration: float):
    """Smooth volume fade."""
    if not state.voice or not state.voice.source:
        return

    steps = max(1, int(duration * 20))
    step_time = duration / steps

    for i in range(steps + 1):
        if not state.voice or not state.voice.source:
            break
        t = i / steps
        vol = start + (end - start) * t
        state.voice.source.volume = vol
        await asyncio.sleep(step_time)


async def fade_in(state: MusicState):
    if not state.voice or not state.voice.source:
        return
    base = state.get_effective_volume()
    state.voice.source.volume = 0.0
    await fade_volume(state, 0.0, base, FADE_DURATION)


async def fade_out(state: MusicState):
    if not state.voice or not state.voice.source:
        return
    current_vol = state.voice.source.volume
    await fade_volume(state, current_vol, 0.0, FADE_DURATION)


# ---------------- NEXT TRACK / STOP LOGIC ----------------

async def fade_out_and_next(state: MusicState):
    """Fade out current track and play the next one."""
    if state.fading:
        return
    state.fading = True

    try:
        if state.voice and state.voice.is_playing():
            await fade_out(state)
            state.voice.stop()

        await asyncio.sleep(random.randint(DELAY_MIN, DELAY_MAX))

        if state.playing:
            await play_next_local(state.guild.id)

    finally:
        state.fading = False


async def fade_out_and_stop(state: MusicState):
    """Fade out and fully stop the radio."""
    if state.fading:
        return
    state.fading = True

    try:
        if state.voice and state.voice.is_playing():
            await fade_out(state)
            state.voice.stop()

        if state.voice and state.voice.is_connected():
            await state.voice.disconnect()
            state.voice = None

        state.current = None

    finally:
        state.fading = False


# ---------------- PLAYBACK ENGINE (FULLY FIXED) ----------------

async def play_next_local(guild_id: int):
    state = music_states.get(guild_id)
    if not state:
        return

    # 🔥 Prevent infinite recursion if audio is already playing
    if state.voice and state.voice.is_playing():
        return

    if not state.playing:
        await update_panel(state)
        return

    # Reload tracks every time (keeps folder live)
    state.tracks = load_local_tracks()
    if not state.has_tracks():
        state.current = None
        await update_panel(state)
        return

    # Determine next track
    if state.current is None:
        state.current_index = 0
    else:
        state.current_index = (state.current_index + 1) % len(state.tracks)

    track = state.tracks[state.current_index]
    state.current = track

    try:
        if not state.voice or not state.voice.is_connected():
            return

        audio_source = discord.FFmpegPCMAudio(track.filepath, **FFMPEG_OPTIONS)
        source = discord.PCMVolumeTransformer(audio_source)

        # 🔥 SAFE after_play callback
        def after_play(error):
            if error:
                print("Playback error:", error)
                return

            async def _after():
                await asyncio.sleep(random.randint(DELAY_MIN, DELAY_MAX))
                if state.playing:
                    await play_next_local(guild_id)

            asyncio.run_coroutine_threadsafe(_after(), bot.loop)

        state.voice.play(source, after=after_play)
        await update_panel(state)
        await fade_in(state)

    except Exception as e:
        print("Playback error:", e)
        state.playing = False
        return
# ---------------- SLASH COMMANDS ----------------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    ensure_folders()

    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print("Sync error:", e)


@tree.command(name="play", description="Show the local radio music controls panel")
async def slash_play(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This only works in servers.", ephemeral=True)
        return

    # Permission check
    if not has_control_role(interaction.user):
        await interaction.response.send_message(
            "You do not have permission to start the radio.",
            ephemeral=True
        )
        return

    # Session lock
    owner_id = SESSION_OWNER.get(interaction.guild.id)
    if owner_id and owner_id != interaction.user.id:
        await interaction.response.send_message(
            "The radio is currently in use by another user.",
            ephemeral=True
        )
        return

    # Set session owner
    SESSION_OWNER[interaction.guild.id] = interaction.user.id

    state = get_state(interaction.guild)
    embed = await build_panel_embed(state)
    view = MusicControlView(state)

    await interaction.response.send_message(embed=embed, view=view)
    msg = await interaction.original_response()
    state.panel_message = msg


@tree.command(name="stop", description="Stop radio and leave the voice channel")
async def slash_stop(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("This only works in servers.", ephemeral=True)
        return

    if not can_control_session(interaction.user):
        await interaction.response.send_message(
            "Only the session owner, a server admin, or a bot admin can stop the radio.",
            ephemeral=True
        )
        return

    state = get_state(interaction.guild)
    state.playing = False

    # Clear session owner
    SESSION_OWNER.pop(interaction.guild.id, None)

    await fade_out_and_stop(state)

    # Delete panel
    try:
        if state.panel_message:
            await state.panel_message.delete()
    except:
        pass

    state.panel_message = None

    await interaction.response.send_message("Stopped radio and left the channel.", ephemeral=True)


@tree.command(name="requestlink", description="Submit a link for the radio hub to review")
@app_commands.describe(url="Direct link to the audio/video (YouTube, MP3, etc.)")
async def slash_requestlink(interaction: discord.Interaction, url: str):
    if not interaction.guild:
        await interaction.response.send_message("This only works in servers.", ephemeral=True)
        return

    if not (url.startswith("http://") or url.startswith("https://")):
        await interaction.response.send_message(
            "Please provide a valid link starting with http:// or https://",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "Your request has been sent for review.\n"
        "Your Discord username and ID are logged.",
        ephemeral=True
    )

    if not WEBHOOK_URL or not WEBHOOK_URL.startswith("https://"):
        print("[WARN] Invalid webhook URL.")
        return

    user = interaction.user
    guild = interaction.guild
    channel = interaction.channel

    content = (
        f"📥 **New radio link request**\n"
        f"**User:** {user} (`{user.id}`)\n"
        f"**Server:** {guild.name} (`{guild.id}`)\n"
        f"**Channel:** #{channel.name} (`{channel.id}`)\n\n"
        f"**Link:** {url}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
            await webhook.send(content=content, username="Radio Link Request")
    except Exception as e:
        print("Webhook error:", e)


# ---------------- PREFIX COMMANDS ----------------

@bot.command(name="play")
async def cmd_play(ctx: commands.Context):
    if not has_control_role(ctx.author):
        await ctx.send("You do not have permission to start the radio.")
        return

    owner_id = SESSION_OWNER.get(ctx.guild.id)
    if owner_id and owner_id != ctx.author.id:
        await ctx.send("The radio is currently in use by another user.")
        return

    SESSION_OWNER[ctx.guild.id] = ctx.author.id

    state = get_state(ctx.guild)
    embed = await build_panel_embed(state)
    view = MusicControlView(state)
    msg = await ctx.send(embed=embed, view=view)
    state.panel_message = msg


@bot.command(name="stop")
async def cmd_stop(ctx: commands.Context):
    if not can_control_session(ctx.author):
        await ctx.send("Only the session owner, a server admin, or a bot admin can stop the radio.")
        return

    state = get_state(ctx.guild)
    state.playing = False

    SESSION_OWNER.pop(ctx.guild.id, None)

    await fade_out_and_stop(state)

    try:
        if state.panel_message:
            await state.panel_message.delete()
    except:
        pass

    state.panel_message = None

    await ctx.send("Stopped radio and left the channel.")
# ---------------- RUN BOT ----------------

bot.run(TOKEN)


# ---------------- OPTIONAL CLEANUP & RECOMMENDATIONS ----------------
#
# These are not required for the bot to run, but they help keep things stable.
#
# 1. Make sure your ffmpeg path is correct.
#    If ffmpeg ever moves, update FFMPEG_PATH.
#
# 2. Keep your music folder clean.
#    The bot reloads the folder every track, so avoid:
#       - huge files
#       - corrupted files
#       - non‑audio files
#
# 3. If you add new audio formats, update SUPPORTED_EXTS.
#
# 4. If you want the bot to be quieter or louder by default,
#    change DEFAULT_VOLUME (0–10).
#
# 5. If you want longer or shorter fade‑in/out,
#    change FADE_DURATION.
#
# 6. If you want longer or shorter delays between tracks,
#    change DELAY_MIN and DELAY_MAX.
#
# 7. If the bot ever gets stuck in a session lock,
#    restart the bot — SESSION_OWNER resets automatically.
#
# 8. If you want to completely reset the bot state manually:
#       music_states.clear()
#       SESSION_OWNER.clear()
#
# ---------------- END OF FILE ----------------
