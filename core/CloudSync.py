# core/CloudSync.py
"""
Handles the ONLY data that ever leaves the phone: public leaderboard
fields (username, avatar, level, streak, today's word count).
Vocabulary, phrases, grammar notes and passwords never touch this module.

If the device is offline, or Supabase is unreachable, every method fails
silently (returns None / empty list) so the rest of the app keeps working.
"""
import requests

# TODO: paste your own values from Supabase → Project Settings → API
SUPABASE_URL = "https://hbbyketrqyzgyduytjai.supabase.co/rest/v1/"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhiYnlrZXRycXl6Z3lkdXl0amFpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMwNDM3OTMsImV4cCI6MjA5ODYxOTc5M30.CY57nZrRNXxN3zbhxRWic-tah5nWPKwk6QkbYO0TqfA"

TIMEOUT = 6  # seconds — fail fast, don't freeze the UI on bad connections


class CloudSync:
    def __init__(self, url=SUPABASE_URL, anon_key=SUPABASE_ANON_KEY):
        self.base = f"{url}/rest/v1/rpc"
        self.headers = {
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
            "Content-Type": "application/json",
        }

    def _call(self, function_name, payload):
        try:
            resp = requests.post(f"{self.base}/{function_name}",
                                  json=payload, headers=self.headers, timeout=TIMEOUT)
            if resp.status_code >= 400:
                print(f"CloudSync error [{function_name}]: {resp.status_code} {resp.text}")
                return None
            return resp.json() if resp.text else True
        except requests.RequestException as e:
            print(f"CloudSync network error [{function_name}]: {e}")
            return None

    def upsert_profile(self, username, sync_token, avatar, level, xp_total, streak, today_words):
        return self._call("upsert_leaderboard_profile", {
            "p_username": username,
            "p_sync_token": sync_token,
            "p_avatar": avatar,
            "p_level": level,
            "p_xp": xp_total,
            "p_streak": streak,
            "p_today_words": today_words,
        })

    def remove_profile(self, username, sync_token):
        return self._call("remove_leaderboard_profile", {
            "p_username": username,
            "p_sync_token": sync_token,
        })

    def get_leaderboard(self, limit=50):
        result = self._call("get_leaderboard", {"p_limit": limit})
        return result if result else []

    def search_profiles(self, query, exclude_username):
        result = self._call("search_leaderboard_profiles", {
            "p_query": query,
            "p_exclude_username": exclude_username,
        })
        return result if result else []

    def get_profile(self, username):
        result = self._call("get_leaderboard_profile", {"p_username": username})
        return result[0] if result else None
