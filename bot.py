
import os
import discord
from discord import app_commands
from discord.ext import commands
from google import genai

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
OWNER_IDS = {
    int(x.strip())
    for x in os.getenv("OWNER_IDS", "").split(",")
    if x.strip().isdigit()
}

ai = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Бот запущен: {bot.user}")


def is_owner(interaction: discord.Interaction):
    return interaction.user.id in OWNER_IDS


@bot.tree.command(name="ask", description="Спросить ИИ")
@app_commands.describe(prompt="Что нужно сделать?")
async def ask(interaction: discord.Interaction, prompt: str):
    if not is_owner(interaction):
        await interaction.response.send_message(
            "⛔ Эта команда доступна только владельцу.",
            ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True)

    try:
        response = ai.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        answer = response.text or "ИИ не вернул ответ."
        for start in range(0, len(answer), 1900):
            await interaction.followup.send(answer[start:start + 1900])
    except Exception as exc:
        await interaction.followup.send(
            f"Ошибка ИИ: {str(exc)[:500]}"
        )


@bot.tree.command(name="create_channel", description="Создать текстовый канал")
@app_commands.describe(name="Название нового канала")
async def create_channel(interaction: discord.Interaction, name: str):
    if not is_owner(interaction):
        await interaction.response.send_message(
            "⛔ Нет доступа.", ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Создать канал **{name}**?",
        view=ConfirmCreate(name),
        ephemeral=True
    )


class ConfirmCreate(discord.ui.View):
    def __init__(self, name):
        super().__init__(timeout=60)
        self.channel_name = name

    @discord.ui.button(label="Подтвердить", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        if not is_owner(interaction):
            await interaction.response.send_message("Нет доступа.", ephemeral=True)
            return
        channel = await interaction.guild.create_text_channel(
            self.channel_name,
            reason=f"Подтверждено владельцем {interaction.user}"
        )
        await interaction.response.edit_message(
            content=f"✅ Создан канал {channel.mention}",
            view=None
        )
        self.stop()

    @discord.ui.button(label="Отмена", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            content="Действие отменено.",
            view=None
        )
        self.stop()


@bot.tree.command(name="help_ai", description="Помощь по командам")
async def help_ai(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Discord AI Admin Bot**\n"
        "`/ask` — задать вопрос ИИ\n"
        "`/create_channel` — создать канал с подтверждением\n"
        "`/help_ai` — помощь",
        ephemeral=True
    )


bot.run(DISCORD_TOKEN)
