import os
import json

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
setting_json_path = os.path.join(root_dir, "json", "Setting.json")
token_json_path = os.path.join(root_dir, "json", "Token.json")
DynamicVoice_ID_json_path = os.path.join(root_dir, "json", "DynamicVoiceID.json")
DynamicVoice_Name_json_path = os.path.join(root_dir, "json", "DynamicVoiceName.json")
words_json_path = os.path.join(root_dir, "json", "Words.json")

def open_json(path):
    with open(path,"r",encoding="utf8") as jfile:
        return json.load(jfile)

def dump_json(path, name):
    with open(path,"w",encoding="utf8") as f:
        json.dump(name, f)

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