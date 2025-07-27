import re
import aiohttp
import tomllib
import discord
from discord.ext import commands
from pathlib import Path
import google.generativeai as gemini
from functools import wraps

toml_dir = Path(__file__).resolve().parents[1] / "toml"

class Gemini(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_history = {}
        self.dmc_on = False

        with open(toml_dir / "Setting.toml", "rb") as tfile:
            self.setting = tomllib.load(tfile)
        with open(toml_dir / "Token.toml", "rb") as tfile:
            self.token = tomllib.load(tfile)

        self.google_ai_key = self.token["Google_AI_Key"]
        self.max_history = int(self.setting["Max_History"])

        gemini.configure(api_key=self.google_ai_key)
        self.text_generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 512,
        }
        self.image_generation_config = {
            "temperature": 0.4,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 512,
        }
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
        self.text_model = gemini.GenerativeModel(
            model_name=self.setting["Gemini_Text_Name"],
            generation_config=self.text_generation_config,
            safety_settings=self.safety_settings
        )
        self.image_model = gemini.GenerativeModel(
            model_name=self.setting["Gemini_Image_Name"],
            generation_config=self.image_generation_config,
            safety_settings=self.safety_settings
        )
        self.prompt_parts = "\n".join(self.setting["Gemini_Prompt"])

    @staticmethod
    def Guild_Admin_Examine(func):
            @wraps(func)
            async def wrapper(self, ctx, *args, **kwargs):
                try:
                    if ctx.author.guild_permissions.administrator:
                        return await func(self, ctx, *args, **kwargs)
                    else:
                        await ctx.respond("你沒有管理者權限用來執行這個指令", ephemeral=True)
                except AttributeError:
                    await ctx.respond("你不在伺服器內")
            return wrapper

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if (
            (self.bot.user.mentioned_in(message) and not message.mention_everyone)
            or (self.dmc_on and isinstance(message.channel, discord.DMChannel))
        ):
            cleaned_text = self.clean_discord_message(message.content)
            async with message.channel.typing():
                if message.attachments:
                    for attachment in message.attachments:
                        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                            mime_type = self.get_mime_type(attachment.filename)
                            async with aiohttp.ClientSession() as session:
                                async with session.get(attachment.url) as resp:
                                    if resp.status != 200:
                                        await message.channel.send('Unable to download image')
                                        return
                                    image_data = await resp.read()
                                    response = await self.generate_response_with_image_and_text(image_data, cleaned_text, mime_type)
                                    await self.split_and_send_messages(message, response, 1700)
                                    return
                else:
                    await message.add_reaction('💬')
                    if self.max_history == 0:
                        response = await self.generate_response_with_text(cleaned_text)
                        await self.split_and_send_messages(message, response, 1700)
                        return
                    self.update_message_history(message.author.id, cleaned_text)
                    history = self.get_formatted_message_history(message.author.id)
                    response = await self.generate_response_with_text(history)
                    self.update_message_history(message.author.id, response)
                    await self.split_and_send_messages(message, response, 1700)

    async def generate_response_with_text(self, message):
        prompt_parts = "\n".join(self.setting["Gemini_Prompt"] + [message])
        try:
            response = self.text_model.generate_content(prompt_parts)
        except Exception as e:
            return f"❌ {str(e)}"
        if hasattr(response, "_error") and response._error:
            return f"❌ {response._error}"
        return getattr(response, "text", str(response))

    async def generate_response_with_image_and_text(self, image_data, text, mime_type):
        image_parts = [{"mime_type": mime_type, "data": image_data}]
        prompt_parts = [image_parts[0], f"\n{text if text else '這是什麼樣的圖片？'}"]
        try:
            response = self.image_model.generate_content(prompt_parts)
        except Exception as e:
            return f"❌ {str(e)}"
        if hasattr(response, "_error") and response._error:
            return f"❌ {response._error}"
        return getattr(response, "text", str(response))

    def update_message_history(self, user_id, text):
        if user_id in self.message_history:
            self.message_history[user_id].append(text)
            if len(self.message_history[user_id]) > self.max_history:
                self.message_history[user_id].pop(0)
        else:
            self.message_history[user_id] = [text]

    def get_formatted_message_history(self, user_id):
        if user_id in self.message_history:
            return "\n\n".join(self.message_history[user_id])
        else:
            return "No message history"

    async def split_and_send_messages(self, message, text, max_length):
        # 優先用換行切割
        messages = []
        while len(text) > max_length:
            split_pos = text.rfind('\n', 0, max_length)
            if split_pos == -1:
                split_pos = max_length
            messages.append(text[:split_pos])
            text = text[split_pos:]
        if text:
            messages.append(text)
        for msg in messages:
            await message.channel.send(msg)

    def clean_discord_message(self, input_string):
        pattern = re.compile(r"<[^>]+>")
        return pattern.sub("", input_string)

    def get_mime_type(self, filename):
        ext = filename.lower().split('.')[-1]
        if ext == "png":
            return "image/png"
        elif ext == "gif":
            return "image/gif"
        elif ext == "webp":
            return "image/webp"
        else:
            return "image/jpeg"

    @commands.slash_command(
        description="重置你的歷史訊息記錄",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    async def gemini_reset(self, ctx):
        if ctx.author.id in self.message_history:
            del self.message_history[ctx.author.id]
        await ctx.respond("🤖 歷史記錄重置", ephemeral=True)

    @commands.slash_command(description="管理Gemini在私訊時是否直接回覆")
    @discord.option(
        "action",
        type=discord.SlashCommandOptionType.string,
        description="on/off",
        choices=["on", "off"]
    )
    @Guild_Admin_Examine
    async def gemini_private(self, ctx, action: str):
        if action.lower() == "on":
            self.dmc_on = True
            await ctx.respond("已啟用Gemini私訊時的直接觸發", ephemeral=True)
        elif action.lower() == "off":
            self.dmc_on = False
            await ctx.respond("已暫時關閉Gemini私訊時的直接觸發", ephemeral=True)
        else:
            await ctx.respond("請輸入正確的動作(on/off)", ephemeral=True)

def setup(bot):
    bot.add_cog(Gemini(bot))