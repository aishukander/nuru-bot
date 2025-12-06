import re
import aiohttp
import tomllib
import discord
from discord.ext import commands
from pathlib import Path
from google import genai as gemini
from functools import wraps

toml_dir = Path(__file__).resolve().parents[1] / "toml"

def Owner_Examine(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        if ctx.author.id == int(self.token['Owner_ID']):
            return await func(self, ctx, *args, **kwargs)
        else:
            await ctx.respond("你沒有權限執行這個指令", ephemeral=True)
    return wrapper

class Gemini(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_history = {}
        self.dmc_on = False

        with open(toml_dir / "Setting.toml", "rb") as tfile:
            self.setting = tomllib.load(tfile)
        with open(toml_dir / "Token.toml", "rb") as tfile:
            self.token = tomllib.load(tfile)

        self.client = gemini.Client(api_key=self.token["Google_AI_Key"])
        self.max_history = int(self.setting["Max_History"])
        self.safety_settings = [
            gemini.types.SafetySetting(
                category=gemini.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=gemini.types.HarmBlockThreshold.BLOCK_NONE,
            ),
            gemini.types.SafetySetting(
                category=gemini.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=gemini.types.HarmBlockThreshold.BLOCK_NONE,
            ),
            gemini.types.SafetySetting(
                category=gemini.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=gemini.types.HarmBlockThreshold.BLOCK_NONE,
            ),
            gemini.types.SafetySetting(
                category=gemini.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=gemini.types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ]
        self.text_generation_config = gemini.types.GenerateContentConfig(
            temperature=0.9,
            top_p=1,
            top_k=1,
            max_output_tokens=self.setting["Gemini_Max_Tokens"],
            safety_settings=self.safety_settings,
        )
        self.image_generation_config = gemini.types.GenerateContentConfig(
            temperature=0.4,
            top_p=1,
            top_k=32,
            max_output_tokens=self.setting["Gemini_Max_Tokens"],
            safety_settings=self.safety_settings,
        )
        self.prompt_parts = "\n".join(self.setting["Gemini_Prompt"])

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

    def validate_response(self, response):
        if not response.candidates:
            return "❌ No valid response candidates were returned."

        candidate = response.candidates[0]

        text_content = ""
        try:
            if response.text:
                text_content = response.text
        except Exception:
            pass

        if not text_content and candidate.content and candidate.content.parts:
            text_content = "".join(part.text for part in candidate.content.parts if part.text)

        return f"❌ Response generation was incomplete. Finish reason: {candidate.finish_reason}"

    async def generate_response_with_text(self, message):
        prompt_parts = "\n".join(self.setting["Gemini_Prompt"] + [message])
        try:
            response = self.client.models.generate_content(
                model=self.setting["Gemini_Text_Name"],
                contents=prompt_parts,
                config=self.text_generation_config
            )
        except Exception as e:
            return f"❌ {str(e)}"
        return self.validate_response(response)

    async def generate_response_with_image_and_text(self, image_data, text, mime_type):
        try:
            image_part = gemini.types.Part(
                inline_data=gemini.types.Blob(
                    data=image_data,
                    mime_type=mime_type
                )
            )
            prompt_text = text if text else '這是什麼樣的圖片？'
            prompt_parts = [prompt_text, image_part]
            response = self.client.models.generate_content(
                model=self.setting["Gemini_Image_Name"],
                contents=prompt_parts,
                config=self.image_generation_config
            )
        except Exception as e:
            return f"❌ {str(e)}"
        return self.validate_response(response)

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
        # use rfind to split at the last newline before max_length
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
        match filename.lower().split('.')[-1]:
            case "png":
                return "image/png"
            case "gif":
                return "image/gif"
            case "webp":
                return "image/webp"
            case _:
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
    @Owner_Examine
    async def gemini_private(self, ctx, action: str):
        if action.lower() == "on":
            self.dmc_on = True
            await ctx.respond("已啟用Gemini私訊時的觸發", ephemeral=True)
        elif action.lower() == "off":
            self.dmc_on = False
            await ctx.respond("已關閉Gemini私訊時的觸發", ephemeral=True)
        else:
            await ctx.respond("請輸入正確的動作(on/off)", ephemeral=True)

def setup(bot):
    bot.add_cog(Gemini(bot))
