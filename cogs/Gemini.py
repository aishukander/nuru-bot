import re
import json

import aiohttp
import discord
from discord.ext import commands
from core.classes import Cog_Extension

import google.generativeai as genai

class Gemini(Cog_Extension):
  
    def __init__(self, bot):
        self.bot = bot
        self.message_history = {}

    with open('token.json','r',encoding='utf8') as tfile:
        TOKEN = json.load(tfile)

    GOOGLE_AI_KEY = TOKEN["GOOGLE_AI_KEY"]  
    MAX_HISTORY = int(TOKEN["MAX_HISTORY"])

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
    text_model = genai.GenerativeModel(model_name="gemini-pro", generation_config=text_generation_config, safety_settings=safety_settings)
    image_model = genai.GenerativeModel(model_name="gemini-pro-vision", generation_config=image_generation_config, safety_settings=safety_settings)

    @commands.Cog.listener()
    async def on_message(self, message):  
      
        if message.author == self.bot.user:
            return

        if self.bot.user.mentioned_in(message):
       
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
        prompt_parts = [message]
        print(f"Got text prompt: {message}")
    
        response = self.text_model.generate_content(prompt_parts)
    
        if response._error:
            return f"❌ {response._error}"
        
        return response.text
  
    async def generate_response_with_image_and_text(self, image_data, text):
        image_parts = [{"mime_type": "image/jpeg", "data": image_data}]  
        prompt_parts = [image_parts[0], f"\n{text if text else 'What is this a picture of?'}"]
    
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

async def setup(bot):
    await bot.add_cog(Gemini(bot))