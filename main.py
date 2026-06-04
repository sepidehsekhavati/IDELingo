import flet as ft
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))

from UserManager import UserManager
from OfflineDictionary import OfflineDictionary

COLORS = {
    'bg': '#0a0a0a', 'card': '#1a1a2e', 'sidebar': '#111122',
    'accent': '#fbbf24', 'accent_dark': '#d97706', 'success': '#10b981',
    'danger': '#ef4444', 'warning': '#f59e0b', 'info': '#3b82f6',
    'text': '#f3f4f6', 'text_secondary': '#9ca3af', 'text_muted': '#6b7280'
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
            import traceback
            traceback.print_exc()
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

        # AppBar
        if os.path.exists(LOGO_PATH):
            try:
                page.appbar = ft.AppBar(
                    title=ft.Image(src=LOGO_PATH, width=50, height=50, fit=ft.ImageFit.CONTAIN),
                    center_title=True, bgcolor=COLORS['sidebar'],
                    actions=[ft.IconButton(icon=ft.icons.PERSON, icon_color=COLORS['text_secondary'], on_click=self.show_profile)]
                )
            except:
                page.appbar = ft.AppBar(title=ft.Text("", size=0), bgcolor=COLORS['sidebar'],
                    actions=[ft.IconButton(icon=ft.icons.PERSON, icon_color=COLORS['text_secondary'], on_click=self.show_profile)])
        else:
            page.appbar = ft.AppBar(title=ft.Text("", size=0), bgcolor=COLORS['sidebar'],
                actions=[ft.IconButton(icon=ft.icons.PERSON, icon_color=COLORS['text_secondary'], on_click=self.show_profile)])

        if self.init_backend():
            self.try_auto_login()
        else:
            self.show_error_page()

    def try_auto_login(self):
        """تلاش برای ورود خودکار"""
        try:
            stored = self.page.client_storage.get("idelingo_user")
            if stored and isinstance(stored, dict):
                user_id = stored.get("id")
                if user_id:
                    if self.user_manager.login_by_id(user_id):
                        self.current_user = self.user_manager.current_user
                        self.show_dashboard()
                        return
        except Exception as e:
            print(f"Auto login error: {e}")
            import traceback
            traceback.print_exc()
        self.show_login()

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
                ft.ElevatedButton("Retry", on_click=lambda e: self.init_backend() and self.try_auto_login(), bgcolor=COLORS['accent'])
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
                logo = ft.Container(content=ft.Column([
                    ft.Icon(ft.icons.SCHOOL, size=80, color=COLORS['accent']),
                    ft.Text("IDELingo", size=32, weight=ft.FontWeight.BOLD, color=COLORS['accent']),
                    ft.Text("Learn English Smarter", size=14, color=COLORS['text_secondary'])
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), margin=ft.margin.only(top=50, bottom=30))
        else:
            logo = ft.Container(content=ft.Column([
                ft.Icon(ft.icons.SCHOOL, size=80, color=COLORS['accent']),
                ft.Text("IDELingo", size=32, weight=ft.FontWeight.BOLD, color=COLORS['accent']),
                ft.Text("Learn English Smarter", size=14, color=COLORS['text_secondary'])
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), margin=ft.margin.only(top=50, bottom=30))

        user = ft.TextField(label="Username or Email", prefix_icon=ft.icons.PERSON, border_color=COLORS['text_muted'],
            focused_border_color=COLORS['accent'], color=COLORS['text'], width=300, height=50)
        pwd = ft.TextField(label="Password", prefix_icon=ft.icons.LOCK, password=True, can_reveal_password=True,
            border_color=COLORS['text_muted'], focused_border_color=COLORS['accent'], color=COLORS['text'], width=300, height=50)
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
                self.page.client_storage.set("idelingo_user", {"id": u["id"], "username": u["username"]})
                self.show_dashboard()
            else:
                err.value = msg
                err.visible = True
                self.page.update()

        self.page.add(ft.Container(
            content=ft.Column([
                logo,
                ft.Container(content=ft.Column([
                    user, pwd, err,
                    ft.ElevatedButton("Login", on_click=do_login, bgcolor=COLORS['accent'], color=COLORS['bg'], width=300, height=45),
                    ft.TextButton("Create New Account", on_click=lambda e: self.show_register(), style=ft.ButtonStyle(color=COLORS['accent']))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15), alignment=ft.alignment.center)
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
                ft.Container(content=ft.Column([
                    user, email, pwd, err,
                    ft.ElevatedButton("Sign Up", on_click=do_reg, bgcolor=COLORS['success'], color=COLORS['bg'], width=300, height=45),
                    ft.TextButton("Back to Login", on_click=lambda e: self.show_login(), style=ft.ButtonStyle(color=COLORS['accent']))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15), alignment=ft.alignment.center)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            expand=True
        ))
        self.page.update()

    def show_dashboard(self):
        self.page.clean()
        self.current_index = 0
        try:
            prog = self.user_manager.get_daily_progress(self.current_user['id'])
            hour = datetime.now().hour
            greet = "Good Evening" if hour > 18 else "Good Afternoon" if hour > 12 else "Good Morning"
            phrases_cnt = self.user_manager.db.execute_query("SELECT COUNT(*) FROM phrases WHERE user_id=?", (self.current_user['id'],), fetchone=True)[0]
        except Exception as e:
            print(f"Dashboard init error: {e}")
            import traceback
            traceback.print_exc()
            self.page.add(ft.Text(f"Error: {e}", color=COLORS['danger']))
            self.page.update()
            return

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
            ft.Container(content=ft.Column([
                ft.Text(f"{greet}, {self.current_user['username']}! 👋", size=22, weight=ft.FontWeight.BOLD, color=COLORS['text']),
                ft.Text(datetime.now().strftime("%A, %B %d, %Y"), size=12, color=COLORS['text_secondary'])
            ], spacing=5), padding=ft.padding.all(20)),
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
        items = [(ft.icons.HOME, "Home", 0), (ft.icons.BOOK, "Words", 1), (ft.icons.MENU_BOOK, "Grammar", 2),
                 (ft.icons.CHAT, "Practice", 3), (ft.icons.FORMAT_QUOTE, "Phrases", 4), (ft.icons.PEOPLE, "Community", 5),
                 (ft.icons.EMOJI_EVENTS, "Leaderboard", 6), (ft.icons.SETTINGS, "Settings", 7)]
        return ft.Container(content=ft.Row([self._nav_button(icon, label, idx) for icon, label, idx in items],
            alignment=ft.MainAxisAlignment.SPACE_AROUND), bgcolor=COLORS['sidebar'], padding=ft.padding.symmetric(vertical=8),
            border_radius=ft.border_radius.only(top_left=15, top_right=15))

    def _nav_button(self, icon, label, index):
        return ft.IconButton(icon=icon, icon_size=24,
            icon_color=COLORS['accent'] if self.current_index==index else COLORS['text_muted'],
            on_click=lambda e, i=index: self.nav_change(i), tooltip=label)

    # ========== Vocabulary (ساده شده برای تست) ==========
    def show_vocabulary(self):
        self.page.clean()
        self.current_index = 1
        self.page.add(ft.Text("Vocabulary Page - Coming Soon", size=24, color=COLORS['accent']))
        self.page.add(self._bottom_nav_bar())
        self.page.update()

    # ========== Grammar (ساده شده برای تست) ==========
    def show_grammar(self):
        self.page.clean()
        self.current_index = 2
        self.page.add(ft.Text("Grammar Page - Coming Soon", size=24, color=COLORS['accent']))
        self.page.add(self._bottom_nav_bar())
        self.page.update()

    # ========== Phrases (ساده شده برای تست) ==========
    def show_phrases(self):
        self.page.clean()
        self.current_index = 4
        self.page.add(ft.Text("Phrases Page - Coming Soon", size=24, color=COLORS['accent']))
        self.page.add(self._bottom_nav_bar())
        self.page.update()

    # ========== Practice (ساده شده برای تست) ==========
    def show_practice(self):
        self.page.clean()
        self.current_index = 3
        self.page.add(ft.Text("Practice Page - Coming Soon", size=24, color=COLORS['accent']))
        self.page.add(self._bottom_nav_bar())
        self.page.update()

    # ========== Community (ساده شده برای تست) ==========
    def show_community(self):
        self.page.clean()
        self.current_index = 5
        self.page.add(ft.Text("Community Page - Coming Soon", size=24, color=COLORS['accent']))
        self.page.add(self._bottom_nav_bar())
        self.page.update()

    # ========== Leaderboard (ساده شده برای تست) ==========
    def show_leaderboard(self):
        self.page.clean()
        self.current_index = 6
        self.page.add(ft.Text("Leaderboard Page - Coming Soon", size=24, color=COLORS['accent']))
        self.page.add(self._bottom_nav_bar())
        self.page.update()

    # ========== Settings ==========
    def show_settings(self):
        self.page.clean()
        self.current_index = 7
        
        goal_dd = ft.Dropdown(label="Daily Learning Goal", options=[ft.dropdown.Option(str(i)) for i in [5,10,15,20,25,30]],
            value=str(self.current_user['daily_goal']), width=200)
        def update_goal(e):
            self.user_manager.update_profile(self.current_user['id'], daily_goal=int(goal_dd.value))
            self.current_user['daily_goal'] = int(goal_dd.value)
            self._show_snack("✅ Goal updated!", COLORS['success'])
        
        avatars = ["😊","😎","🤓","👨‍🎓","👩‍🎓","🐱","🐶","🦊","🐼","⭐"]
        avatar_row = ft.Row([ft.Container(content=ft.Text(a, size=32), bgcolor=COLORS['card'] if a==self.current_user['avatar'] else COLORS['bg'],
            border_radius=10, padding=10, on_click=lambda _, av=a: self._update_avatar(av)) for a in avatars], spacing=10, wrap=True)
        
        def logout(e):
            def confirm(e):
                self._close_dialog(confirm_dlg)
                self.page.client_storage.remove("idelingo_user")
                self.current_user = None
                self.show_login()
            confirm_dlg = ft.AlertDialog(title=ft.Text("Logout", color=COLORS['warning']), content=ft.Text("Are you sure you want to logout?"),
                actions=[ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(confirm_dlg)),
                         ft.ElevatedButton("Logout", on_click=confirm, bgcolor=COLORS['danger'])])
            self.page.dialog = confirm_dlg
            confirm_dlg.open = True
            self.page.update()
        
        tabs = ft.Tabs(selected_index=0, tabs=[
            ft.Tab(text="⚙️ General", content=ft.Container(content=ft.Column([
                ft.Text("Daily Learning Goal", size=14, weight=ft.FontWeight.BOLD),
                goal_dd, ft.ElevatedButton("Update Goal", on_click=update_goal, bgcolor=COLORS['info']),
                ft.Divider(), ft.Text("Avatar", size=14, weight=ft.FontWeight.BOLD), avatar_row
            ], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20, expand=True)),
            ft.Tab(text="🔒 Privacy", content=ft.Container(content=ft.Column([
                ft.ElevatedButton("Logout", on_click=logout, bgcolor=COLORS['danger'])
            ], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20, expand=True))
        ], expand=True)
        
        self.page.add(ft.Column([
            ft.Container(content=ft.Text("⚙️ Settings", size=24, weight=ft.FontWeight.BOLD, color=COLORS['accent']), padding=20),
            ft.Container(content=tabs, expand=True),
            self._bottom_nav_bar()
        ], spacing=10, expand=True))
        self.page.update()

    def _update_avatar(self, new_avatar):
        self.user_manager.update_profile(self.current_user['id'], avatar=new_avatar)
        self.current_user['avatar'] = new_avatar
        self._show_snack("✅ Avatar updated!", COLORS['success'])
        self.show_settings()

    def show_profile(self, e):
        wcnt = self.user_manager.db.execute_query("SELECT COUNT(*) FROM vocabulary WHERE user_id=?", (self.current_user['id'],), fetchone=True)[0]
        pcnt = self.user_manager.db.execute_query("SELECT COUNT(*) FROM phrases WHERE user_id=?", (self.current_user['id'],), fetchone=True)[0]
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
