import re
import aiohttp
import json
import discord
from discord.ext import commands
from pathlib import Path
import google.generativeai as genai

json_dir = Path(__file__).resolve().parents[1] / "json"

class Gemini(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_history = {}
        self.DMC_on = False

    with open(json_dir / "Setting.json", "r", encoding="utf8") as jfile:
        Setting = json.load(jfile)

    with open(json_dir / "Token.json", "r", encoding="utf8") as jfile:
        Token = json.load(jfile)

    GOOGLE_AI_KEY = Token["Google_AI_Key"]  
    MAX_HISTORY = int(Setting["Max_History"])

    genai.configure(api_key=GOOGLE_AI_KEY)
    text_generation_config = {
        "temperature": 0.9,
        "top_p": 1, 
        "top_k": 1,
        "max_output_tokens": 512,
    }
    image_generation_config = {
        "temperature": 0.4,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 512,
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]
    text_model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=text_generation_config, safety_settings=safety_settings)
    image_model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=image_generation_config, safety_settings=safety_settings)

    prompt_parts = "\n".join(Setting["Gemini_Prompt"])

    @commands.Cog.listener()
    async def on_message(self, message):
      
        if message.author == self.bot.user:
            return

        if self.bot.user.mentioned_in(message) or (self.DMC_on and isinstance(message.channel, discord.DMChannel)):
       
            cleaned_text = self.clean_discord_message(message.content)
       
            async with message.channel.typing():
        
                if message.attachments:
            
                    for attachment in message.attachments:
                
                        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    
                            async with aiohttp.ClientSession() as session:
                                async with session.get(attachment.url) as resp:
                                
                                    if resp.status != 200:
                                        await message.channel.send('Unable to download image')
                                        return
                                    
                                    image_data = await resp.read()
                                    response = await self.generate_response_with_image_and_text(image_data, cleaned_text)  
                                    await self.split_and_send_messages(message, response, 1700)
                                    return
                                
                else:
            
                    if "RESET" in cleaned_text: 
                
                        if message.author.id in self.message_history:
                            del self.message_history[message.author.id]
                        
                        await message.channel.send("🤖 歷史記錄重置")  
                        return
                        
                    await message.add_reaction('💬')
                
                    if self.MAX_HISTORY == 0:
                
                        response = await self.generate_response_with_text(cleaned_text)
                        await self.split_and_send_messages(message, response, 1700)  
                        return
                
                    self.update_message_history(message.author.id, cleaned_text)  
                    history = self.get_formatted_message_history(message.author.id)
                
                    response = await self.generate_response_with_text(history)
                    self.update_message_history(message.author.id, response)   
                    await self.split_and_send_messages(message, response, 1700)

    async def generate_response_with_text(self, message):
        with open(json_dir / "Setting.json", "r", encoding="utf8") as jfile:
            Setting = json.load(jfile)
        prompt_parts = "\n".join(Setting["Gemini_Prompt"] + [message])
    
        response = self.text_model.generate_content(prompt_parts)
    
        if response._error:
            return f"❌ {response._error}"
        
        return response.text
  
    async def generate_response_with_image_and_text(self, image_data, text):
        image_parts = [{"mime_type": "image/jpeg", "data": image_data}]  
        prompt_parts = [image_parts[0], f"\n{text if text else '這是什麼樣的圖片？'}"]
    
        response = self.image_model.generate_content(prompt_parts)
    
        if response._error:
            return f"❌ {response._error}"
        
        return response.text  

    def update_message_history(self, user_id, text):
        if user_id in self.message_history:
            self.message_history[user_id].append(text)
            if len(self.message_history[user_id]) > self.MAX_HISTORY:
                self.message_history[user_id].pop(0)
        else:
            self.message_history[user_id] = [text]

    def get_formatted_message_history(self, user_id):
        if user_id in self.message_history:
            return "\n\n".join(self.message_history[user_id])
        else:
            return "No message history"  

    async def split_and_send_messages(self, message, text, max_length):
        messages = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    
        for msg in messages: 
            await message.channel.send(msg)
        
    def clean_discord_message(self, input_string):
        pattern = re.compile(r"<[^>]+>")
        return pattern.sub("", input_string)
    
    @commands.slash_command(description="管理Gemini在私訊時是否直接回覆")
    @discord.option("action", type=discord.SlashCommandOptionType.string, description="on/off")
    async def gemini_private_management(self, ctx, action: str):
        if ctx.author.guild_permissions.administrator:
            if action.lower() == "on":
                self.DMC_on = True
                await ctx.respond("已啟用Gemini私訊時的直接觸發")
       
            elif action.lower() == "off":
                self.DMC_on = False
                await ctx.respond("已暫時關閉Gemini私訊時的直接觸發")

            else:
                await ctx.respond("請輸入正確的動作(on/off)")
        else:
            await ctx.respond("你沒有管理者權限用來執行這個指令")

def setup(bot):
    bot.add_cog(Gemini(bot))