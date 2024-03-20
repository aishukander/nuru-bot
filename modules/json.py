import os
import json

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
setting_json_path = os.path.join(root_dir, "json", "Setting.json")
token_json_path = os.path.join(root_dir, "json", "Token.json")
DynamicVoice_ID_json_path = os.path.join(root_dir, "json", "DynamicVoiceID.json")
DynamicVoice_Name_json_path = os.path.join(root_dir, "json", "DynamicVoiceName.json")
words_json_path = os.path.join(root_dir, "json", "Words.json")

def open_setting_json():
    with open(setting_json_path,"r",encoding="utf8") as jfile:
        return json.load(jfile)
    
def open_token_json():
    with open(token_json_path,"r",encoding="utf8") as tfile:
        return json.load(tfile)

def open_words_json():
    with open(words_json_path,"r",encoding="utf8") as f:
        return json.load(f)

def dump_words(words):
    with open(words_json_path,"w",encoding="utf8") as f:
        json.dump(words, f)

def open_DynamicVoice_Name_json():
    global DynamicVoiceName
    with open(DynamicVoice_Name_json_path,"r",encoding="utf8") as jfile:
        return json.load(jfile)

def open_DynamicVoice_ID_json():
    with open(DynamicVoice_ID_json_path,"r",encoding="utf8") as f:
        return json.load(f)

def dump_DynamicVoice_Name_json():
    with open(DynamicVoice_Name_json_path,"w",encoding="utf8") as f:
        json.dump(DynamicVoiceName, f, ensure_ascii=False, indent=4)

def save_DynamicVoice_ID_json(origin_channels):
    if not origin_channels:
        json_str = "{}" 
    else:
        data = {}
        formatted_data = ""
        for guild_id, channel_ids in origin_channels.items():
            formatted_data += f'\n"{guild_id}": {channel_ids},'

        json_str = "{" + formatted_data[:-1] + "\n}"

    with open(DynamicVoice_ID_json_path,"w",encoding="utf8") as f:
        f.write(json_str)