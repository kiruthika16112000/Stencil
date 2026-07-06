from tkinter import messagebox

import customtkinter as ctk

from app.services.auth_service import AuthError
from app.services.password_policy import password_strength

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SECURITY_QUESTIONS = [
    "What is your favorite pet's name?",
    "What city were you born in?",
    "What is your mother's maiden name?",
    "What was the name of your first school?",
]

PASSWORD_HINT = "At least 8 characters, with uppercase, lowercase and a digit."

# First value applies in light mode, second in dark mode (CustomTkinter convention).
ADAPTIVE_TEXT_COLOR = ("gray10", "gray90")
ICON_TEXT_COLOR = ADAPTIVE_TEXT_COLOR
HINT_TEXT_COLOR = ("gray40", "gray65")
ERROR_TEXT_COLOR = ("#c0392b", "#ff6347")

STRENGTH_DISPLAY = {
    "weak": ("Weak", ERROR_TEXT_COLOR),
    "medium": ("Medium", ("#b8860b", "#ffa500")),
    "strong": ("Strong", ("#2e7d32", "#4caf50")),
}


def make_strength_label(master):
    return ctk.CTkLabel(master, text="", font=ctk.CTkFont(size=11))


def update_strength_label(label, password):
    if not password:
        label.configure(text="")
        return

    level = password_strength(password)
    text, color = STRENGTH_DISPLAY[level]
    label.configure(text=f"Password strength: {text}", text_color=color)


COLOR_THEMES = {
    "Blue": "blue",
    "Green": "green",
    "Dark Blue": "dark-blue",
}


class PasswordEntry(ctk.CTkFrame):
    """An entry + Show/Hide toggle button, usable anywhere a plain CTkEntry is."""

    def __init__(self, master, placeholder_text="", width=260, **kwargs):
        super().__init__(master, fg_color="transparent")

        self._visible = False

        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder_text, show="*", width=width - 56, **kwargs)
        self.entry.pack(side="left")

        self.toggle_button = ctk.CTkButton(self, text="Show", width=50, command=self._toggle)
        self.toggle_button.pack(side="left", padx=(6, 0))

    def _toggle(self):
        self._visible = not self._visible
        self.entry.configure(show="" if self._visible else "*")
        self.toggle_button.configure(text="Hide" if self._visible else "Show")

    def get(self):
        return self.entry.get()

    def delete(self, *args):
        self.entry.delete(*args)

    def insert(self, *args):
        self.entry.insert(*args)

    def bind(self, *args, **kwargs):
        self.entry.bind(*args, **kwargs)


class BaseFrame(ctk.CTkFrame):
    """Every screen's widgets live in self.content, kept centered no matter the window size."""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.place(relx=0.5, rely=0.5, anchor="center")


class LoginFrame(BaseFrame):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = self.content

        ctk.CTkLabel(c, text="Login", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 20))

        self.username_entry = ctk.CTkEntry(c, placeholder_text="Username", width=260)
        self.username_entry.pack(pady=8)

        self.password_entry = PasswordEntry(c, placeholder_text="Password", width=260)
        self.password_entry.pack(pady=8)
        self.password_entry.bind("<Return>", lambda _event: self._login())

        self.status_label = ctk.CTkLabel(c, text="", text_color=ERROR_TEXT_COLOR)
        self.status_label.pack(pady=(4, 0))

        ctk.CTkButton(c, text="Login", width=260, command=self._login).pack(pady=(16, 8))
        ctk.CTkButton(
            c,
            text="Manage Account",
            width=260,
            fg_color="transparent",
            border_width=1,
            text_color=ADAPTIVE_TEXT_COLOR,
            command=self._manage_account,
        ).pack(pady=4)
        ctk.CTkButton(
            c,
            text="Forgot password?",
            width=260,
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            text_color=("#1f6aa5", "#3b8ed0"),
            command=lambda: self.app.show_frame("forgot_password"),
        ).pack(pady=4)
        ctk.CTkButton(
            c,
            text="Create an account",
            width=260,
            fg_color="transparent",
            border_width=1,
            text_color=ADAPTIVE_TEXT_COLOR,
            command=lambda: self.app.show_frame("register"),
        ).pack(pady=4)

    def _authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        try:
            user = self.app.auth_service.login(username, password)
        except AuthError as error:
            self.status_label.configure(text=str(error))
            return None

        self.status_label.configure(text="")
        self.password_entry.delete(0, "end")
        return user

    def _login(self):
        user = self._authenticate()

        if user:
            self.app.show_frame("home")

    def _manage_account(self):
        user = self._authenticate()

        if user:
            self.app.show_frame("dashboard", user=user)


