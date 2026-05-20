import flet as ft
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))

from UserManager import UserManager
from OfflineDictionary import OfflineDictionary

COLORS = {
    'bg': '#0a0a0a',
    'card': '#1a1a2e',
    'sidebar': '#111122',
    'accent': '#fbbf24',
    'accent_dark': '#d97706',
    'success': '#10b981',
    'danger': '#ef4444',
    'warning': '#f59e0b',
    'info': '#3b82f6',
    'text': '#f3f4f6',
    'text_secondary': '#9ca3af',
    'text_muted': '#6b7280'
}

LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo.png")

class IDELingoApp:
    def __init__(self):
        self.user_manager = None
        self.current_user = None
        self.page = None
        self.current_index = 0
        self.offline_dict = None

    def init_backend(self):
        try:
            self.user_manager = UserManager()
            self.offline_dict = OfflineDictionary()
            return True
        except Exception as e:
            print(f"Backend error: {e}")
            return False

    def main(self, page: ft.Page):
        self.page = page
        page.title = "IDELingo"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 0
        page.window_width = 400
        page.window_height = 780
        page.window_resizable = False
        page.bgcolor = COLORS['bg']
        page.theme = ft.Theme(color_scheme_seed=COLORS['accent'], use_material3=True)

        # AppBar: فقط لوگو (بدون متن)
        if os.path.exists(LOGO_PATH):
            try:
                page.appbar = ft.AppBar(
                    title=ft.Image(src=LOGO_PATH, width=50, height=50, fit=ft.ImageFit.CONTAIN),
                    center_title=True,
                    bgcolor=COLORS['sidebar'],
                    actions=[ft.IconButton(icon=ft.icons.PERSON, icon_color=COLORS['text_secondary'], on_click=self.show_profile)]
                )
            except:
                page.appbar = ft.AppBar(
                    title=ft.Text("", size=0),
                    bgcolor=COLORS['sidebar'],
                    actions=[ft.IconButton(icon=ft.icons.PERSON, icon_color=COLORS['text_secondary'], on_click=self.show_profile)]
                )
        else:
            page.appbar = ft.AppBar(
                title=ft.Text("", size=0),
                bgcolor=COLORS['sidebar'],
                actions=[ft.IconButton(icon=ft.icons.PERSON, icon_color=COLORS['text_secondary'], on_click=self.show_profile)]
            )

        if self.init_backend():
            self.show_login()
        else:
            self.show_error_page()

    def _close_dialog(self, dialog):
        if dialog:
            dialog.open = False
            self.page.update()

    def show_error_page(self):
        self.page.clean()
        self.page.add(ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.ERROR_OUTLINE, size=80, color=COLORS['danger']),
                ft.Text("Error", size=28, weight=ft.FontWeight.BOLD, color=COLORS['danger']),
                ft.Text("Failed to initialize backend", size=16, color=COLORS['text_secondary']),
                ft.ElevatedButton("Retry", on_click=lambda e: self.init_backend() and self.show_login(), bgcolor=COLORS['accent'])
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            alignment=ft.alignment.center, expand=True
        ))
        self.page.update()

    def show_login(self):
        self.page.clean()
        logo = ft.Container()
        if os.path.exists(LOGO_PATH):
            try:
                logo = ft.Container(content=ft.Image(src=LOGO_PATH, width=200, height=200, fit=ft.ImageFit.CONTAIN), margin=ft.margin.only(top=30, bottom=10))
            except:
                logo = ft.Container(content=ft.Column([ft.Icon(ft.icons.SCHOOL, size=80, color=COLORS['accent']), ft.Text("IDELingo", size=32, weight=ft.FontWeight.BOLD, color=COLORS['accent']), ft.Text("Learn English Smarter", size=14, color=COLORS['text_secondary'])], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), margin=ft.margin.only(top=50, bottom=30))
        else:
            logo = ft.Container(content=ft.Column([ft.Icon(ft.icons.SCHOOL, size=80, color=COLORS['accent']), ft.Text("IDELingo", size=32, weight=ft.FontWeight.BOLD, color=COLORS['accent']), ft.Text("Learn English Smarter", size=14, color=COLORS['text_secondary'])], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), margin=ft.margin.only(top=50, bottom=30))

        user = ft.TextField(label="Username or Email", prefix_icon=ft.icons.PERSON, border_color=COLORS['text_muted'], focused_border_color=COLORS['accent'], color=COLORS['text'], width=300, height=50)
        pwd = ft.TextField(label="Password", prefix_icon=ft.icons.LOCK, password=True, can_reveal_password=True, border_color=COLORS['text_muted'], focused_border_color=COLORS['accent'], color=COLORS['text'], width=300, height=50)
        err = ft.Text("", color=COLORS['danger'], size=14, visible=False)

        def do_login(e):
            if not user.value or not pwd.value:
                err.value = "Please fill all fields"
                err.visible = True
                self.page.update()
                return
            ok, msg, u = self.user_manager.login(user.value, pwd.value)
            if ok:
                self.current_user = u
                self.show_dashboard()
            else:
                err.value = msg
                err.visible = True
                self.page.update()

        self.page.add(ft.Container(
            content=ft.Column([
                logo,
                ft.Container(content=ft.Column([user, pwd, err, ft.ElevatedButton("Login", on_click=do_login, bgcolor=COLORS['accent'], color=COLORS['bg'], width=300, height=45), ft.TextButton("Create New Account", on_click=lambda e: self.show_register(), style=ft.ButtonStyle(color=COLORS['accent']))], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15), alignment=ft.alignment.center)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20, scroll=ft.ScrollMode.AUTO),
            expand=True
        ))
        self.page.update()

    def show_register(self):
        self.page.clean()
        logo = ft.Container()
        if os.path.exists(LOGO_PATH):
            try:
                logo = ft.Container(content=ft.Image(src=LOGO_PATH, width=100, height=100, fit=ft.ImageFit.CONTAIN), margin=ft.margin.only(top=20, bottom=10))
            except:
                logo = ft.Container(content=ft.Text("IDELingo", size=28, weight=ft.FontWeight.BOLD, color=COLORS['accent']), margin=ft.margin.only(top=30, bottom=20))
        else:
            logo = ft.Container(content=ft.Text("IDELingo", size=28, weight=ft.FontWeight.BOLD, color=COLORS['accent']), margin=ft.margin.only(top=30, bottom=20))

        user = ft.TextField(label="Username", prefix_icon=ft.icons.PERSON, color=COLORS['text'], width=300, height=50)
        email = ft.TextField(label="Email", prefix_icon=ft.icons.EMAIL, color=COLORS['text'], width=300, height=50)
        pwd = ft.TextField(label="Password (min 6 chars)", prefix_icon=ft.icons.LOCK, password=True, can_reveal_password=True, color=COLORS['text'], width=300, height=50)
        err = ft.Text("", color=COLORS['danger'], size=14, visible=False)

        def do_reg(e):
            if not user.value or not email.value or not pwd.value:
                err.value = "Please fill all fields"
                err.visible = True
                self.page.update()
                return
            if len(pwd.value) < 6:
                err.value = "Password must be at least 6 characters"
                err.visible = True
                self.page.update()
                return
            ok, msg = self.user_manager.register(user.value, email.value, pwd.value)
            if ok:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Registration successful! Please login."), bgcolor=COLORS['success'])
                self.page.snack_bar.open = True
                self.page.update()
                self.show_login()
            else:
                err.value = msg
                err.visible = True
                self.page.update()

        self.page.add(ft.Container(
            content=ft.Column([
                logo,
                ft.Container(content=ft.Column([user, email, pwd, err, ft.ElevatedButton("Sign Up", on_click=do_reg, bgcolor=COLORS['success'], color=COLORS['bg'], width=300, height=45), ft.TextButton("Back to Login", on_click=lambda e: self.show_login(), style=ft.ButtonStyle(color=COLORS['accent']))], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15), alignment=ft.alignment.center)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            expand=True
        ))
        self.page.update()

    def show_dashboard(self):
        self.page.clean()
        self.current_index = 0
        prog = self.user_manager.get_daily_progress(self.current_user['id'])
        hour = datetime.now().hour
        greet = "Good Evening" if hour > 18 else "Good Afternoon" if hour > 12 else "Good Morning"
        phrases_cnt = self.user_manager.db.cursor.execute("SELECT COUNT(*) FROM phrases WHERE user_id=?", (self.current_user['id'],)).fetchone()[0]

        def nav_words(e): self.nav_change(1)
        def nav_gram(e): self.nav_change(2)
        def nav_phr(e): self.nav_change(4)
        def nav_streak(e): self.nav_change(7)

        row1 = ft.Row([
            self._stat_card("📚", f"{prog['words_learned']}", f"/{self.current_user['daily_goal']}", "Words Today", nav_words),
            self._stat_card("📖", f"{prog['grammar_learned']}", "", "Grammar Today", nav_gram),
            self._stat_card("💬", f"{phrases_cnt}", "", "Phrases", nav_phr),
        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=5)
        row2 = ft.Row([
            self._stat_card("🔥", f"{self.current_user['current_streak']}", "days", "Streak", nav_streak),
            self._stat_card("🎯", "✅" if prog['goal_achieved'] else "⏳", "", "Daily Goal", None),
            self._stat_card("🏆", f"{self.current_user['level']}", "", "Level", None),
        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=5)

        quick = self._quick_add_section()
        nav = self._bottom_nav_bar()
        self.page.add(ft.Column([
            ft.Container(content=ft.Column([ft.Text(f"{greet}, {self.current_user['username']}! 👋", size=22, weight=ft.FontWeight.BOLD, color=COLORS['text']), ft.Text(datetime.now().strftime("%A, %B %d, %Y"), size=12, color=COLORS['text_secondary'])], spacing=5), padding=ft.padding.all(20)),
            ft.Container(content=ft.Column([row1, row2], spacing=10), padding=ft.padding.symmetric(horizontal=20)),
            quick,
            ft.Container(expand=True),
            nav
        ], spacing=10, expand=True))
        self.page.update()

    def _stat_card(self, icon, value, subtitle, label, on_click):
        card = ft.Container(
            content=ft.Column([
                ft.Text(icon, size=24),
                ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=COLORS['accent']),
                ft.Text(subtitle, size=10, color=COLORS['text_muted']) if subtitle else ft.Container(),
                ft.Text(label, size=10, color=COLORS['text_secondary'])
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
            bgcolor=COLORS['card'], border_radius=10, padding=ft.padding.all(8), width=110, height=100
        )
        if on_click:
            card.on_click = on_click
        return card

    def _quick_add_section(self):
        wf = ft.TextField(hint_text="Word", border_color=COLORS['text_muted'], focused_border_color=COLORS['accent'], color=COLORS['text'], expand=True, height=45)
        mf = ft.TextField(hint_text="Meaning", border_color=COLORS['text_muted'], focused_border_color=COLORS['accent'], color=COLORS['text'], expand=True, height=45)
        # حذف dropdown زبان
        def add(e):
            if not wf.value: self._show_snack("❌ Please enter a word!", COLORS['danger']); return
            if not mf.value: self._show_snack("❌ Please enter a meaning!", COLORS['danger']); return
            self.user_manager.add_vocabulary(self.current_user['id'], wf.value, mf.value, "", "English", "medium", "", "")
            wf.value = ""; mf.value = ""
            self._show_snack("✅ Word added!", COLORS['success'])
            self.show_dashboard()
        return ft.Container(content=ft.Column([
            ft.Text("➕ Quick Add Word", size=16, weight=ft.FontWeight.BOLD, color=COLORS['text']),
            ft.Row([wf, mf, ft.IconButton(icon=ft.icons.ADD_CIRCLE, icon_color=COLORS['success'], icon_size=40, on_click=add)], spacing=10)
        ], spacing=10), bgcolor=COLORS['card'], border_radius=12, padding=15, margin=ft.margin.symmetric(horizontal=20))

    def _show_snack(self, msg, color):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=color)
        self.page.snack_bar.open = True
        self.page.update()

    def _bottom_nav_bar(self):
        items = [(ft.icons.HOME, "Home", 0), (ft.icons.BOOK, "Words", 1), (ft.icons.MENU_BOOK, "Grammar", 2), (ft.icons.CHAT, "Practice", 3), (ft.icons.FORMAT_QUOTE, "Phrases", 4), (ft.icons.PEOPLE, "Community", 5), (ft.icons.EMOJI_EVENTS, "Leaderboard", 6), (ft.icons.SETTINGS, "Settings", 7)]
        return ft.Container(content=ft.Row([self._nav_button(icon, label, idx) for icon, label, idx in items], alignment=ft.MainAxisAlignment.SPACE_AROUND), bgcolor=COLORS['sidebar'], padding=ft.padding.symmetric(vertical=8), border_radius=ft.border_radius.only(top_left=15, top_right=15))

    def _nav_button(self, icon, label, index):
        return ft.IconButton(icon=icon, icon_size=24, icon_color=COLORS['accent'] if self.current_index==index else COLORS['text_muted'], on_click=lambda e, i=index: self.nav_change(i), tooltip=label)

    # ========== Vocabulary ==========
    def show_vocabulary(self):
        self.page.clean()
        self.current_index = 1
        # هدر: عنوان در وسط، آیکون سرچ در راست
        header = ft.Container(content=ft.Row([
            ft.Text("📝 Vocabulary Manager", size=24, weight=ft.FontWeight.BOLD, color=COLORS['accent'], expand=True, text_align=ft.TextAlign.CENTER),
            ft.IconButton(icon=ft.icons.SEARCH, icon_color=COLORS['accent'], icon_size=24, on_click=lambda e: self.show_search_dialog("vocabulary"))
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=ft.padding.all(20))
        add_btn = ft.ElevatedButton(content=ft.Row([ft.Icon(ft.icons.ADD), ft.Text("Add New Word")], spacing=10), on_click=lambda e: self.add_vocabulary_dialog(), bgcolor=COLORS['success'], color=COLORS['bg'])
        # فقط فیلتر difficulty (زبان حذف شد)
        self.vocab_diff = ft.Dropdown(options=[ft.dropdown.Option("All"), ft.dropdown.Option("easy"), ft.dropdown.Option("medium"), ft.dropdown.Option("hard")], value="All", width=100, bgcolor=COLORS['bg'], color=COLORS['text'])
        self.vocab_diff.on_change = self.refresh_vocab
        self.vocab_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        self.page.add(ft.Column([header, ft.Container(content=add_btn, padding=ft.padding.symmetric(horizontal=20)), ft.Container(content=ft.Row([self.vocab_diff], spacing=10), padding=ft.padding.symmetric(horizontal=20, vertical=10)), ft.Container(content=self.vocab_container, expand=True, padding=ft.padding.symmetric(horizontal=20)), self._bottom_nav_bar()], spacing=10, expand=True))
        self.refresh_vocab(None)

    def refresh_vocab(self, e):
        self.vocab_container.controls.clear()
        filters = {}
        if self.vocab_diff.value != "All": filters['difficulty'] = self.vocab_diff.value
        words = self.user_manager.get_vocabulary(self.current_user['id'], filters)
        if not words:
            self.vocab_container.controls.append(ft.Container(content=ft.Text("No words yet. Add your first word!", color=COLORS['text_secondary']), padding=40))
        else:
            for w in words[:20]:
                meaning_disp = ft.Text("❓", size=14, color=COLORS['text_secondary'])
                def toggle(m, d): return lambda _: self._toggle_meaning(d, m)
                diff_icon = "🟢" if w[6]=='easy' else "🟡" if w[6]=='medium' else "🔴"
                card = ft.Container(
                    content=ft.Row([
                        ft.Column([ft.Row([ft.Text(w[2], size=16, weight=ft.FontWeight.BOLD, color=COLORS['accent']), ft.Text(diff_icon, size=12)], spacing=5), ft.GestureDetector(content=meaning_disp, on_tap=toggle(w[3], meaning_disp))], spacing=3, expand=True),
                        ft.Column([ft.Text(f"🌐 English", size=11, color=COLORS['text_muted']), ft.Row([ft.IconButton(icon=ft.icons.EDIT, icon_size=18, icon_color=COLORS['info'], on_click=lambda _, ww=w: self.edit_word(ww)), ft.IconButton(icon=ft.icons.DELETE, icon_size=18, icon_color=COLORS['danger'], on_click=lambda _, wid=w[0]: self.delete_word(wid))], spacing=0)], horizontal_alignment=ft.CrossAxisAlignment.END)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=COLORS['card'], border_radius=10, padding=12)
                self.vocab_container.controls.append(card)
        self.page.update()

    def _toggle_meaning(self, txt, meaning):
        if txt.value == "❓":
            txt.value = meaning[:50] + ("..." if len(meaning)>50 else "")
            txt.color = COLORS['text']
        else:
            txt.value = "❓"
            txt.color = COLORS['text_secondary']
        txt.update()

    def edit_word(self, w): self._show_snack(f"Edit: {w[2]}", COLORS['info'])
    def delete_word(self, wid):
        def confirm(e):
            confirm_dlg.open = False
            self.user_manager.delete_vocabulary(wid)
            self.refresh_vocab(None)
            self._show_snack("✅ Word deleted!", COLORS['success'])
        confirm_dlg = ft.AlertDialog(title=ft.Text("Delete Word", color=COLORS['warning']), content=ft.Text("Are you sure?"), actions=[ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(confirm_dlg)), ft.ElevatedButton("Delete", on_click=confirm, bgcolor=COLORS['danger'])])
        self.page.dialog = confirm_dlg
        confirm_dlg.open = True
        self.page.update()

    def add_vocabulary_dialog(self):
        wf = ft.TextField(label="Word", width=300)
        mf = ft.TextField(label="Meaning", width=300, multiline=True, min_lines=2)
        exf = ft.TextField(label="Example (optional)", width=300)
        # حذف dropdown زبان
        diff = ft.Dropdown(options=[ft.dropdown.Option("easy"), ft.dropdown.Option("medium"), ft.dropdown.Option("hard")], value="medium", width=300)
        dict_res = ft.Text("", size=12)
        def search_dict(e):
            if wf.value:
                res = self.offline_dict.get_meaning_with_pronunciation(wf.value)
                dict_res.value = res[:300] + ("..." if len(res)>300 else "")
                dict_res.update()
        def save(e):
            if not wf.value: self._show_snack("❌ Please enter a word!", COLORS['danger']); return
            if not mf.value: self._show_snack("❌ Please enter a meaning!", COLORS['danger']); return
            self.user_manager.add_vocabulary(self.current_user['id'], wf.value, mf.value, exf.value or "", "English", diff.value, "", "")
            self._close_dialog(dlg)
            self.refresh_vocab(None)
            self._show_snack(f"✅ '{wf.value}' added!", COLORS['success'])
        dlg = ft.AlertDialog(title=ft.Text("Add New Word", color=COLORS['accent']), content=ft.Container(content=ft.Column([wf, mf, exf, diff, ft.ElevatedButton("🔍 Search in Dictionary", on_click=search_dict, bgcolor=COLORS['info']), dict_res], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20, width=380, height=550), actions=[ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(dlg)), ft.ElevatedButton("Save", on_click=save, bgcolor=COLORS['success'])])
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def show_search_dialog(self, target):
        sf = ft.TextField(hint_text="Search...", width=300)
        res = ft.Text("", size=14)
        def do_search(e):
            q = sf.value
            if not q: return
            if target == "vocabulary":
                ww = self.user_manager.get_vocabulary(self.current_user['id'], {'search': q})
                res.value = f"🔍 Found {len(ww)} words containing '{q}'" if ww else f"❌ No words found for '{q}'"
            elif target == "phrases":
                pp = self.user_manager.get_phrases(self.current_user['id'], q)
                res.value = f"🔍 Found {len(pp)} phrases containing '{q}'" if pp else f"❌ No phrases found for '{q}'"
            res.update()
        dlg = ft.AlertDialog(title=ft.Text(f"Search {target.capitalize()}"), content=ft.Column([sf, res]), actions=[ft.TextButton("Search", on_click=do_search), ft.TextButton("Close", on_click=lambda e: self._close_dialog(dlg))])
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    # ========== Grammar ==========
        # ========== Grammar (نسخه تست شده با قابلیت ویرایش یادداشت) ==========
        # ========== Grammar ==========
        # ========== Grammar ==========
        # ========== Grammar (بازنویسی کامل) ==========
        # ========== Grammar ==========
    def show_grammar(self):
        self.page.clean()
        self.current_index = 2
        topics = self.user_manager.get_all_grammar_topics()
        search = ft.TextField(hint_text="Search grammar rules...", prefix_icon=ft.icons.SEARCH, expand=True, height=45,
                              border_color=COLORS['text_muted'], focused_border_color=COLORS['accent'], color=COLORS['text'])
        grammar_content = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        def filter_grammar(e):
            q = search.value.lower() if search.value else ""
            grammar_content.controls.clear()
            filtered = [t for t in topics if q in t.lower()] if q else topics
            for t in filtered[:30]:
                info = self.user_manager.get_grammar_info(t)
                title = info.get('title', t.replace('_', ' ').title()) if info else t.replace('_', ' ').title()
                level = info.get('level', 'beginner') if info else 'beginner'
                level_icon = "🔰" if level == 'beginner' else "📘" if level == 'intermediate' else "🎓"
                is_fav = self.user_manager.is_grammar_favorite(t)
                fav_icon = "❤️" if is_fav else "🤍"
                btn = ft.Container(
                    content=ft.Row([ft.Text(f"{level_icon} {fav_icon}", size=14), ft.Text(title, size=14, color=COLORS['text'], expand=True), ft.Icon(ft.icons.CHEVRON_RIGHT, color=COLORS['text_muted'], size=18)]),
                    bgcolor=COLORS['card'], border_radius=8, padding=12,
                    on_click=lambda _, tt=t: self.open_grammar_topic(tt)
                )
                grammar_content.controls.append(btn)
            if not filtered:
                grammar_content.controls.append(ft.Container(content=ft.Text("No grammar rules found.", color=COLORS['text_secondary']), padding=40))
            self.page.update()

        search.on_change = filter_grammar
        self.page.add(ft.Column([
            ft.Container(content=ft.Text("📖 Grammar Library", size=24, weight=ft.FontWeight.BOLD, color=COLORS['accent']), padding=20),
            ft.Container(content=ft.Text(f"📚 Total Rules: {len(topics)}", size=13, color=COLORS['text_secondary']), padding=ft.padding.symmetric(horizontal=20)),
            ft.Container(content=search, padding=20),
            ft.Container(content=grammar_content, expand=True, padding=ft.padding.symmetric(horizontal=20)),
            self._bottom_nav_bar()
        ], spacing=10, expand=True))
        filter_grammar(None)

    def open_grammar_topic(self, topic_key):
        info = self.user_manager.get_grammar_info(topic_key)
        if not info:
            self._show_snack("Grammar rule not found!", COLORS['danger'])
            return

        level_icon = "🔰" if info.get('level') == 'beginner' else "📘" if info.get('level') == 'intermediate' else "🎓"
        is_fav = self.user_manager.is_grammar_favorite(topic_key)
        notes = self.user_manager.get_grammar_notes(topic_key)

        # بخش نمایش یادداشت‌ها
        notes_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=250)

        def refresh_notes():
            notes_list.controls.clear()
            for n in notes:
                timestamp = n['timestamp']
                text = n['note']
                display_text = ft.Text(text, size=12, color=COLORS['text_secondary'], selectable=True)
                
                # کادر هر یادداشت
                note_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(timestamp, size=10, color=COLORS['text_muted']),
                            display_text,
                            ft.Row([
                                ft.TextButton("✏️ Edit", on_click=lambda e, t=topic_key, old=text, ts=timestamp: self._edit_note_dialog(t, old, ts, refresh_notes)),
                                ft.TextButton("🗑️ Delete", on_click=lambda e, t=topic_key, old=text, ts=timestamp: self._delete_note(t, old, ts, refresh_notes), icon_color=COLORS['danger'])
                            ], alignment=ft.MainAxisAlignment.END)
                        ], spacing=5),
                        padding=10
                    ),
                    margin=5,
                    elevation=2
                )
                notes_list.controls.append(note_card)
            if not notes:
                notes_list.controls.append(
                    ft.Container(
                        content=ft.Text("No notes yet. Write your first note above!", size=12, color=COLORS['text_secondary'], italic=True),
                        padding=20,
                        alignment=ft.alignment.center
                    )
                )

        refresh_notes()

        note_field = ft.TextField(hint_text="Write a new note...", multiline=True, min_lines=2, max_lines=3, width=300)

        def add_note(e):
            if note_field.value:
                self.user_manager.save_grammar_note(topic_key, note_field.value)
                note_field.value = ""
                notes[:] = self.user_manager.get_grammar_notes(topic_key)
                refresh_notes()
                dialog.update()
                self._show_snack("✅ Note added!", COLORS['success'])

        def toggle_fav(e):
            nonlocal is_fav
            if is_fav:
                self.user_manager.remove_grammar_favorite(topic_key)
                is_fav = False
                fav_btn.icon = ft.icons.FAVORITE_BORDER
                fav_btn.icon_color = COLORS['text_secondary']
            else:
                self.user_manager.add_grammar_favorite(topic_key)
                is_fav = True
                fav_btn.icon = ft.icons.FAVORITE
                fav_btn.icon_color = COLORS['danger']
            dialog.update()
            self.show_grammar()

        fav_btn = ft.IconButton(icon=ft.icons.FAVORITE if is_fav else ft.icons.FAVORITE_BORDER,
                                icon_color=COLORS['danger'] if is_fav else COLORS['text_secondary'], on_click=toggle_fav)

        content = ft.Column([
            ft.Text("📐 Structure", weight=ft.FontWeight.BOLD, color=COLORS['accent']),
            ft.Text(info.get('structure', ''), size=13, color=COLORS['text_secondary']),
            ft.Divider(),
            ft.Text("📝 Examples", weight=ft.FontWeight.BOLD, color=COLORS['accent']),
        ] + [ft.Text(f"• {ex}", size=13, color=COLORS['text_secondary']) for ex in info.get('example', [])[:3]] + [
            ft.Divider(),
            ft.Text("🎯 Key Usages", weight=ft.FontWeight.BOLD, color=COLORS['accent']),
        ] + [ft.Text(f"• {u}", size=13, color=COLORS['text_secondary']) for u in info.get('usage', [])[:3]] + [
            ft.Divider(),
            ft.Text("⚠️ Common Mistakes", weight=ft.FontWeight.BOLD, color=COLORS['warning']),
        ] + [ft.Text(f"• {m}", size=12, color=COLORS['text_secondary']) for m in info.get('common_mistakes', [])[:2]] + [
            ft.Divider(),
            ft.Text("📓 My Notes", weight=ft.FontWeight.BOLD, color=COLORS['accent']),
            notes_list,
            note_field,
            ft.ElevatedButton("➕ Add Note", on_click=add_note, bgcolor=COLORS['success'])
        ], spacing=10, scroll=ft.ScrollMode.AUTO)

        dialog = ft.AlertDialog(
            title=ft.Row([ft.Text(f"{level_icon} ", size=14), ft.Text(info.get('title', topic_key), color=COLORS['accent'], expand=True), fav_btn]),
            content=ft.Container(content=content, padding=15, width=400, height=600),
            actions=[ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog))]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _edit_note_dialog(self, topic_key, old_text, timestamp, refresh_callback):
        edit_field = ft.TextField(value=old_text, multiline=True, min_lines=3, max_lines=5, width=350)
        def save_edit(e):
            new_text = edit_field.value
            if new_text and new_text != old_text:
                # حذف یادداشت قدیمی و اضافه جدید
                notes_list = self.user_manager.get_grammar_notes(topic_key)
                for i, n in enumerate(notes_list):
                    if n['timestamp'] == timestamp and n['note'] == old_text:
                        notes_list.pop(i)
                        break
                self.user_manager.save_grammar_note(topic_key, new_text)
                refresh_callback()
                edit_dialog.open = False
                self._show_snack("✅ Note updated!", COLORS['success'])
            else:
                edit_dialog.open = False
        edit_dialog = ft.AlertDialog(
            title=ft.Text("Edit Note", color=COLORS['accent']),
            content=ft.Container(content=edit_field, padding=20),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(edit_dialog, 'open', False)),
                ft.ElevatedButton("Save", on_click=save_edit, bgcolor=COLORS['success'])
            ]
        )
        self.page.dialog = edit_dialog
        edit_dialog.open = True
        self.page.update()

    def _delete_note(self, topic_key, old_text, timestamp, refresh_callback):
        def confirm_delete(e):
            notes_list = self.user_manager.get_grammar_notes(topic_key)
            for i, n in enumerate(notes_list):
                if n['timestamp'] == timestamp and n['note'] == old_text:
                    notes_list.pop(i)
                    break
            refresh_callback()
            confirm_dialog.open = False
            self._show_snack("🗑️ Note deleted!", COLORS['success'])
        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Delete Note", color=COLORS['warning']),
            content=ft.Text("Are you sure you want to delete this note?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(confirm_dialog, 'open', False)),
                ft.ElevatedButton("Delete", on_click=confirm_delete, bgcolor=COLORS['danger'])
            ]
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    # ========== Phrases ==========
    def show_phrases(self):
        self.page.clean()
        self.current_index = 4
        # هدر مشابه Vocabulary
        header = ft.Container(content=ft.Row([
            ft.Text("💬 My Phrase Library", size=24, weight=ft.FontWeight.BOLD, color=COLORS['accent'], expand=True, text_align=ft.TextAlign.CENTER),
            ft.IconButton(icon=ft.icons.SEARCH, icon_color=COLORS['accent'], icon_size=24, on_click=lambda e: self.show_search_dialog("phrases"))
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=20)
        add_btn = ft.ElevatedButton(content=ft.Row([ft.Icon(ft.icons.ADD), ft.Text("Add New Phrase")], spacing=10), on_click=lambda e: self.add_phrase_dialog(), bgcolor=COLORS['success'], color=COLORS['bg'])
        self.phrases_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        self.page.add(ft.Column([header, ft.Container(content=add_btn, padding=ft.padding.symmetric(horizontal=20)), ft.Container(content=self.phrases_container, expand=True, padding=ft.padding.symmetric(horizontal=20)), self._bottom_nav_bar()], spacing=10, expand=True))
        self.refresh_phrases(None)

    def refresh_phrases(self, e):
        self.phrases_container.controls.clear()
        phrases = self.user_manager.get_phrases(self.current_user['id'])
        if not phrases:
            self.phrases_container.controls.append(ft.Container(content=ft.Text("No phrases yet. Click '+ Add Phrase' to start learning!", color=COLORS['text_secondary']), padding=40))
        else:
            for idx, p in enumerate(phrases[:20], 1):
                card = ft.Container(content=ft.Column([
                    ft.Row([ft.Text(f"{idx}.", size=12, color=COLORS['text_muted'], width=30), ft.Text(p[2][:60], size=14, weight=ft.FontWeight.BOLD, color=COLORS['accent'], expand=True)]),
                    ft.Text(f"📖 {p[3][:80]}", size=12, color=COLORS['text_secondary']),
                    ft.Row([ft.Text(f"🏷️ {p[4]}" if p[4] else "", size=10, color=COLORS['text_muted']), ft.Text(f"📅 {p[6][:10]}" if p[6] else "", size=10, color=COLORS['text_muted']), ft.IconButton(icon=ft.icons.DELETE, icon_size=18, icon_color=COLORS['danger'], on_click=lambda _, pid=p[0]: self.delete_phrase(pid))], spacing=10)
                ], spacing=5), bgcolor=COLORS['card'], border_radius=10, padding=12)
                self.phrases_container.controls.append(card)
        self.page.update()

    def add_phrase_dialog(self):
        pf = ft.TextField(label="Phrase / Sentence *", multiline=True, min_lines=2, width=350)
        mf = ft.TextField(label="Translation / Meaning *", multiline=True, min_lines=2, width=350)
        tf = ft.TextField(label="Tags (comma separated)", hint_text="e.g., greeting, travel", width=350)
        nf = ft.TextField(label="Notes (optional)", multiline=True, min_lines=2, width=350)
        def save(e):
            if not pf.value: self._show_snack("❌ Please enter a phrase!", COLORS['danger']); return
            if not mf.value: self._show_snack("❌ Please enter a meaning!", COLORS['danger']); return
            self.user_manager.add_phrase(self.current_user['id'], pf.value, mf.value, tf.value or "", nf.value or "")
            self._close_dialog(dlg)
            self.show_phrases()
            self._show_snack("✅ Phrase added!", COLORS['success'])
        dlg = ft.AlertDialog(title=ft.Text("Add New Phrase", color=COLORS['accent']), content=ft.Container(content=ft.Column([pf, mf, tf, nf], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20, width=400, height=500), actions=[ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(dlg)), ft.ElevatedButton("Save", on_click=save, bgcolor=COLORS['success'])])
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def delete_phrase(self, pid):
        def confirm(e):
            confirm_dlg.open = False
            self.user_manager.delete_phrase(pid)
            self.show_phrases()
            self._show_snack("✅ Phrase deleted!", COLORS['success'])
        confirm_dlg = ft.AlertDialog(title=ft.Text("Delete Phrase", color=COLORS['warning']), content=ft.Text("Are you sure?"), actions=[ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(confirm_dlg)), ft.ElevatedButton("Delete", on_click=confirm, bgcolor=COLORS['danger'])])
        self.page.dialog = confirm_dlg
        confirm_dlg.open = True
        self.page.update()

    # ========== Practice ==========
    def show_practice(self):
        self.page.clean()
        self.current_index = 3
        inp = ft.TextField(multiline=True, min_lines=4, max_lines=6, hint_text="Write a sentence in English...", border_color=COLORS['text_muted'], focused_border_color=COLORS['accent'], color=COLORS['text'], expand=True)
        res = ft.Text("", color=COLORS['text_secondary'], size=13)
        corr_cb = ft.Checkbox(label="AI Auto-correct (spelling & grammar)", value=True, check_color=COLORS['accent'])
        def check(e):
            txt = inp.value
            if not txt or not txt.strip():
                res.value = "⚠️ Please write something to practice!"
                res.color = COLORS['warning']
                self.page.update()
                return
            if corr_cb.value:
                corrected, feedback = self.user_manager.check_grammar_offline(txt)
            else:
                corrected, feedback = txt, "✅ Message saved (auto-correct disabled)"
            self.user_manager.save_practice_message(self.current_user['id'], txt, corrected, feedback)
            # XP حذف شد (دیگر add_xp فراخوانی نمی‌شود)
            if corrected != txt:
                res.value = f"✨ Suggested: \"{corrected}\"\n\n💡 {feedback}"
                res.color = COLORS['warning']
            else:
                res.value = f"✅ {feedback}"
                res.color = COLORS['success']
            inp.value = ""
            self.page.update()
        history = self.user_manager.get_practice_history(self.current_user['id'])
        hist_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
        if history:
            hist_col.controls.append(ft.Text("Recent Practice:", size=14, weight=ft.FontWeight.BOLD, color=COLORS['text']))
            for msg, corr, _, ts in history[:10]:
                t = ts[11:16] if len(ts)>16 else ts
                hist_col.controls.append(ft.Container(content=ft.Column([ft.Text(f"[{t}] You: {msg[:50]}...", size=11, color=COLORS['text_secondary']), ft.Text(f"🤖 AI: {corr[:50]}...", size=11, color=COLORS['success'])], spacing=3), bgcolor=COLORS['card'], border_radius=6, padding=8))
        self.page.add(ft.Column([
            ft.Container(content=ft.Text("💬 AI Writing Practice", size=22, weight=ft.FontWeight.BOLD, color=COLORS['accent']), padding=20),
            ft.Container(content=ft.Text("Write sentences and get intelligent AI corrections! (100% offline)", size=12, color=COLORS['text_secondary']), padding=ft.padding.symmetric(horizontal=20)),
            ft.Container(content=ft.Column([inp, corr_cb, ft.ElevatedButton("Check Grammar ✨", on_click=check, bgcolor=COLORS['success'], height=45), ft.Divider(), res, ft.Divider(), ft.Container(content=hist_col, height=200)], spacing=12), expand=True, padding=20),
            self._bottom_nav_bar()
        ], spacing=10, expand=True))
        self.page.update()

    # ========== Community ==========
    def show_community(self):
        self.page.clean()
        self.current_index = 5
        sf = ft.TextField(hint_text="Enter username...", prefix_icon=ft.icons.SEARCH, width=250, height=45, border_color=COLORS['text_muted'], focused_border_color=COLORS['accent'], color=COLORS['text'])
        res = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        def search(e):
            res.controls.clear()
            q = sf.value
            if not q or len(q)<2:
                res.controls.append(ft.Text("Enter at least 2 characters to search", color=COLORS['text_secondary']))
                self.page.update()
                return
            users = self.user_manager.search_users(q, self.current_user['id'])
            if not users:
                res.controls.append(ft.Text("No users found", color=COLORS['text_secondary']))
            else:
                for u in users:
                    res.controls.append(ft.Container(content=ft.Row([ft.Text(u[2], size=32), ft.Column([ft.Text(u[1], size=14, weight=ft.FontWeight.BOLD, color=COLORS['text']), ft.Text(f"Level {u[3]} • {u[4]} XP", size=11, color=COLORS['text_secondary'])], spacing=3, expand=True), ft.ElevatedButton("View Profile", on_click=lambda _, uid=u[0]: self.view_profile(uid), bgcolor=COLORS['info'], height=35)]), bgcolor=COLORS['card'], border_radius=10, padding=12))
            self.page.update()
        sf.on_submit = search
        self.page.add(ft.Column([ft.Container(content=ft.Text("👥 Community", size=24, weight=ft.FontWeight.BOLD, color=COLORS['accent']), padding=20), ft.Container(content=ft.Row([sf, ft.ElevatedButton("Search", on_click=search, bgcolor=COLORS['accent'])], spacing=10), padding=ft.padding.symmetric(horizontal=20)), ft.Container(content=ft.Text("💡 Tip: Search for friends to see their progress!", size=12, color=COLORS['text_secondary']), padding=ft.padding.symmetric(horizontal=20)), ft.Container(content=res, expand=True, padding=20), self._bottom_nav_bar()], spacing=10, expand=True))
        self.page.update()

    def view_profile(self, uid):
        prof, err = self.user_manager.get_user_public_profile(uid)
        if err:
            self._show_snack(err, COLORS['danger'])
            return
        dlg = ft.AlertDialog(title=ft.Text(f"{prof['username']}'s Profile", color=COLORS['accent']), content=ft.Container(content=ft.Column([ft.Container(content=ft.Text(prof['avatar'], size=50), alignment=ft.alignment.center), ft.Text(prof['username'], size=20, weight=ft.FontWeight.BOLD, color=COLORS['text']), ft.Divider(), ft.Row([ft.Column([ft.Text("⭐ Level", size=12), ft.Text(str(prof['level']), size=18, weight=ft.FontWeight.BOLD, color=COLORS['accent'])], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True), ft.Column([ft.Text("🔥 Streak", size=12), ft.Text(str(prof['streak']), size=18, weight=ft.FontWeight.BOLD, color=COLORS['warning'])], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)]), ft.Divider(), ft.Text(f"📚 Today: {prof['today_words']} words", size=13), ft.Text("✅ Goal achieved!" if prof['goal_achieved'] else "⏳ Goal in progress", size=13, color=COLORS['success'] if prof['goal_achieved'] else COLORS['warning'])], spacing=10), padding=20, width=350), actions=[ft.TextButton("Close", on_click=lambda e: self._close_dialog(dlg))])
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    # ========== Leaderboard ==========
    def show_leaderboard(self):
        self.page.clean()
        self.current_index = 6
        lb = self.user_manager.get_leaderboard(50)
        col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
        col.controls.append(ft.Container(content=ft.Row([ft.Text("Rank", width=50, weight=ft.FontWeight.BOLD), ft.Text("User", width=150, weight=ft.FontWeight.BOLD, expand=True), ft.Text("Level", width=60, weight=ft.FontWeight.BOLD), ft.Text("Today's Words", width=100, weight=ft.FontWeight.BOLD)]), padding=10, bgcolor=COLORS['sidebar'], border_radius=8))
        for i, (name, av, lvl, score) in enumerate(lb, 1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
            is_me = name == self.current_user['username']
            col.controls.append(ft.Container(content=ft.Row([ft.Text(medal, width=50), ft.Text(f"{av} {name}", width=150, expand=True, weight=ft.FontWeight.BOLD if is_me else None, color=COLORS['accent'] if is_me else COLORS['text']), ft.Text(f"Lv.{lvl}", width=60), ft.Text(str(score), width=100, color=COLORS['success'] if i<=3 else COLORS['text_secondary'])]), bgcolor=COLORS['accent'] if is_me else COLORS['card'], border_radius=8, padding=10))
        self.page.add(ft.Column([ft.Container(content=ft.Text("🏆 Leaderboard", size=24, weight=ft.FontWeight.BOLD, color=COLORS['accent']), padding=20), ft.Container(content=ft.Text("Top learners today", size=13, color=COLORS['text_secondary']), padding=ft.padding.symmetric(horizontal=20)), ft.Container(content=col, expand=True, padding=20), self._bottom_nav_bar()], spacing=10, expand=True))
        self.page.update()

    # ========== Settings ==========
    def show_settings(self):
        self.page.clean()
        self.current_index = 7
        goal_dd = ft.Dropdown(label="Daily Learning Goal", options=[ft.dropdown.Option(str(i)) for i in [5,10,15,20,25,30]], value=str(self.current_user['daily_goal']), width=200)
        def update_goal(e):
            self.user_manager.update_profile(self.current_user['id'], daily_goal=int(goal_dd.value))
            self.current_user['daily_goal'] = int(goal_dd.value)
            self._show_snack("✅ Goal updated!", COLORS['success'])
        avatars = ["😊","😎","🤓","👨‍🎓","👩‍🎓","🐱","🐶","🦊","🐼","⭐"]
        avatar_row = ft.Row([ft.Container(content=ft.Text(a, size=32), bgcolor=COLORS['card'] if a==self.current_user['avatar'] else COLORS['bg'], border_radius=10, padding=10, on_click=lambda _, av=a: self._update_avatar(av)) for a in avatars], spacing=10, wrap=True)
        plan = self.user_manager.get_user_plan(self.current_user['id'])
        plan_type = ft.Dropdown(label="Plan Type", options=[ft.dropdown.Option("daily"), ft.dropdown.Option("weekly"), ft.dropdown.Option("monthly"), ft.dropdown.Option("custom")], value=plan.get('plan_type','daily'), width=200)
        goals_col = ft.Column(spacing=10)
        goal_entries = {}
        def update_plan_inputs(e):
            goals_col.controls.clear()
            pt = plan_type.value
            if pt == 'weekly':
                goals = [("📚 Words per week", "weekly_goal_words", plan.get('weekly_goal_words',20)),
                         ("📖 Grammar rules per week", "weekly_goal_grammar", plan.get('weekly_goal_grammar',5)),
                         ("💬 Phrases per week", "weekly_goal_phrases", plan.get('weekly_goal_phrases',10))]
                for label, key, default in goals:
                    row = ft.Row([ft.Text(label, width=180, color=COLORS['text_secondary']), ft.TextField(value=str(default), width=100, text_align=ft.TextAlign.CENTER)])
                    goals_col.controls.append(row)
                    goal_entries[key] = row.controls[1]
            elif pt == 'monthly':
                goals = [("📚 Words per month", "monthly_goal_words", plan.get('monthly_goal_words',80)),
                         ("📖 Grammar rules per month", "monthly_goal_grammar", plan.get('monthly_goal_grammar',20)),
                         ("💬 Phrases per month", "monthly_goal_phrases", plan.get('monthly_goal_phrases',40))]
                for label, key, default in goals:
                    row = ft.Row([ft.Text(label, width=180, color=COLORS['text_secondary']), ft.TextField(value=str(default), width=100, text_align=ft.TextAlign.CENTER)])
                    goals_col.controls.append(row)
                    goal_entries[key] = row.controls[1]
            else:
                goals = [("📚 Words per day", "custom_goal_words", plan.get('custom_goal_words',10)),
                         ("📖 Grammar rules per day", "custom_goal_grammar", plan.get('custom_goal_grammar',3)),
                         ("💬 Phrases per day", "custom_goal_phrases", plan.get('custom_goal_phrases',5))]
                for label, key, default in goals:
                    row = ft.Row([ft.Text(label, width=180, color=COLORS['text_secondary']), ft.TextField(value=str(default), width=100, text_align=ft.TextAlign.CENTER)])
                    goals_col.controls.append(row)
                    goal_entries[key] = row.controls[1]
                if pt == 'custom':
                    row = ft.Row([ft.Text("⏱️ Interval (days):", width=180, color=COLORS['text_secondary']), ft.TextField(value=str(plan.get('custom_interval_days',1)), width=100, text_align=ft.TextAlign.CENTER)])
                    goals_col.controls.append(row)
                    goal_entries['custom_interval_days'] = row.controls[1]
            self.page.update()
        plan_type.on_change = update_plan_inputs
        def save_plan(e):
            updates = {}
            for k, entry in goal_entries.items():
                try:
                    updates[k] = int(entry.value)
                except:
                    self._show_snack("Please enter valid numbers", COLORS['warning'])
                    return
            self.user_manager.update_user_plan(self.current_user['id'], plan_type.value, **updates)
            self._show_snack("✅ Plan updated!", COLORS['success'])
        privacy = self.user_manager.get_privacy_settings(self.current_user['id'])
        pub_cb = ft.Checkbox(label="Make my profile public", value=privacy['profile_public'], check_color=COLORS['accent'])
        pub_cb.on_change = lambda e: self.user_manager.update_privacy(self.current_user['id'], pub_cb.value) or self._show_snack("✅ Privacy settings updated!", COLORS['success'])
        def logout(e):
            def confirm(e):
                self._close_dialog(confirm_dlg)
                self.current_user = None
                self.show_login()
            confirm_dlg = ft.AlertDialog(title=ft.Text("Logout", color=COLORS['warning']), content=ft.Text("Are you sure you want to logout?"), actions=[ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(confirm_dlg)), ft.ElevatedButton("Logout", on_click=confirm, bgcolor=COLORS['danger'])])
            self.page.dialog = confirm_dlg
            confirm_dlg.open = True
            self.page.update()
        def delete_data(e):
            def confirm(e):
                self._close_dialog(confirm_dlg)
                for table in ['vocabulary','phrases','practice_chat','daily_progress']:
                    self.user_manager.db.cursor.execute(f"DELETE FROM {table} WHERE user_id=?", (self.current_user['id'],))
                self.user_manager.db.conn.commit()
                self._show_snack("✅ All learning data cleared!", COLORS['success'])
                self.show_dashboard()
            confirm_dlg = ft.AlertDialog(title=ft.Text("Clear Data", color=COLORS['warning']), content=ft.Text("This will delete all your vocabulary, phrases, and practice history. This cannot be undone!"), actions=[ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(confirm_dlg)), ft.ElevatedButton("Clear", on_click=confirm, bgcolor=COLORS['danger'])])
            self.page.dialog = confirm_dlg
            confirm_dlg.open = True
            self.page.update()
        tabs = ft.Tabs(selected_index=0, tabs=[
            ft.Tab(text="⚙️ General", content=ft.Container(content=ft.Column([ft.Text("Daily Learning Goal", size=14, weight=ft.FontWeight.BOLD), goal_dd, ft.ElevatedButton("Update Goal", on_click=update_goal, bgcolor=COLORS['info']), ft.Divider(), ft.Text("Avatar", size=14, weight=ft.FontWeight.BOLD), avatar_row], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20, expand=True)),
            ft.Tab(text="📅 Learning Plan", content=ft.Container(content=ft.Column([ft.Text("Personalized Learning Plan", size=18, weight=ft.FontWeight.BOLD, color=COLORS['accent']), plan_type, goals_col, ft.ElevatedButton("💾 Save Plan Settings", on_click=save_plan, bgcolor=COLORS['success']), ft.Divider(), ft.Text(f"🔥 Current Streak: {plan.get('current_streak',0)} days", size=13), ft.Text(f"🏆 Longest Streak: {plan.get('longest_streak',0)} days", size=13)], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20, expand=True)),
            ft.Tab(text="🔒 Privacy", content=ft.Container(content=ft.Column([pub_cb, ft.Divider(), ft.Text("Account Information", size=14, weight=ft.FontWeight.BOLD), ft.Text(f"Username: {self.current_user['username']}", size=13), ft.Text(f"Email: {self.current_user['email']}", size=13), ft.Divider(), ft.ElevatedButton("Delete Account Data", on_click=delete_data, bgcolor=COLORS['danger']), ft.ElevatedButton("Logout", on_click=logout, bgcolor=COLORS['danger'])], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20, expand=True))
        ], expand=True)
        self.page.add(ft.Column([ft.Container(content=ft.Text("⚙️ Settings", size=24, weight=ft.FontWeight.BOLD, color=COLORS['accent']), padding=20), ft.Container(content=tabs, expand=True), self._bottom_nav_bar()], spacing=10, expand=True))
        update_plan_inputs(None)

    def _update_avatar(self, new_avatar):
        self.user_manager.update_profile(self.current_user['id'], avatar=new_avatar)
        self.current_user['avatar'] = new_avatar
        self._show_snack("✅ Avatar updated!", COLORS['success'])
        self.show_settings()

    def show_profile(self, e):
        wcnt = self.user_manager.db.cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE user_id=?", (self.current_user['id'],)).fetchone()[0]
        pcnt = self.user_manager.db.cursor.execute("SELECT COUNT(*) FROM phrases WHERE user_id=?", (self.current_user['id'],)).fetchone()[0]
        favcnt = len(self.user_manager.get_grammar_favorites())
        dlg = ft.AlertDialog(title=ft.Text("User Profile", color=COLORS['accent']), content=ft.Container(content=ft.Column([
            ft.Container(content=ft.Text(self.current_user['avatar'], size=50), alignment=ft.alignment.center),
            ft.Text(self.current_user['username'], size=20, weight=ft.FontWeight.BOLD, color=COLORS['text']),
            ft.Text(self.current_user['email'], size=13, color=COLORS['text_secondary']),
            ft.Divider(),
            ft.Row([
                ft.Column([ft.Text("⭐ Level", size=12), ft.Text(str(self.current_user['level']), size=18, weight=ft.FontWeight.BOLD, color=COLORS['accent'])], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ft.Column([ft.Text("🔥 Streak", size=12), ft.Text(str(self.current_user['current_streak']), size=18, weight=ft.FontWeight.BOLD, color=COLORS['warning'])], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            ]),
            ft.Divider(),
            ft.Row([
                ft.Column([ft.Text("📚 Words", size=12), ft.Text(str(wcnt), size=16, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ft.Column([ft.Text("💬 Phrases", size=12), ft.Text(str(pcnt), size=16, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ft.Column([ft.Text("⭐ Grammar", size=12), ft.Text(str(favcnt), size=16, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            ])
        ], spacing=10), padding=20, width=380), actions=[ft.TextButton("Close", on_click=lambda e: self._close_dialog(dlg))])
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def nav_change(self, index):
        self.current_index = index
        if index == 0: self.show_dashboard()
        elif index == 1: self.show_vocabulary()
        elif index == 2: self.show_grammar()
        elif index == 3: self.show_practice()
        elif index == 4: self.show_phrases()
        elif index == 5: self.show_community()
        elif index == 6: self.show_leaderboard()
        elif index == 7: self.show_settings()

def main(page: ft.Page):
    app = IDELingoApp()
    app.main(page)

if __name__ == "__main__":
    ft.app(target=main)
