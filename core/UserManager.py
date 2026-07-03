# core/UserManager.py
from Database import Database
from GrammarEnhancer import GrammarEnhancer
from OfflineDictionary import OfflineDictionary
from AdvancedGrammarChecker import AdvancedGrammarChecker
from PlanManager import PlanManager
from CloudSync import CloudSync
import hashlib
import secrets
from datetime import datetime, timedelta


class UserManager:
    def __init__(self):
        try:
            self.db = Database()
            self.grammar_enhancer = GrammarEnhancer()
            self.offline_dict = OfflineDictionary()
            self.grammar_checker = AdvancedGrammarChecker()
            self.plan_manager = PlanManager(self.db)
            self.cloud = CloudSync()
            self.current_user = None
            print("🎉 UserManager loaded")
        except Exception as e:
            print(f"Error: {e}")
            raise

    def hash_password(self, password):
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}${hash_obj.hex()}"

    def verify_password(self, password, hashed):
        try:
            salt, stored_hash = hashed.split('$')
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return hash_obj.hex() == stored_hash
        except:
            return False

    def register(self, username, email, password):
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pwd_hash = self.hash_password(password)
            sync_token = secrets.token_hex(16)
            self.db.execute_query(
                'INSERT INTO users (username, email, password_hash, created_at, last_active, cloud_sync_token) VALUES (?, ?, ?, ?, ?, ?)',
                (username, email, pwd_hash, now, now, sync_token), commit=True)
            user_id = self.db.execute_query('SELECT last_insert_rowid()', fetchone=True)[0]
            self.db.execute_query('INSERT INTO privacy_settings (user_id, profile_public) VALUES (?, 1)', (user_id,), commit=True)
            # Publish public leaderboard fields (best-effort — ignored if offline)
            self.cloud.upsert_profile(username, sync_token, '😊', 1, 0, 0, 0)
            return True, "Registration successful!"
        except Exception as e:
            if "UNIQUE constraint failed: users.username" in str(e):
                return False, "This username is already taken."
            if "UNIQUE constraint failed: users.email" in str(e):
                return False, "This email is already registered."
            print(f"Register error: {e}")
            return False, "Something went wrong. Please try again."

    def login(self, username, password):
        try:
            row = self.db.execute_query(
                'SELECT id, username, email, password_hash, avatar, plan, daily_goal, current_streak, xp_total, level, cloud_sync_token FROM users WHERE username = ? OR email = ?',
                (username, username), fetchone=True)
            if not row:
                return False, "Incorrect username/email or password.", None
            if not self.verify_password(password, row[3]):
                return False, "Incorrect username/email or password.", None
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute_query("UPDATE users SET last_active = ? WHERE id = ?", (now, row[0]), commit=True)
            user = {
                'id': row[0], 'username': row[1], 'email': row[2],
                'avatar': row[4] or '😊', 'plan': row[5] or 'free',
                'daily_goal': row[6] or 10, 'current_streak': row[7] or 0,
                'xp_total': row[8] or 0, 'level': row[9] or 1,
                'cloud_sync_token': row[10]
            }
            self.current_user = user
            return True, "Welcome back!", user
        except Exception as e:
            print(f"Login error: {e}")
            return False, "Something went wrong. Please try again.", None

    def login_by_id(self, user_id):
        try:
            row = self.db.execute_query(
                'SELECT id, username, email, password_hash, avatar, plan, daily_goal, current_streak, xp_total, level, cloud_sync_token FROM users WHERE id = ?',
                (user_id,), fetchone=True)
            if not row:
                return False
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute_query("UPDATE users SET last_active = ? WHERE id = ?", (now, row[0]), commit=True)
            self.current_user = {
                'id': row[0], 'username': row[1], 'email': row[2],
                'avatar': row[4] or '😊', 'plan': row[5] or 'free',
                'daily_goal': row[6] or 10, 'current_streak': row[7] or 0,
                'xp_total': row[8] or 0, 'level': row[9] or 1,
                'cloud_sync_token': row[10]
            }
            return True
        except Exception as e:
            print(f"Auto login error: {e}")
            return False

    def add_xp(self, user_id, amount):
        pass  # XP removed

    def _sync_to_cloud(self, user_id):
        """Push public leaderboard fields to Supabase, if the user opted in."""
        if not self.current_user or self.current_user['id'] != user_id:
            return
        privacy = self.get_privacy_settings(user_id)
        if not privacy['profile_public']:
            return
        token = self.current_user.get('cloud_sync_token')
        if not token:
            return
        progress = self.get_daily_progress(user_id)
        self.cloud.upsert_profile(
            self.current_user['username'], token, self.current_user['avatar'],
            self.current_user['level'], self.current_user['xp_total'],
            self.current_user['current_streak'], progress['words_learned']
        )

    def get_daily_progress(self, user_id):
        today = datetime.now().strftime("%Y-%m-%d")
        row = self.db.execute_query(
            'SELECT COALESCE(words_learned,0), COALESCE(grammar_learned,0), COALESCE(minutes_studied,0), COALESCE(goal_achieved,0) FROM daily_progress WHERE user_id=? AND date=?',
            (user_id, today), fetchone=True)
        if row:
            return {'words_learned': row[0], 'grammar_learned': row[1], 'minutes_studied': row[2], 'goal_achieved': bool(row[3])}
        return {'words_learned': 0, 'grammar_learned': 0, 'minutes_studied': 0, 'goal_achieved': False}

    def update_daily_progress(self, user_id, words_added=0, grammar_added=0, minutes=0, phrases_added=0):
        today = datetime.now().strftime("%Y-%m-%d")
        self.db.execute_query(
            '''INSERT INTO daily_progress (user_id, date, words_learned, grammar_learned, minutes_studied)
               VALUES (?,?,?,?,?) ON CONFLICT(user_id,date) DO UPDATE SET
               words_learned = words_learned + ?, grammar_learned = grammar_learned + ?, minutes_studied = minutes_studied + ?''',
            (user_id, today, words_added, grammar_added, minutes, words_added, grammar_added, minutes), commit=True)
        self._sync_to_cloud(user_id)
        return True

    def update_profile(self, user_id, **kwargs):
        for key, value in kwargs.items():
            if key in ['avatar', 'daily_goal']:
                self.db.execute_query(f"UPDATE users SET {key}=? WHERE id=?", (value, user_id), commit=True)
        if 'avatar' in kwargs and self.current_user and self.current_user['id'] == user_id:
            self.current_user['avatar'] = kwargs['avatar']
            self._sync_to_cloud(user_id)

    def add_vocabulary(self, user_id, word, meaning, example, language, difficulty, tags, notes):
        today = datetime.now().strftime("%Y-%m-%d")
        next_review = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.db.execute_query(
            'INSERT INTO vocabulary (user_id, word, meaning, example, language, difficulty, next_review, tags, date_added, notes, error_count) VALUES (?,?,?,?,?,?,?,?,?,?,0)',
            (user_id, word, meaning, example, language, difficulty, next_review, tags, today, notes), commit=True)
        self.update_daily_progress(user_id, words_added=1)
        return self.db.execute_query('SELECT last_insert_rowid()', fetchone=True)[0]

    def get_vocabulary(self, user_id, filters=None):
        query = "SELECT * FROM vocabulary WHERE user_id = ?"
        params = [user_id]
        if filters:
            if filters.get('search'):
                query += " AND (word LIKE ? OR meaning LIKE ?)"
                params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])
            if filters.get('language') and filters['language'] != 'All':
                query += " AND language = ?"
                params.append(filters['language'])
            if filters.get('difficulty') and filters['difficulty'] != 'All':
                query += " AND difficulty = ?"
                params.append(filters['difficulty'])
        query += " ORDER BY date_added DESC"
        return self.db.execute_query(query, params, fetchall=True)

    def update_vocabulary(self, vocab_id, word, meaning, example, language, difficulty):
        self.db.execute_query(
            'UPDATE vocabulary SET word=?, meaning=?, example=?, language=?, difficulty=? WHERE id=?',
            (word, meaning, example, language, difficulty, vocab_id), commit=True)

    def delete_vocabulary(self, vocab_id):
        self.db.execute_query("DELETE FROM vocabulary WHERE id=?", (vocab_id,), commit=True)

    def add_phrase(self, user_id, phrase, meaning, tags, notes):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute_query(
            'INSERT INTO phrases (user_id, phrase, meaning, tags, notes, date_added, practice_count) VALUES (?,?,?,?,?,?,0)',
            (user_id, phrase, meaning, tags, notes, now), commit=True)
        self.update_daily_progress(user_id, words_added=1)
        return self.db.execute_query('SELECT last_insert_rowid()', fetchone=True)[0]

    def get_phrases(self, user_id, search=None):
        if search:
            return self.db.execute_query(
                'SELECT * FROM phrases WHERE user_id=? AND (phrase LIKE ? OR meaning LIKE ? OR tags LIKE ?) ORDER BY date_added DESC',
                (user_id, f"%{search}%", f"%{search}%", f"%{search}%"), fetchall=True)
        else:
            return self.db.execute_query('SELECT * FROM phrases WHERE user_id=? ORDER BY date_added DESC', (user_id,), fetchall=True)

    def update_phrase(self, phrase_id, phrase, meaning, tags, notes):
        self.db.execute_query(
            'UPDATE phrases SET phrase=?, meaning=?, tags=?, notes=? WHERE id=?',
            (phrase, meaning, tags, notes, phrase_id), commit=True)

    def delete_phrase(self, phrase_id):
        self.db.execute_query('DELETE FROM phrases WHERE id=?', (phrase_id,), commit=True)

    def increment_phrase_practice(self, phrase_id):
        self.db.execute_query(
            'UPDATE phrases SET practice_count = practice_count + 1, last_practiced = ? WHERE id=?',
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), phrase_id), commit=True)

    def save_practice_message(self, user_id, message, corrected=None, suggestions=None):
        self.db.execute_query(
            'INSERT INTO practice_chat (user_id, message, corrected_text, suggestions, timestamp) VALUES (?,?,?,?,?)',
            (user_id, message, corrected, suggestions, datetime.now().strftime("%Y-%m-%d %H:%M:%S")), commit=True)

    def get_practice_history(self, user_id):
        return self.db.execute_query(
            'SELECT message, corrected_text, suggestions, timestamp FROM practice_chat WHERE user_id=? ORDER BY timestamp DESC LIMIT 50',
            (user_id,), fetchall=True)

    def check_grammar_offline(self, text):
        return self.grammar_checker.check_and_correct(text)

    def get_grammar_info(self, topic):
        return self.grammar_enhancer.get_grammar_info(topic)

    def get_all_grammar_topics(self):
        return self.grammar_enhancer.get_all_topics()

    def search_grammar_rules(self, query):
        return self.grammar_enhancer.search_grammar(query)

    def get_grammar_by_level(self, level):
        return self.grammar_enhancer.get_rules_by_level(level)

    def add_grammar_favorite(self, topic):
        return self.grammar_enhancer.add_favorite(topic)

    def remove_grammar_favorite(self, topic):
        return self.grammar_enhancer.remove_favorite(topic)

    def get_grammar_favorites(self):
        return self.grammar_enhancer.get_favorites()

    def is_grammar_favorite(self, topic):
        return self.grammar_enhancer.is_favorite(topic)

    def get_grammar_notes(self, topic):
        return self.grammar_enhancer.get_notes(topic)

    def save_grammar_note(self, topic, note):
        self.grammar_enhancer.save_note(topic, note)

    def get_grammar_stats(self):
        return self.grammar_enhancer.get_grammar_stats()

    def get_user_plan(self, user_id):
        return self.plan_manager.get_user_plan(user_id)

    def update_user_plan(self, user_id, plan_type, **kwargs):
        self.plan_manager.update_plan(user_id, plan_type, **kwargs)

    def get_plan_progress(self, user_id, today_stats):
        return self.plan_manager.get_plan_progress(user_id, today_stats)

    def get_leaderboard(self, limit=10):
        """Cross-device leaderboard, backed by Supabase. Returns [] if offline."""
        rows = self.cloud.get_leaderboard(limit)
        return [(r['username'], r['avatar'], r['level'], r['today_words']) for r in rows]

    def search_users(self, query, current_user_id):
        """Cross-device username search, backed by Supabase. Returns [] if offline."""
        exclude = self.current_user['username'] if self.current_user else ""
        rows = self.cloud.search_profiles(query, exclude)
        return [(r['username'], r['username'], r['avatar'], r['level'], r['xp_total']) for r in rows]

    def get_user_public_profile(self, target_username):
        profile = self.cloud.get_profile(target_username)
        if profile is None:
            return None, "User not found, is offline-only, or has a private profile"
        return {
            'username': profile['username'], 'avatar': profile['avatar'],
            'level': profile['level'], 'streak': profile['current_streak'],
            'today_words': profile['today_words']
        }, None

    def get_privacy_settings(self, user_id):
        row = self.db.execute_query("SELECT profile_public FROM privacy_settings WHERE user_id=?", (user_id,), fetchone=True)
        return {'profile_public': bool(row[0])} if row else {'profile_public': True}

    def update_privacy(self, user_id, profile_public):
        self.db.execute_query("UPDATE privacy_settings SET profile_public=? WHERE user_id=?", (profile_public, user_id), commit=True)
        if self.current_user and self.current_user['id'] == user_id:
            token = self.current_user.get('cloud_sync_token')
            if profile_public:
                self._sync_to_cloud(user_id)
            elif token:
                self.cloud.remove_profile(self.current_user['username'], token)

    def close(self):
        self.db.close()
