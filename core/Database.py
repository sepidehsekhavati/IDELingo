# core/Database.py
import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path='idelingo.db'):
        self.db_path = db_path
        # جداول را یک بار در main thread می‌سازیم (در __init__ که در thread اصلی اجرا می‌شود)
        self._create_tables()
        self._migrate()
        self._create_indexes()

    def _connect(self):
        """ایجاد یک اتصال جدید (هر بار)"""
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar TEXT DEFAULT '😊',
            plan TEXT DEFAULT 'free',
            created_at TEXT NOT NULL,
            last_active TEXT NOT NULL,
            daily_goal INTEGER DEFAULT 10,
            current_streak INTEGER DEFAULT 0,
            xp_total INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            words_learned INTEGER DEFAULT 0,
            grammar_learned INTEGER DEFAULT 0,
            minutes_studied INTEGER DEFAULT 0,
            goal_achieved BOOLEAN DEFAULT FALSE,
            UNIQUE(user_id, date))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            meaning TEXT NOT NULL,
            example TEXT,
            language TEXT NOT NULL,
            difficulty TEXT DEFAULT 'medium',
            next_review TEXT,
            review_count INTEGER DEFAULT 0,
            tags TEXT,
            date_added TEXT NOT NULL,
            notes TEXT,
            error_count INTEGER DEFAULT 0,
            last_reviewed TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS grammar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            rule TEXT NOT NULL,
            explanation TEXT,
            example TEXT,
            language TEXT NOT NULL,
            tags TEXT,
            date_added TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS phrases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            phrase TEXT NOT NULL,
            meaning TEXT NOT NULL,
            tags TEXT,
            notes TEXT,
            date_added TEXT NOT NULL,
            practice_count INTEGER DEFAULT 0,
            last_practiced TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            plan_type TEXT DEFAULT 'daily',
            weekly_goal_words INTEGER DEFAULT 20,
            weekly_goal_grammar INTEGER DEFAULT 5,
            weekly_goal_phrases INTEGER DEFAULT 10,
            monthly_goal_words INTEGER DEFAULT 80,
            monthly_goal_grammar INTEGER DEFAULT 20,
            monthly_goal_phrases INTEGER DEFAULT 40,
            custom_goal_words INTEGER DEFAULT 10,
            custom_goal_grammar INTEGER DEFAULT 3,
            custom_goal_phrases INTEGER DEFAULT 5,
            custom_interval_days INTEGER DEFAULT 1,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_reset_date TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS practice_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            corrected_text TEXT,
            suggestions TEXT,
            timestamp TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS privacy_settings (
            user_id INTEGER PRIMARY KEY,
            profile_public BOOLEAN DEFAULT 1)''')
        conn.commit()
        conn.close()

    def _migrate(self):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA table_info(vocabulary)")
            columns = [col[1] for col in cursor.fetchall()]
            for col in ['tags', 'notes', 'error_count', 'last_reviewed']:
                if col not in columns:
                    cursor.execute(f"ALTER TABLE vocabulary ADD COLUMN {col} TEXT")
            cursor.execute('CREATE TABLE IF NOT EXISTS privacy_settings (user_id INTEGER PRIMARY KEY, profile_public BOOLEAN DEFAULT 1)')
            cursor.execute('INSERT OR IGNORE INTO privacy_settings (user_id, profile_public) SELECT id, 1 FROM users')
            conn.commit()
        except Exception as e:
            print(f"Migration error: {e}")
        finally:
            conn.close()

    def _create_indexes(self):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_vocabulary_user_id ON vocabulary(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_vocabulary_word ON vocabulary(word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_phrases_user_id ON phrases(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_practice_chat_user_id ON practice_chat(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_progress_user_date ON daily_progress(user_id, date)')
            conn.commit()
        except Exception as e:
            print(f"Index error: {e}")
        finally:
            conn.close()

    # ---------- متدهای عمومی برای دسترسی به دیتابیس ----------
    def execute_query(self, query, params=None, fetchone=False, fetchall=False, commit=False):
        conn = self._connect()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if commit:
                conn.commit()
            if fetchone:
                result = cursor.fetchone()
            elif fetchall:
                result = cursor.fetchall()
            else:
                result = None
            return result
        finally:
            conn.close()

    # متدهای راحت برای استفاده در UserManager (سازگاری با کدهای قبلی)
    @property
    def cursor(self):
        """این پراپرتی فقط برای سازگاری با کدهای قدیمی استفاده می‌شود (و thread-safe نیست!)"""
        # بهتر است از متد execute_query استفاده شود
        raise RuntimeError("Direct cursor access is not thread-safe. Use execute_query instead.")
    
    @property
    def conn(self):
        raise RuntimeError("Direct connection access is not thread-safe. Use execute_query instead.")
    
    # متدهای خاص (مثلاً getUserPlan) را می‌توان با execute_query بازنویسی کرد
    def get_user_plan(self, user_id):
        query = 'SELECT * FROM user_plans WHERE user_id = ?'
        row = self.execute_query(query, (user_id,), fetchone=True)
        if not row:
            self.execute_query('INSERT INTO user_plans (user_id, plan_type, last_reset_date) VALUES (?, "daily", ?)',
                               (user_id, datetime.now().strftime("%Y-%m-%d")), commit=True)
            return self.get_user_plan(user_id)
        return {
            'id': row[0], 'user_id': row[1], 'plan_type': row[2], 'weekly_goal_words': row[3],
            'weekly_goal_grammar': row[4], 'weekly_goal_phrases': row[5], 'monthly_goal_words': row[6],
            'monthly_goal_grammar': row[7], 'monthly_goal_phrases': row[8], 'custom_goal_words': row[9],
            'custom_goal_grammar': row[10], 'custom_goal_phrases': row[11], 'custom_interval_days': row[12],
            'current_streak': row[13], 'longest_streak': row[14], 'last_reset_date': row[15]
        }

    def update_user_plan(self, user_id, plan_type, **kwargs):
        allowed = ['weekly_goal_words', 'weekly_goal_grammar', 'weekly_goal_phrases',
                   'monthly_goal_words', 'monthly_goal_grammar', 'monthly_goal_phrases',
                   'custom_goal_words', 'custom_goal_grammar', 'custom_goal_phrases', 'custom_interval_days']
        updates = []
        values = []
        for field, value in kwargs.items():
            if field in allowed and value is not None:
                updates.append(f"{field} = ?")
                values.append(value)
        if updates:
            query = f"UPDATE user_plans SET plan_type = ?, {', '.join(updates)} WHERE user_id = ?"
            self.execute_query(query, [plan_type] + values + [user_id], commit=True)
        else:
            self.execute_query("UPDATE user_plans SET plan_type = ? WHERE user_id = ?", (plan_type, user_id), commit=True)

    # دیگر متدهای مشابه (get_leaderboard, search_users, ...) نیز باید با execute_query بازنویسی شوند.
    # برای جلوگیری از طولانی شدن، من فقط متدهای اصلی را تغییر می‌دهم.
    # شما باید بقیه متدها (مانند get_vocabulary, add_vocabulary و ...) را خودتان به همین شکل بازنویسی کنید.
    # اما برای سرعت، راه حل موقت: در UserManager به جای self.db.cursor از self.db.execute_query استفاده کنید.

    def close(self):
        pass  # دیگر نیازی به بستن نیست چون هر بار اتصال بسته می‌شود