class HomeFrame(BaseFrame):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = self.content

        ctk.CTkLabel(c, text="Home", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(60, 8))
        ctk.CTkLabel(
            c,
            text="This screen is a placeholder.\nMore features will be built here later.",
            font=ctk.CTkFont(size=13),
            text_color=HINT_TEXT_COLOR,
            justify="center",
        ).pack(pady=(0, 20))


class RegisterFrame(BaseFrame):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = self.content

        ctk.CTkLabel(c, text="Create Account", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 16))

        ctk.CTkLabel(c, text="Username", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.username_entry = ctk.CTkEntry(c, placeholder_text="Choose a username", width=260)
        self.username_entry.pack(pady=(2, 10))

        ctk.CTkLabel(c, text="Password", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        ctk.CTkLabel(c, text=PASSWORD_HINT, font=ctk.CTkFont(size=10), text_color=HINT_TEXT_COLOR, anchor="w", width=260).pack()
        self.password_entry = PasswordEntry(c, placeholder_text="Choose a password", width=260)
        self.password_entry.pack(pady=(2, 0))
        self.password_entry.bind("<KeyRelease>", self._update_strength)
        self.strength_label = make_strength_label(c)
        self.strength_label.pack(pady=(0, 10))

        ctk.CTkLabel(c, text="Confirm password", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.confirm_entry = PasswordEntry(c, placeholder_text="Repeat the password above", width=260)
        self.confirm_entry.pack(pady=(2, 10))

        self.is_admin_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(c, text="Register as admin", variable=self.is_admin_var).pack(pady=8)

        ctk.CTkLabel(
            c, text="Security question (used to recover your password)", font=ctk.CTkFont(size=12), anchor="w", width=260
        ).pack(pady=(6, 0))
        self.security_question_var = ctk.StringVar(value=SECURITY_QUESTIONS[0])
        ctk.CTkOptionMenu(c, values=SECURITY_QUESTIONS, variable=self.security_question_var, width=260).pack(pady=(4, 10))

        ctk.CTkLabel(c, text="Answer", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.security_answer_entry = ctk.CTkEntry(c, placeholder_text="Answer to the question above", width=260)
        self.security_answer_entry.pack(pady=(2, 10))

        self.status_label = ctk.CTkLabel(c, text="", text_color=ERROR_TEXT_COLOR)
        self.status_label.pack(pady=(4, 0))

        ctk.CTkButton(c, text="Register", width=260, command=self._handle_register).pack(pady=(16, 8))
        ctk.CTkButton(
            c,
            text="Back to login",
            width=260,
            fg_color="transparent",
            border_width=1,
            text_color=ADAPTIVE_TEXT_COLOR,
            command=lambda: self.app.show_frame("login"),
        ).pack(pady=4)

    def _update_strength(self, _event=None):
        update_strength_label(self.strength_label, self.password_entry.get())

    def _handle_register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        security_answer = self.security_answer_entry.get()

        if password != confirm:
            self.status_label.configure(text="Passwords do not match.")
            return

        try:
            self.app.auth_service.register(
                username,
                password,
                self.is_admin_var.get(),
                security_question=self.security_question_var.get(),
                security_answer=security_answer,
            )
        except AuthError as error:
            self.status_label.configure(text=str(error))
            return

        self.status_label.configure(text="")
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.confirm_entry.delete(0, "end")
        self.security_answer_entry.delete(0, "end")
        self.strength_label.configure(text="")
        self.app.show_frame("login")


class DashboardFrame(BaseFrame):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = self.content

        self.welcome_label = ctk.CTkLabel(c, text="", font=ctk.CTkFont(size=24, weight="bold"))
        self.welcome_label.pack(pady=(50, 8))

        self.role_label = ctk.CTkLabel(c, text="", font=ctk.CTkFont(size=14))
        self.role_label.pack(pady=(0, 24))

        self.edit_button = ctk.CTkButton(c, text="Edit Profile", width=200, command=self._edit_profile)
        self.edit_button.pack(pady=6)

        self.manage_users_button = ctk.CTkButton(c, text="Manage Users", width=200, command=self._manage_users)

    def on_show(self, user):
        self.welcome_label.configure(text=f"Welcome, {user.username}!")
        self.role_label.configure(text=f"Role: {user.role()}")

        if user.role() == "Admin":
            self.manage_users_button.pack(pady=6, after=self.edit_button)
        else:
            self.manage_users_button.pack_forget()

    def _edit_profile(self):
        self.app.show_frame("edit_profile", user=self.app.auth_service.current_user)

    def _manage_users(self):
        self.app.show_frame("admin_panel")


class EditProfileFrame(BaseFrame):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = self.content

        ctk.CTkLabel(c, text="Edit Profile", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 4))
        ctk.CTkLabel(
            c,
            text="Leave the username or password fields\nblank to keep them unchanged.",
            font=ctk.CTkFont(size=12),
            text_color=HINT_TEXT_COLOR,
            justify="center",
        ).pack(pady=(0, 16))

        ctk.CTkLabel(c, text="Username", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.username_entry = ctk.CTkEntry(c, placeholder_text="Your username", width=260)
        self.username_entry.pack(pady=(2, 10))

        ctk.CTkLabel(c, text="New password (optional)", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        ctk.CTkLabel(c, text=PASSWORD_HINT, font=ctk.CTkFont(size=10), text_color=HINT_TEXT_COLOR, anchor="w", width=260).pack()
        self.password_entry = PasswordEntry(c, placeholder_text="Leave blank to keep current password", width=260)
        self.password_entry.pack(pady=(2, 0))
        self.password_entry.bind("<KeyRelease>", self._update_strength)
        self.strength_label = make_strength_label(c)
        self.strength_label.pack(pady=(0, 10))

        ctk.CTkLabel(c, text="Confirm new password", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.confirm_entry = PasswordEntry(c, placeholder_text="Repeat the new password above", width=260)
        self.confirm_entry.pack(pady=(2, 10))

        ctk.CTkLabel(
            c, text="Current password (required to save)", font=ctk.CTkFont(size=12), anchor="w", width=260
        ).pack()
        self.current_password_entry = PasswordEntry(c, placeholder_text="Needed to confirm it's you", width=260)
        self.current_password_entry.pack(pady=(2, 10))

        self.status_label = ctk.CTkLabel(c, text="", text_color=ERROR_TEXT_COLOR)
        self.status_label.pack(pady=(4, 0))

        ctk.CTkButton(c, text="Save Changes", width=260, command=self._save).pack(pady=(16, 8))
        ctk.CTkButton(
            c,
            text="Cancel",
            width=260,
            fg_color="transparent",
            border_width=1,
            text_color=ADAPTIVE_TEXT_COLOR,
            command=self._cancel,
        ).pack(pady=4)

    def on_show(self, user):
        self.status_label.configure(text="")
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, user.username)
        self.password_entry.delete(0, "end")
        self.confirm_entry.delete(0, "end")
        self.current_password_entry.delete(0, "end")
        self.strength_label.configure(text="")

    def _update_strength(self, _event=None):
        update_strength_label(self.strength_label, self.password_entry.get())

    def _cancel(self):
        self.app.show_frame("dashboard", user=self.app.auth_service.current_user)

    def _save(self):
        new_username = self.username_entry.get()
        new_password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        current_password = self.current_password_entry.get()

        if new_password != confirm:
            self.status_label.configure(text="New passwords do not match.")
            return

        try:
            updated_user = self.app.auth_service.update_profile(
                current_password, new_username=new_username, new_password=new_password
            )
        except AuthError as error:
            self.status_label.configure(text=str(error))
            return

        self.app.show_frame("dashboard", user=updated_user)


class ForgotPasswordFrame(BaseFrame):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = self.content

        self._target_username = None

        ctk.CTkLabel(c, text="Forgot Password", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 4))
        ctk.CTkLabel(
            c,
            text="Enter your username and click\n\"Find Account\" to see your security question.",
            font=ctk.CTkFont(size=12),
            text_color=HINT_TEXT_COLOR,
            justify="center",
        ).pack(pady=(0, 16))

        ctk.CTkLabel(c, text="Username", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.username_entry = ctk.CTkEntry(c, placeholder_text="Your username", width=260)
        self.username_entry.pack(pady=(2, 10))

        ctk.CTkButton(c, text="Find Account", width=260, command=self._find_account).pack(pady=(0, 8))

        # Step-two widgets: created now, packed/unpacked as a group once the account is found.
        self.question_caption_label = ctk.CTkLabel(
            c, text="Your security question:", font=ctk.CTkFont(size=12), anchor="w", width=260
        )
        self.question_label = ctk.CTkLabel(
            c, text="", font=ctk.CTkFont(size=13, weight="bold"), wraplength=260, justify="left", anchor="w", width=260
        )
        self.answer_label = ctk.CTkLabel(c, text="Your answer", font=ctk.CTkFont(size=12), anchor="w", width=260)
        self.answer_entry = ctk.CTkEntry(c, placeholder_text="Answer to the question above", width=260)
        self.new_password_label = ctk.CTkLabel(c, text="New password", font=ctk.CTkFont(size=12), anchor="w", width=260)
        self.new_password_hint_label = ctk.CTkLabel(
            c, text=PASSWORD_HINT, font=ctk.CTkFont(size=10), text_color=HINT_TEXT_COLOR, anchor="w", width=260
        )
        self.new_password_entry = PasswordEntry(c, placeholder_text="Choose a new password", width=260)
        self.new_password_entry.bind("<KeyRelease>", self._update_strength)
        self.strength_label = make_strength_label(c)
        self.confirm_label = ctk.CTkLabel(c, text="Confirm new password", font=ctk.CTkFont(size=12), anchor="w", width=260)
        self.confirm_entry = PasswordEntry(c, placeholder_text="Repeat the new password above", width=260)
        self.reset_button = ctk.CTkButton(c, text="Reset Password", width=260, command=self._reset_password)

        self._step_two_widgets = [
            (self.question_caption_label, {"pady": (6, 0)}),
            (self.question_label, {"pady": (0, 8)}),
            (self.answer_label, {"pady": (0, 0)}),
            (self.answer_entry, {"pady": (2, 10)}),
            (self.new_password_label, {"pady": (0, 0)}),
            (self.new_password_hint_label, {"pady": (0, 0)}),
            (self.new_password_entry, {"pady": (2, 0)}),
            (self.strength_label, {"pady": (0, 10)}),
            (self.confirm_label, {"pady": (0, 0)}),
            (self.confirm_entry, {"pady": (2, 10)}),
            (self.reset_button, {"pady": (10, 4)}),
        ]

        self.status_label = ctk.CTkLabel(c, text="", text_color=ERROR_TEXT_COLOR)
        self.status_label.pack(pady=(4, 0))

        ctk.CTkButton(
            c,
            text="Back to login",
            width=260,
            fg_color="transparent",
            border_width=1,
            text_color=ADAPTIVE_TEXT_COLOR,
            command=self._back_to_login,
        ).pack(pady=(16, 4))

    def on_show(self):
        self._target_username = None
        self.username_entry.delete(0, "end")
        self.status_label.configure(text="")
        self._hide_step_two()

    def _hide_step_two(self):
        for widget, _pack_opts in self._step_two_widgets:
            widget.pack_forget()

        self.answer_entry.delete(0, "end")
        self.new_password_entry.delete(0, "end")
        self.confirm_entry.delete(0, "end")
        self.strength_label.configure(text="")

    def _update_strength(self, _event=None):
        update_strength_label(self.strength_label, self.new_password_entry.get())

    def _find_account(self):
        self._hide_step_two()
        username = self.username_entry.get()

        try:
            question = self.app.auth_service.get_security_question(username)
        except AuthError as error:
            self.status_label.configure(text=str(error))
            return

        self._target_username = username.strip()
        self.status_label.configure(text="")
        self.question_label.configure(text=question)

        for widget, pack_opts in self._step_two_widgets:
            widget.pack(before=self.status_label, **pack_opts)

    def _reset_password(self):
        answer = self.answer_entry.get()
        new_password = self.new_password_entry.get()
        confirm = self.confirm_entry.get()

        if not answer.strip():
            self.status_label.configure(text="Please answer the security question.")
            return

        if new_password != confirm:
            self.status_label.configure(text="Passwords do not match.")
            return

        try:
            self.app.auth_service.reset_password(self._target_username, answer, new_password)
        except AuthError as error:
            self.status_label.configure(text=str(error))
            return

        self._back_to_login()

    def _back_to_login(self):
        self.app.show_frame("login")


class AdminPanelFrame(BaseFrame):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = self.content

        ctk.CTkLabel(c, text="Manage Users", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(24, 12))

        self.list_frame = ctk.CTkScrollableFrame(c, width=300, height=300)
        self.list_frame.pack(pady=(0, 12), padx=20, fill="both", expand=True)

        self.status_label = ctk.CTkLabel(c, text="", text_color=ERROR_TEXT_COLOR)
        self.status_label.pack(pady=(0, 4))

        ctk.CTkButton(
            c,
            text="Back to Dashboard",
            width=260,
            fg_color="transparent",
            border_width=1,
            text_color=ADAPTIVE_TEXT_COLOR,
            command=lambda: self.app.show_frame("dashboard", user=self.app.auth_service.current_user),
        ).pack(pady=(4, 16))

    def on_show(self):
        self.status_label.configure(text="")
        self._refresh()

    def _refresh(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        try:
            users = self.app.auth_service.list_users()
        except AuthError as error:
            self.status_label.configure(text=str(error))
            return

        current_username = self.app.auth_service.current_user.username

        for user in users:
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=4)

            label_text = f"{user.username} ({user.role()})"
            if user.username == current_username:
                label_text += " - you"

            ctk.CTkLabel(row, text=label_text, anchor="w").pack(side="left", fill="x", expand=True)

            if user.username != current_username:
                ctk.CTkButton(
                    row,
                    text="Delete",
                    width=70,
                    fg_color="darkred",
                    hover_color="#8b0000",
                    command=lambda username=user.username: self._delete(username),
                ).pack(side="right")

    def _delete(self, username):
        if not messagebox.askyesno("Delete User", f"Delete user '{username}'? This cannot be undone."):
            return

        try:
            self.app.auth_service.admin_delete_user(username)
        except AuthError as error:
            self.status_label.configure(text=str(error))
            return

        self._refresh()


class SettingsPopup(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)

        self.app = app
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        x = app.winfo_rootx() + app.winfo_width() - 210
        y = app.winfo_rooty() + 44
        self.geometry(f"200x180+{x}+{y}")

        card = ctk.CTkFrame(self, corner_radius=10, border_width=1)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(card, text="Display Settings", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(12, 10))

        ctk.CTkLabel(card, text="Appearance", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", padx=16)
        ctk.CTkOptionMenu(
            card,
            values=["Light", "Dark", "System"],
            variable=app.appearance_var,
            width=168,
            command=app._change_appearance,
        ).pack(pady=(2, 10), padx=16)

        ctk.CTkLabel(card, text="Color Theme", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", padx=16)
        ctk.CTkOptionMenu(
            card,
            values=list(COLOR_THEMES.keys()),
            variable=app.color_var,
            width=168,
            command=app._change_color_theme,
        ).pack(pady=(2, 12), padx=16)


class AccountPopup(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)

        self.app = app
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        x = app.account_button.winfo_rootx() - 60
        y = app.account_button.winfo_rooty() + app.account_button.winfo_height() + 4
        self.geometry(f"170x70+{x}+{y}")

        card = ctk.CTkFrame(self, corner_radius=10, border_width=1)
        card.pack(fill="both", expand=True)

        ctk.CTkButton(card, text="Logout", command=self._logout).pack(pady=14, padx=14, fill="x")

    def _logout(self):
        self.app._close_account_popup()
        self.app.auth_service.logout()
        self.app.show_frame("login")


class App(ctk.CTk):
    def __init__(self, auth_service):
        super().__init__()

        self.auth_service = auth_service

        self.title("User Login")
        self.geometry("380x760")
        self.minsize(340, 480)
        self.resizable(True, True)

        self.appearance_var = ctk.StringVar(value="Dark")
        self.color_var = ctk.StringVar(value="Blue")
        self._settings_window = None
        self._account_window = None

        self._current_frame_name = "login"
        self._current_frame_kwargs = {}

        self._build_ui()
        self.bind_all("<Button-1>", self._dismiss_popups_on_outside_click, add="+")

    def _dismiss_popups_on_outside_click(self, event):
        widget = event.widget

        if self._settings_window is not None and self._settings_window.winfo_exists():
            if not self._is_within(widget, self._settings_window) and not self._is_within(widget, self.settings_button):
                self._close_settings()

        if self._account_window is not None and self._account_window.winfo_exists():
            if not self._is_within(widget, self._account_window) and not self._is_within(widget, self.account_button):
                self._close_account_popup()

    @staticmethod
    def _is_within(widget, container):
        while widget is not None:
            if widget == container:
                return True

            widget = getattr(widget, "master", None)

        return False

    def _build_ui(self):
        self.topbar = ctk.CTkFrame(self, fg_color="transparent", height=36)
        self.topbar.pack(fill="x", padx=8, pady=(6, 0))

        self.settings_button = ctk.CTkButton(
            self.topbar,
            text="⚙",
            width=32,
            height=28,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
            text_color=ICON_TEXT_COLOR,
            command=self._toggle_settings,
        )
        self.settings_button.pack(side="right")

        self.account_button = ctk.CTkButton(
            self.topbar,
            text="👤",
            width=32,
            height=28,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
            text_color=ICON_TEXT_COLOR,
            command=self._toggle_account,
        )

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {
            "login": LoginFrame(self.container, self),
            "home": HomeFrame(self.container, self),
            "register": RegisterFrame(self.container, self),
            "dashboard": DashboardFrame(self.container, self),
            "edit_profile": EditProfileFrame(self.container, self),
            "forgot_password": ForgotPasswordFrame(self.container, self),
            "admin_panel": AdminPanelFrame(self.container, self),
        }

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(self._current_frame_name, **self._current_frame_kwargs)

    def show_frame(self, name, **kwargs):
        self._current_frame_name = name
        self._current_frame_kwargs = kwargs

        frame = self.frames[name]

        if hasattr(frame, "on_show"):
            frame.on_show(**kwargs)

        frame.tkraise()
        self._update_account_icon()

    def _update_account_icon(self):
        if self.auth_service.current_user is not None:
            self.account_button.pack(side="right", padx=(0, 6), before=self.settings_button)
        else:
            self.account_button.pack_forget()
            self._close_account_popup()

    def _toggle_settings(self):
        if self._settings_window is not None and self._settings_window.winfo_exists():
            self._settings_window.destroy()
            self._settings_window = None
            return

        self._settings_window = SettingsPopup(self)

    def _close_settings(self):
        if self._settings_window is not None and self._settings_window.winfo_exists():
            self._settings_window.destroy()

        self._settings_window = None

    def _toggle_account(self):
        if self._account_window is not None and self._account_window.winfo_exists():
            self._close_account_popup()
            return

        self._account_window = AccountPopup(self)

    def _close_account_popup(self):
        if self._account_window is not None and self._account_window.winfo_exists():
            self._account_window.destroy()

        self._account_window = None

    def _change_appearance(self, value):
        ctk.set_appearance_mode(value)

    def _change_color_theme(self, value):
        ctk.set_default_color_theme(COLOR_THEMES[value])

        self._close_settings()
        self._close_account_popup()
        self.topbar.destroy()
        self.container.destroy()
        self._build_ui()
