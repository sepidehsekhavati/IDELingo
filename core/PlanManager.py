from datetime import datetime

class PlanManager:
    def __init__(self, db):
        self.db = db

    def get_user_plan(self, user_id):
        row = self.db.execute_query('SELECT * FROM user_plans WHERE user_id=?', (user_id,), fetchone=True)
        if not row:
            self.create_default_plan(user_id)
            return self.get_user_plan(user_id)
        return {'id': row[0], 'user_id': row[1], 'plan_type': row[2], 'weekly_goal_words': row[3],
                'weekly_goal_grammar': row[4], 'weekly_goal_phrases': row[5], 'monthly_goal_words': row[6],
                'monthly_goal_grammar': row[7], 'monthly_goal_phrases': row[8], 'custom_goal_words': row[9],
                'custom_goal_grammar': row[10], 'custom_goal_phrases': row[11], 'custom_interval_days': row[12],
                'current_streak': row[13], 'longest_streak': row[14], 'last_reset_date': row[15]}

    def create_default_plan(self, user_id):
        self.db.execute_query(
            'INSERT INTO user_plans (user_id, plan_type, last_reset_date) VALUES (?, "daily", ?)',
            (user_id, datetime.now().strftime("%Y-%m-%d")), commit=True)

    def update_plan(self, user_id, plan_type, **kwargs):
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
            self.db.execute_query(query, [plan_type] + values + [user_id], commit=True)
        else:
            self.db.execute_query("UPDATE user_plans SET plan_type = ? WHERE user_id = ?", (plan_type, user_id), commit=True)

    def get_plan_progress(self, user_id, today_stats):
        plan = self.get_user_plan(user_id)
        if plan['plan_type'] == 'daily':
            goal_words, goal_grammar, goal_phrases = plan['custom_goal_words'], plan['custom_goal_grammar'], plan['custom_goal_phrases']
        elif plan['plan_type'] == 'weekly':
            goal_words, goal_grammar, goal_phrases = plan['weekly_goal_words'], plan['weekly_goal_grammar'], plan['weekly_goal_phrases']
        elif plan['plan_type'] == 'monthly':
            goal_words, goal_grammar, goal_phrases = plan['monthly_goal_words'], plan['monthly_goal_grammar'], plan['monthly_goal_phrases']
        else:
            goal_words, goal_grammar, goal_phrases = plan['custom_goal_words'], plan['custom_goal_grammar'], plan['custom_goal_phrases']
        return {'plan_type': plan['plan_type'], 'current_streak': plan['current_streak'],
                'longest_streak': plan['longest_streak'],
                'words': {'current': today_stats.get('words', 0), 'goal': goal_words},
                'grammar': {'current': today_stats.get('grammar', 0), 'goal': goal_grammar},
                'phrases': {'current': today_stats.get('phrases', 0), 'goal': goal_phrases}}

    def update_streak(self, user_id, today_learned):
        plan = self.get_user_plan(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if plan['plan_type'] == 'daily':
            goal_words, goal_grammar, goal_phrases = plan['custom_goal_words'], plan['custom_goal_grammar'], plan['custom_goal_phrases']
        elif plan['plan_type'] == 'weekly':
            goal_words, goal_grammar, goal_phrases = plan['weekly_goal_words']/7, plan['weekly_goal_grammar']/7, plan['weekly_goal_phrases']/7
        elif plan['plan_type'] == 'monthly':
            goal_words, goal_grammar, goal_phrases = plan['monthly_goal_words']/30, plan['monthly_goal_grammar']/30, plan['monthly_goal_phrases']/30
        else:
            goal_words, goal_grammar, goal_phrases = plan['custom_goal_words'], plan['custom_goal_grammar'], plan['custom_goal_phrases']
        words_pct = today_learned.get('words', 0) / max(goal_words, 1)
        grammar_pct = today_learned.get('grammar', 0) / max(goal_grammar, 1)
        phrases_pct = today_learned.get('phrases', 0) / max(goal_phrases, 1)
        avg_pct = (words_pct + grammar_pct + phrases_pct) / 3
        goal_achieved = avg_pct >= 0.8
        if goal_achieved and plan['last_reset_date'] != today:
            new_streak = plan['current_streak'] + 1
            self.db.execute_query('UPDATE user_plans SET current_streak=?, last_reset_date=? WHERE user_id=?',
                                  (new_streak, today, user_id), commit=True)
            if new_streak > plan['longest_streak']:
                self.db.execute_query('UPDATE user_plans SET longest_streak=? WHERE user_id=?', (new_streak, user_id), commit=True)
            return True, new_streak
        elif not goal_achieved and plan['last_reset_date'] != today:
            self.db.execute_query('UPDATE user_plans SET current_streak=0 WHERE user_id=?', (user_id,), commit=True)
        return goal_achieved, plan['current_streak']
