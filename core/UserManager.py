# core/UserManager.py
from Database import Database
from GrammarEnhancer import GrammarEnhancer
from OfflineDictionary import OfflineDictionary
from AdvancedGrammarChecker import AdvancedGrammarChecker
from PlanManager import PlanManager
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
            self.db.execute_query(
                'INSERT INTO users (username, email, password_hash, created_at, last_active) VALUES (?, ?, ?, ?, ?)',
                (username, email, pwd_hash, now, now), commit=True)
            user_id = self.db.execute_query('SELECT last_insert_rowid()', fetchone=True)[0]
            self.db.execute_query('INSERT INTO privacy_settings (user_id, profile_public) VALUES (?, 1)', (user_id,), commit=True)
            return True, "Registration successful!"
        except Exception as e:
            return False, str(e)

    def login(self, username, password):
        try:
            row = self.db.execute_query(
                'SELECT id, username, email, password_hash, avatar, plan, daily_goal, current_streak, xp_total, level FROM users WHERE username = ? OR email = ?',
                (username, username), fetchone=True)
            if not row:
                return False, "User not found", None
            if not self.verify_password(password, row[3]):
                return False, "Wrong password", None
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute_query("UPDATE users SET last_active = ? WHERE id = ?", (now, row[0]), commit=True)
            user = {
                'id': row[0], 'username': row[1], 'email': row[2],
                'avatar': row[4] or '😊', 'plan': row[5] or 'free',
                'daily_goal': row[6] or 10, 'current_streak': row[7] or 0,
                'xp_total': row[8] or 0, 'level': row[9] or 1
            }
            self.current_user = user
            return True, "Welcome back!", user
        except Exception as e:
            return False, str(e), None

    def login_by_id(self, user_id):
        try:
            row = self.db.execute_query(
                'SELECT id, username, email, password_hash, avatar, plan, daily_goal, current_streak, xp_total, level FROM users WHERE id = ?',
                (user_id,), fetchone=True)
            if not row:
                return False
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute_query("UPDATE users SET last_active = ? WHERE id = ?", (now, row[0]), commit=True)
            self.current_user = {
                'id': row[0], 'username': row[1], 'email': row[2],
                'avatar': row[4] or '😊', 'plan': row[5] or 'free',
                'daily_goal': row[6] or 10, 'current_streak': row[7] or 0,
                'xp_total': row[8] or 0, 'level': row[9] or 1
            }
            return True
        except Exception as e:
            print(f"Auto login error: {e}")
            return False

    def add_xp(self, user_id, amount):
        pass  # XP removed

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
        return True

    def update_profile(self, user_id, **kwargs):
        for key, value in kwargs.items():
            if key in ['avatar', 'daily_goal']:
                self.db.execute_query(f"UPDATE users SET {key}=? WHERE id=?", (value, user_id), commit=True)

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
        today = datetime.now().strftime("%Y-%m-%d")
        return self.db.execute_query(
            '''SELECT u.username, u.avatar, u.level, COALESCE(dp.words_learned,0) as score
               FROM users u LEFT JOIN daily_progress dp ON u.id=dp.user_id AND dp.date=?
               ORDER BY score DESC, u.level DESC LIMIT ?''',
            (today, limit), fetchall=True)

    def search_users(self, query, current_user_id):
        return self.db.execute_query(
            'SELECT id, username, avatar, level, xp_total FROM users WHERE username LIKE ? AND id != ? LIMIT 20',
            (f"%{query}%", current_user_id), fetchall=True)

    def get_user_public_profile(self, target_id):
        row = self.db.execute_query(
            '''SELECT u.username, u.avatar, u.level, u.xp_total, u.current_streak, COALESCE(p.profile_public,1) as is_public
               FROM users u LEFT JOIN privacy_settings p ON u.id=p.user_id WHERE u.id=?''',
            (target_id,), fetchone=True)
        if not row:
            return None, "User not found"
        if not row[5]:
            return None, "This user's profile is private"
        today = datetime.now().strftime("%Y-%m-%d")
        progress = self.db.execute_query(
            'SELECT words_learned, goal_achieved FROM daily_progress WHERE user_id=? AND date=?',
            (target_id, today), fetchone=True)
        return {
            'username': row[0], 'avatar': row[1], 'level': row[2],
            'xp': row[3], 'streak': row[4],
            'today_words': progress[0] if progress else 0,
            'goal_achieved': progress[1] if progress else False
        }, None

    def get_privacy_settings(self, user_id):
        row = self.db.execute_query("SELECT profile_public FROM privacy_settings WHERE user_id=?", (user_id,), fetchone=True)
        return {'profile_public': bool(row[0])} if row else {'profile_public': True}

    def update_privacy(self, user_id, profile_public):
        self.db.execute_query("UPDATE privacy_settings SET profile_public=? WHERE user_id=?", (profile_public, user_id), commit=True)

    def close(self):
        self.db.close()
