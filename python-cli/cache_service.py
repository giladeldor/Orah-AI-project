import json
import os

CACHE_FILE = os.path.join(os.path.dirname(__file__), ".profile_cache.json")

def get_cached_result(username):
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get(username)
    except:
        return None

def set_cached_result(username, data):
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except:
            pass
    cache[username] = data
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
