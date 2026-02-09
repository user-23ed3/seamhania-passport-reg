import json
import threading
import asyncio
import os
from flask import Flask, request, redirect, render_template_string
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

# ================== CONFIG ==================
BOT_TOKEN = "MTQ2ODE1NDA1NjIzNjIwODIyMQ.GbZJan.4LsqYJFT4vrT4CbFuyrj6wqmnHoDds_hfrds1k"  # ROTATE IMMEDIATELY
CHANNEL_ID = 1468153130700243072
DATA_FILE = "passports.json"
# ============================================

PASSPORT_TYPES = [
    ("Civilian", "🧑 Unarmed Civilian"),
    ("Diplomatic", "🕊️ Diplomat"),
    ("Official", "🏛️ Official")
]

# ---------- PATHS ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
PASSPORT_OUT = os.path.join(BASE_DIR, "generated_passports")

CREST_PATH = os.path.join(ASSETS_DIR, "crest.png")
FONT_REG = os.path.join(FONTS_DIR, "Inter-Regular.ttf")
FONT_BOLD = os.path.join(FONTS_DIR, "Inter-Bold.ttf")
FONT_SEMI = os.path.join(FONTS_DIR, "Inter-SemiBold.ttf")

os.makedirs(PASSPORT_OUT, exist_ok=True)

app = Flask(__name__)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def generate_passport(entry):
    img = Image.new("RGB", (1000, 600), "#f3efe6")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_BOLD, 46)
        label_font = ImageFont.truetype(FONT_SEMI, 26)
        text_font = ImageFont.truetype(FONT_REG, 26)
    except:
        title_font = label_font = text_font = ImageFont.load_default()

    # Header
    draw.text((40, 30), "Republic of Seamhania", fill="#000", font=title_font)
    draw.text((40, 90), "Official Passport Document", fill="#000", font=text_font)

    # Fields
    y = 170
    spacing = 48

    draw.text((40, y), "Minecraft Username:", fill="#000", font=label_font)
    draw.text((360, y), entry["mc_username"], fill="#000", font=text_font)
    y += spacing

    draw.text((40, y), "Discord Username:", fill="#000", font=label_font)
    draw.text((360, y), entry["discord_username"], fill="#000", font=text_font)
    y += spacing

    draw.text((40, y), "Passport Type:", fill="#000", font=label_font)
    draw.text((360, y), entry["type"], fill="#000", font=text_font)
    y += spacing

    draw.text((40, y), "Passport ID:", fill="#000", font=label_font)
    draw.text((360, y), f"SH-{entry['id']:05d}", fill="#000", font=text_font)

    # Crest
    if os.path.exists(CREST_PATH):
        crest = Image.open(CREST_PATH).convert("RGBA")
        crest = crest.resize((180, 180))
        img.paste(crest, (780, 40), crest)

    out_path = os.path.join(PASSPORT_OUT, f"passport_{entry['id']}.png")
    img.save(out_path)
    return out_path


class PassportView(discord.ui.View):
    def __init__(self, app_id):
        super().__init__(timeout=None)
        self.app_id = app_id

    async def finalize(self, interaction, status):
        data = load_data()
        entry = next(e for e in data if e["id"] == self.app_id)
        entry["status"] = status
        save_data(data)

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green() if status == "Approved" else discord.Color.red()
        embed.add_field(name="Final Status", value=status.upper(), inline=False)

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(embed=embed, view=self)

        if status == "Approved":
            img_path = generate_passport(entry)
            await interaction.channel.send(
                content="📎 **Passport generated**\n\n⚠️ **Please DM the user their passport**",
                file=discord.File(img_path)
            )

        await interaction.response.send_message(
            f"Passport {status.lower()}.",
            ephemeral=True
        )

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.finalize(interaction, "Approved")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, emoji="❌")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.finalize(interaction, "Denied")


HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Seamhanian Passport Registry</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;700&display=swap');

* { font-family: Inter, sans-serif; box-sizing: border-box; }

body {
    margin: 0;
    min-height: 100vh;
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
}

.card {
    width: 500px;
    background: rgba(255,255,255,0.12);
    backdrop-filter: blur(22px);
    border-radius: 22px;
    padding: 32px;
    box-shadow: 0 0 45px rgba(0,0,0,0.6);
    animation: fadeIn 0.9s ease;
}

h1 { text-align: center; margin-bottom: 6px; }

.subtitle {
    text-align: center;
    font-size: 14px;
    opacity: 0.75;
    margin-bottom: 26px;
}

label { font-size: 13px; opacity: 0.9; }

select, input, textarea {
    width: 100%;
    margin-top: 6px;
    margin-bottom: 18px;
    padding: 12px;
    border-radius: 12px;
    border: none;
    background: rgba(255,255,255,0.15);
    color: white;
    outline: none;
}

textarea { height: 90px; resize: none; }

button {
    width: 100%;
    padding: 15px;
    border-radius: 16px;
    border: none;
    background: linear-gradient(135deg, #00c6ff, #0072ff);
    color: white;
    font-weight: 700;
    cursor: pointer;
    transition: 0.25s;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 25px rgba(0,0,0,0.45);
}

.footer {
    text-align: center;
    font-size: 11px;
    opacity: 0.6;
    margin-top: 16px;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(25px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
</head>

<body>
<div class="card">
    <h1>🏛️ Seamhania</h1>
    <div class="subtitle">Passport Registry Office (SPRO)</div>

    <form method="POST">
        <label>Passport Type</label>
        <select name="type">
            {% for t, d in types %}
            <option value="{{t}}">{{d}}</option>
            {% endfor %}
        </select>

        <label>Minecraft Username</label>
        <input name="mc_username" required>

        <label>Discord Username</label>
        <input name="discord_username" placeholder="user#0000" required>

        <label>Reason for Request</label>
        <textarea name="reason" required></textarea>

        <button type="submit">Submit Passport Application</button>
    </form>

    <div class="footer">
        Seamhanian Government Authority • Renewal every 5 months
    </div>
</div>
</body>
</html>
"""

# ---------- FLASK ROUTE ----------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = load_data()
        app_id = len(data) + 1

        entry = {
            "id": app_id,
            "type": request.form["type"],
            "mc_username": request.form["mc_username"],
            "discord_username": request.form["discord_username"],
            "reason": request.form["reason"],
            "status": "Pending"
        }

        data.append(entry)
        save_data(data)

        asyncio.run_coroutine_threadsafe(
            send_to_discord(entry),
            bot.loop
        )

        return redirect("/")

    return render_template_string(HTML, types=PASSPORT_TYPES)

# ---------- DISCORD SEND ----------
async def send_to_discord(entry):
    await bot.wait_until_ready()
    channel = await bot.fetch_channel(CHANNEL_ID)

    embed = discord.Embed(
        title="📘 Seamhanian Passport Application",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Type", value=entry["type"], inline=True)
    embed.add_field(name="Minecraft Username", value=entry["mc_username"], inline=True)
    embed.add_field(name="Discord Username", value=entry["discord_username"], inline=True)
    embed.add_field(name="Reason", value=entry["reason"], inline=False)
    embed.add_field(name="Status", value="⏳ Pending", inline=False)

    await channel.send(embed=embed, view=PassportView(entry["id"]))

# ---------- START ----------
def run_flask():
    app.run(host="0.0.0.0", port=5000)

@bot.event
async def on_ready():
    print(f"Seamhania Passport Bot online as {bot.user}")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(BOT_TOKEN)

