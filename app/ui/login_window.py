from tkinter import messagebox

import customtkinter as ctk

from app.services.auth_service import AuthError
from app.ui.actuator_debug_screen import ActuatorDebugFrame
from app.ui.assets import load_adaptive_logo
from app.ui.hero import make_login_hero_image
from app.ui.icons import gear_icon, lock_icon, person_icon, person_plus_icon
from app.ui.common import (
    ADAPTIVE_TEXT_COLOR,
    BaseFrame,
    CARD_BORDER_COLOR,
    CARD_COLOR,
    ERROR_TEXT_COLOR,
    HINT_TEXT_COLOR,
    PASSWORD_HINT,
    PasswordEntry,
    accent_names,
    accent_swatch_color,
    get_accent_name,
    link_button,
    make_strength_label,
    primary_button,
    primary_color,
    secondary_button,
    set_accent,
    styled_option_menu,
    update_strength_label,
)
from app.ui.main_screen import MainFrame
from app.ui.settings_screen import SettingsFrame
from app.ui.variant_screen import ManageVariantFrame, VariantSelectionFrame

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

MAX_WIDGET_SCALE = 1.2
TOPBAR_HEIGHT = 44
ICON_BUTTON_SIZE = 38

# Login's hero/form card is a fixed-size floating panel (like every other
# simple screen's BaseFrame card) centered over a plain backdrop that fills
# the rest of the window - so maximizing just reveals more backdrop instead
# of stretching the hero photo across an entire monitor.
LOGIN_WINDOW_WIDTH = 900
LOGIN_WINDOW_HEIGHT = 560
LOGIN_HERO_WIDTH = LOGIN_WINDOW_WIDTH // 2
# A plain, "decent" solid fill (explicitly not a gradient) for the backdrop
# behind Login's card once the window is bigger than the card itself.
LOGIN_BACKDROP_COLOR = ("#dfe2e8", "#16171d")

SECURITY_QUESTIONS = [
    "What is your favorite pet's name?",
    "What city were you born in?",
    "What is your mother's maiden name?",
    "What was the name of your first school?",
]

# Screens whose title lives in the topbar, next to the logo, instead of
# inside their own (vertically centered) content. Main Inspection shows the
# overall product name here rather than a per-screen label - it's the
# screen operators actually run the machine from, not just another item in
# the flow, so it carries the brand instead of "Manual Inspection".
SCREEN_TITLES = {
    "login": "Login",
    "variant_selection": "Select Variant",
    "settings": "Settings",
    "home": "Stencil Inspection",
    "debug": "Diagnostic Mode",
}

# The topbar title's default size (see App._build_ui) - screens can look up
# a larger size here to stand out, e.g. Main Inspection's brand header.
SCREEN_TITLE_FONT_SIZE = 18
SCREEN_TITLE_FONT_SIZE_OVERRIDES = {"home": 21}

# The OS window title (top-left corner of the window chrome) used to be a
# fixed "User Login" on every screen - this gives each one its own name
# instead. Kept separate from SCREEN_TITLES since that dict intentionally
# leaves some screens (Register, Dashboard, ...) blank in the in-app topbar
# (they already have their own heading inside the card).
WINDOW_TITLES = {
    "login": "Login",
    "variant_selection": "Select Variant",
    "manage_variant": "Manage Variants",
    "settings": "Settings",
    "home": "Stencil Inspection",
    "debug": "Diagnostic Mode",
    "register": "Create Account",
    "dashboard": "Dashboard",
    "edit_profile": "Edit Profile",
    "forgot_password": "Forgot Password",
    "admin_panel": "Manage Users",
}

# Screens whose content lives in self.content/self.card (see BaseFrame) -
# the window is resized to snugly fit that card on every switch to one of
# these. Settings/Main/Diagnostics bypass self.content for a dense,
# full-page layout instead, so they're left out and keep whatever size the
# window is currently at. Login also opts out - see FIXED_SIZE_FRAMES.
CARD_SIZED_FRAMES = {
    "register",
    "variant_selection",
    "manage_variant",
    "dashboard",
    "edit_profile",
    "forgot_password",
    "admin_panel",
}

# Dense, full-page screens (bypass self.content, like Settings/Main) whose
# window is still sized to fit their actual content rather than maximized -
# maximizing Diagnostics left a large empty gap below its columns on a
# full-height monitor, since its content doesn't grow to fill extra space.
SIZE_TO_FIT_FRAMES = {"debug"}

# Screens whose window opens sized to exactly fit their card with no
# backdrop margin, and hide the shared topbar (their card already carries
# its own branding) - just Login's hero/form split for now. Unlike
# CARD_SIZED_FRAMES, that fit is computed once at startup and never
# reapplied - the card stays this size afterward regardless of how the
# window itself is resized/maximized (see LoginFrame).
FIXED_SIZE_FRAMES = {"login"}


class LoginFrame(ctk.CTkFrame):
    """A fixed-size hero photo + form card, floating centered over a plain
    backdrop (see LOGIN_BACKDROP_COLOR) that fills whatever's left of the
    window - so maximizing (now true fullscreen, unlike the fixed-size
    window this used to require) just shows more backdrop around the same
    card instead of stretching the hero photo or the form across a monitor.

    The two halves are sized via grid's uniform column groups rather than
    an explicit pixel width - CTk's widget_scaling (see MAX_WIDGET_SCALE)
    multiplies explicit width=/height= constructor arguments, which
    previously desynced a scaled panel width against unscaled place()
    coordinates. Sizing purely from each side's own natural content (the
    hero image's real pixel size on the left, the packed form fields on the
    right) sidesteps that scaling pitfall entirely."""

    def __init__(self, master, app):
        super().__init__(master, fg_color=LOGIN_BACKDROP_COLOR)
        self.app = app

        self.card = ctk.CTkFrame(
            self, fg_color=CARD_COLOR, corner_radius=18, border_width=1, border_color=CARD_BORDER_COLOR
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.grid_columnconfigure(0, weight=1, uniform="half")
        self.card.grid_columnconfigure(1, weight=1, uniform="half")
        self.card.grid_rowconfigure(0, weight=1)

        hero_panel = ctk.CTkFrame(self.card, fg_color="transparent")
        hero_panel.grid(row=0, column=0, sticky="nsew")

        # Packed (not placed) so hero_panel's own natural size - and so the
        # grid row/column sizes derived from it - come directly from the
        # image's real pixel dimensions instead of a separately-tracked
        # width value that could drift out of sync with it.
        self._hero_label = ctk.CTkLabel(hero_panel, text="")
        self._hero_label.pack(fill="both", expand=True)
        self._refresh_hero()

        # The logo/wordmark/tagline are all baked directly into hero_image
        # itself (see make_login_hero_image) rather than laid out as
        # separate CTkLabel widgets here - a label's "transparent" fg_color
        # is CTk's simulated transparency (it just colors itself to match
        # whatever flat color it thinks its parent is), not true pixel
        # compositing against a sibling image, so any overlay widget here
        # showed up as a visible box against this photo's varied pixels.

        form_panel = ctk.CTkFrame(self.card, fg_color=CARD_COLOR)
        form_panel.grid(row=0, column=1, sticky="nsew")

        c = ctk.CTkFrame(form_panel, fg_color="transparent")
        c.place(relx=0.5, rely=0.5, anchor="center")
        self.content = c

        ctk.CTkLabel(c, text="Welcome Back", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 2))
        ctk.CTkLabel(
            c,
            text="Sign in to continue to Stencil Inspection",
            font=ctk.CTkFont(size=12),
            text_color=HINT_TEXT_COLOR,
            width=260,
            wraplength=260,
            justify="center",
        ).pack(pady=(0, 20))

        ctk.CTkLabel(c, text="Username", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.username_entry = ctk.CTkEntry(c, placeholder_text="Enter your username", width=260, height=36)
        self.username_entry.pack(pady=(4, 12))

        ctk.CTkLabel(c, text="Password", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.password_entry = PasswordEntry(c, placeholder_text="Enter your password", width=260)
        self.password_entry.pack(pady=(4, 0))
        self.password_entry.bind("<Return>", lambda _event: self._login())

        self.status_label = ctk.CTkLabel(
            c, text="", text_color=ERROR_TEXT_COLOR, width=260, wraplength=260, justify="center"
        )
        self.status_label.pack(pady=(6, 0))

        primary_button(c, "Login  →", self._login, height=40).pack(pady=(18, 4))
        link_button(
            c,
            "  Forgot password?",
            lambda: self.app.show_frame("forgot_password"),
            image=lock_icon(size=26, light_color=primary_color()[0], dark_color=primary_color()[1]),
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack()

        divider_row = ctk.CTkFrame(c, fg_color="transparent")
        divider_row.pack(fill="x", pady=(18, 10))
        ctk.CTkFrame(divider_row, fg_color=CARD_BORDER_COLOR, height=1).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(divider_row, text="or", font=ctk.CTkFont(size=11), text_color=HINT_TEXT_COLOR).pack(
            side="left", padx=8
        )
        ctk.CTkFrame(divider_row, fg_color=CARD_BORDER_COLOR, height=1).pack(side="left", fill="x", expand=True)

        secondary_button(
            c,
            "  Create an account",
            lambda: self.app.show_frame("register"),
            image=person_plus_icon(size=18),
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(0, 6))
        link_button(
            c,
            "  Manage Account",
            self._manage_account,
            image=person_icon(size=16, light_color=primary_color()[0], dark_color=primary_color()[1]),
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack()

    def _refresh_hero(self):
        """Picks a new random photo from data/UI Reference (see
        make_login_hero_image) - called once at construction and again every
        time this screen is shown, since the frame itself is built once and
        reused via tkraise() rather than recreated on each visit."""
        hero_image = make_login_hero_image(LOGIN_HERO_WIDTH, LOGIN_WINDOW_HEIGHT, primary_color()[1])
        # Kept alive on the label itself via configure(image=...); also held
        # here so it isn't garbage-collected out from under the label.
        self._hero_image = hero_image
        self._hero_label.configure(image=hero_image)

    def on_show(self):
        self._refresh_hero()

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
            self.app.variant_service.load()
            self.app.show_frame("variant_selection")

    def _manage_account(self):
        user = self._authenticate()

        if user:
            self.app.show_frame("dashboard", user=user)


class RegisterFrame(BaseFrame):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = self.content

        ctk.CTkLabel(c, text="Create Account", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 2))
        ctk.CTkLabel(
            c, text="Sign up to get started", font=ctk.CTkFont(size=12), text_color=HINT_TEXT_COLOR, width=260
        ).pack(pady=(0, 18))

        ctk.CTkLabel(c, text="Username", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.username_entry = ctk.CTkEntry(c, placeholder_text="Choose a username", width=260, height=36)
        self.username_entry.pack(pady=(4, 10))

        ctk.CTkLabel(c, text="Password", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        ctk.CTkLabel(c, text=PASSWORD_HINT, font=ctk.CTkFont(size=10), text_color=HINT_TEXT_COLOR, anchor="w", width=260).pack()
        self.password_entry = PasswordEntry(c, placeholder_text="Choose a password", width=260, height=36)
        self.password_entry.pack(pady=(4, 0))
        self.password_entry.bind("<KeyRelease>", self._update_strength)
        self.strength_label = make_strength_label(c)
        self.strength_label.pack(pady=(0, 10))

        ctk.CTkLabel(c, text="Confirm password", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.confirm_entry = PasswordEntry(c, placeholder_text="Repeat the password above", width=260, height=36)
        self.confirm_entry.pack(pady=(4, 10))

        self.is_admin_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(c, text="Register as admin", variable=self.is_admin_var).pack(pady=8)

        ctk.CTkLabel(
            c, text="Security question (used to recover your password)", font=ctk.CTkFont(size=12), anchor="w", width=260
        ).pack(pady=(6, 0))
        self.security_question_var = ctk.StringVar(value=SECURITY_QUESTIONS[0])
        styled_option_menu(
            c, values=SECURITY_QUESTIONS, variable=self.security_question_var, width=260, height=36
        ).pack(pady=(4, 10))

        ctk.CTkLabel(c, text="Answer", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.security_answer_entry = ctk.CTkEntry(c, placeholder_text="Answer to the question above", width=260, height=36)
        self.security_answer_entry.pack(pady=(4, 10))

        self.status_label = ctk.CTkLabel(
            c, text="", text_color=ERROR_TEXT_COLOR, width=260, wraplength=260, justify="center"
        )
        self.status_label.pack(pady=(4, 0))

        primary_button(c, "Register", self._handle_register, height=40).pack(pady=(18, 4))
        link_button(c, "Back to login", lambda: self.app.show_frame("login")).pack()

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

        self.welcome_label = ctk.CTkLabel(c, text="", font=ctk.CTkFont(size=22, weight="bold"))
        self.welcome_label.pack(pady=(0, 2))

        self.role_label = ctk.CTkLabel(c, text="", font=ctk.CTkFont(size=12), text_color=HINT_TEXT_COLOR)
        self.role_label.pack(pady=(0, 22))

        self.edit_button = primary_button(c, "Edit Profile", self._edit_profile, width=220, height=40)
        self.edit_button.pack(pady=6)

        self.manage_users_button = secondary_button(c, "Manage Users", self._manage_users, width=220)

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

        ctk.CTkLabel(c, text="Edit Profile", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 2))
        ctk.CTkLabel(
            c,
            text="Leave the username or password fields\nblank to keep them unchanged.",
            font=ctk.CTkFont(size=12),
            text_color=HINT_TEXT_COLOR,
            width=260,
            justify="center",
        ).pack(pady=(0, 18))

        ctk.CTkLabel(c, text="Username", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.username_entry = ctk.CTkEntry(c, placeholder_text="Your username", width=260, height=36)
        self.username_entry.pack(pady=(4, 10))

        ctk.CTkLabel(c, text="New password (optional)", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        ctk.CTkLabel(c, text=PASSWORD_HINT, font=ctk.CTkFont(size=10), text_color=HINT_TEXT_COLOR, anchor="w", width=260).pack()
        self.password_entry = PasswordEntry(c, placeholder_text="Leave blank to keep current password", width=260, height=36)
        self.password_entry.pack(pady=(4, 0))
        self.password_entry.bind("<KeyRelease>", self._update_strength)
        self.strength_label = make_strength_label(c)
        self.strength_label.pack(pady=(0, 10))

        ctk.CTkLabel(c, text="Confirm new password", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.confirm_entry = PasswordEntry(c, placeholder_text="Repeat the new password above", width=260, height=36)
        self.confirm_entry.pack(pady=(4, 10))

        ctk.CTkLabel(
            c, text="Current password (required to save)", font=ctk.CTkFont(size=12), anchor="w", width=260
        ).pack()
        self.current_password_entry = PasswordEntry(c, placeholder_text="Needed to confirm it's you", width=260, height=36)
        self.current_password_entry.pack(pady=(4, 10))

        self.status_label = ctk.CTkLabel(
            c, text="", text_color=ERROR_TEXT_COLOR, width=260, wraplength=260, justify="center"
        )
        self.status_label.pack(pady=(4, 0))

        primary_button(c, "Save Changes", self._save, height=40).pack(pady=(18, 4))
        link_button(c, "Cancel", self._cancel).pack()

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

        ctk.CTkLabel(c, text="Forgot Password", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 2))
        ctk.CTkLabel(
            c,
            text="Enter your username and click\n\"Find Account\" to see your security question.",
            font=ctk.CTkFont(size=12),
            text_color=HINT_TEXT_COLOR,
            width=260,
            justify="center",
        ).pack(pady=(0, 18))

        ctk.CTkLabel(c, text="Username", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.username_entry = ctk.CTkEntry(c, placeholder_text="Your username", width=260, height=36)
        self.username_entry.pack(pady=(4, 10))

        primary_button(c, "Find Account", self._find_account, height=40).pack(pady=(0, 8))

        # Step-two widgets: created now, packed/unpacked as a group once the account is found.
        self.question_caption_label = ctk.CTkLabel(
            c, text="Your security question:", font=ctk.CTkFont(size=12), anchor="w", width=260
        )
        self.question_label = ctk.CTkLabel(
            c, text="", font=ctk.CTkFont(size=13, weight="bold"), wraplength=260, justify="left", anchor="w", width=260
        )
        self.answer_label = ctk.CTkLabel(c, text="Your answer", font=ctk.CTkFont(size=12), anchor="w", width=260)
        self.answer_entry = ctk.CTkEntry(c, placeholder_text="Answer to the question above", width=260, height=36)
        self.new_password_label = ctk.CTkLabel(c, text="New password", font=ctk.CTkFont(size=12), anchor="w", width=260)
        self.new_password_hint_label = ctk.CTkLabel(
            c, text=PASSWORD_HINT, font=ctk.CTkFont(size=10), text_color=HINT_TEXT_COLOR, anchor="w", width=260
        )
        self.new_password_entry = PasswordEntry(c, placeholder_text="Choose a new password", width=260, height=36)
        self.new_password_entry.bind("<KeyRelease>", self._update_strength)
        self.strength_label = make_strength_label(c)
        self.confirm_label = ctk.CTkLabel(c, text="Confirm new password", font=ctk.CTkFont(size=12), anchor="w", width=260)
        self.confirm_entry = PasswordEntry(c, placeholder_text="Repeat the new password above", width=260, height=36)
        self.reset_button = primary_button(c, "Reset Password", self._reset_password, height=40)

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

        self.status_label = ctk.CTkLabel(
            c, text="", text_color=ERROR_TEXT_COLOR, width=260, wraplength=260, justify="center"
        )
        self.status_label.pack(pady=(4, 0))

        link_button(c, "Back to login", self._back_to_login).pack(pady=(16, 4))

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

        # The card just grew a lot taller (security question, new password,
        # confirm) - resize the window again so the Reset Password button
        # doesn't end up pushed outside the visible area.
        self.app._size_to_content("forgot_password")

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

        ctk.CTkLabel(c, text="Manage Users", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 2))
        ctk.CTkLabel(
            c, text="View accounts and remove access", font=ctk.CTkFont(size=12), text_color=HINT_TEXT_COLOR, width=300
        ).pack(pady=(0, 16))

        self.list_frame = ctk.CTkScrollableFrame(c, width=300, height=300)
        self.list_frame.pack(pady=(0, 12), padx=20, fill="both", expand=True)

        self.status_label = ctk.CTkLabel(
            c, text="", text_color=ERROR_TEXT_COLOR, width=260, wraplength=260, justify="center"
        )
        self.status_label.pack(pady=(0, 4))

        link_button(
            c, "Back to Dashboard", lambda: self.app.show_frame("dashboard", user=self.app.auth_service.current_user)
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


def _position_beside(app, button, width, height, gap=8, margin=4):
    """Anchor a popup to the left of button, bottom-aligned with it, clamped
    to stay fully inside the app window (rather than below/off the edge)."""
    x = button.winfo_rootx() - width - gap
    x = max(app.winfo_rootx() + margin, x)

    y = button.winfo_rooty() + button.winfo_height() - height
    y = max(app.winfo_rooty() + margin, y)

    return x, y


# Sun/moon render fine as plain glyphs; "System" used to be a text gear
# ("⚙") which rendered like a flower at this size/font - drawn as an image
# instead (see app.ui.icons) for a reliably clean shape.
THEME_MODE_TEXT_ICONS = {"Light": "☀", "Dark": "☽"}


class SettingsPopup(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)

        self.app = app
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        scale = app._current_scale
        # Wide enough for all 5 preset-color swatches at MAX_WIDGET_SCALE -
        # 240 was too narrow and clipped the last swatch (Amber) against the
        # popup's own edge instead of showing a full circle.
        width, height = int(280 * scale), int(250 * scale)
        x, y = _position_beside(app, app.settings_button, width, height)
        self.geometry(f"{width}x{height}+{x}+{y}")

        card = ctk.CTkFrame(self, corner_radius=12, border_width=1, border_color=CARD_BORDER_COLOR)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card, text="THEME MODE", font=ctk.CTkFont(size=10, weight="bold"), text_color=HINT_TEXT_COLOR, anchor="w"
        ).pack(fill="x", padx=16, pady=(14, 6))

        mode_row = ctk.CTkFrame(card, fg_color="transparent")
        mode_row.pack(padx=16)

        self._mode_buttons = {}
        for value in ("Light", "Dark", "System"):
            icon_kwargs = (
                {"text": "", "image": gear_icon(size=16)}
                if value == "System"
                else {"text": THEME_MODE_TEXT_ICONS[value]}
            )
            button = ctk.CTkButton(
                mode_row,
                width=44,
                height=38,
                corner_radius=8,
                font=ctk.CTkFont(size=15),
                fg_color=("gray90", "gray20"),
                text_color=ADAPTIVE_TEXT_COLOR,
                border_width=2,
                # CTk's border_color doesn't accept "transparent" - match
                # the button's own background instead, so the border simply
                # isn't visible until this option is selected.
                border_color=("gray90", "gray20"),
                hover_color=("gray85", "gray25"),
                command=lambda v=value: self._select_mode(v),
                **icon_kwargs,
            )
            button.pack(side="left", padx=4)
            self._mode_buttons[value] = button

        ctk.CTkFrame(card, fg_color=CARD_BORDER_COLOR, height=1).pack(fill="x", padx=16, pady=(14, 10))

        ctk.CTkLabel(
            card,
            text="PRESET COLOR",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=HINT_TEXT_COLOR,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 6))

        swatch_row = ctk.CTkFrame(card, fg_color="transparent")
        swatch_row.pack(padx=16, pady=(0, 14))

        self._swatch_buttons = {}
        for name in accent_names():
            hex_color = accent_swatch_color(name)
            button = ctk.CTkButton(
                swatch_row,
                text="",
                width=34,
                height=34,
                corner_radius=17,
                fg_color=hex_color,
                hover_color=hex_color,
                text_color="white",
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda n=name: self._select_color(n),
            )
            button.pack(side="left", padx=5)
            self._swatch_buttons[name] = button

        self._refresh_selection()

    def _select_mode(self, value):
        self.app.appearance_var.set(value)
        self.app._change_appearance(value)
        self._refresh_selection()

    def _select_color(self, name):
        self.app.color_var.set(name)
        # Rebuilds the whole UI (including this popup's owning button), and
        # already closes this popup as part of that - nothing left to do
        # here afterward.
        self.app._change_color_theme(name)

    def _refresh_selection(self):
        for value, button in self._mode_buttons.items():
            selected = self.app.appearance_var.get() == value
            button.configure(border_color=primary_color() if selected else ("gray90", "gray20"))

        for name, button in self._swatch_buttons.items():
            selected = self.app.color_var.get() == name
            button.configure(text="✓" if selected else "")


class AccountPopup(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)

        self.app = app
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        scale = app._current_scale
        width, height = int(190 * scale), int(104 * scale)
        x, y = _position_beside(app, app.account_button, width, height)
        self.geometry(f"{width}x{height}+{x}+{y}")

        card = ctk.CTkFrame(self, corner_radius=10, border_width=1, border_color=CARD_BORDER_COLOR)
        card.pack(fill="both", expand=True)

        username = app.auth_service.current_user.username
        ctk.CTkLabel(
            card,
            text=username,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=162,
            wraplength=162,
        ).pack(pady=(14, 0), padx=14)

        ctk.CTkFrame(card, fg_color=CARD_BORDER_COLOR, height=1).pack(fill="x", padx=14, pady=(10, 10))

        ctk.CTkButton(card, text="Logout", command=self._logout).pack(pady=(0, 14), padx=14, fill="x")

    def _logout(self):
        self.app._close_account_popup()
        self.app.auth_service.logout()
        self.app.show_frame("login")


class App(ctk.CTk):
    def __init__(self, auth_service, variant_service, settings_service, actuator_service, camera):
        super().__init__()

        self.auth_service = auth_service
        self.variant_service = variant_service
        self.settings_service = settings_service
        self.actuator_service = actuator_service
        self.camera = camera

        self.minsize(320, 420)
        self.resizable(True, True)
        # icon_stack's own fg_color="transparent" (see _build_ui) is CTk's
        # simulated transparency - it just matches whatever flat color it
        # thinks its parent (this root window) is, not the actual pixels
        # rendered beneath it. Without this, the root's own CTk-default
        # background (not necessarily matching CARD_COLOR) showed through
        # as a visible square around the circular settings/account
        # buttons, most noticeably in light mode.
        self.configure(fg_color=CARD_COLOR)

        self.appearance_var = ctk.StringVar(value="Dark")
        self.color_var = ctk.StringVar(value=get_accent_name())
        self._settings_window = None
        self._account_window = None

        # Fonts/buttons are always drawn at the max scale (instead of
        # growing with the window) - the window is sized to fit its content
        # at that scale instead, so screens open compact with no dead space
        # rather than tiny widgets in a mostly-empty maximized window.
        self._current_scale = MAX_WIDGET_SCALE
        ctk.set_widget_scaling(MAX_WIDGET_SCALE)

        self._current_frame_name = "login"
        self._current_frame_kwargs = {}

        self.demeter_logo = load_adaptive_logo("demeter_logo.png", height=34)

        self._build_ui()
        self.bind_all("<Button-1>", self._dismiss_popups_on_outside_click, add="+")
        self.bind("<Configure>", self._on_resize)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _maximize(self):
        """Settings/Main/Diagnostics are dense, full-page layouts (not a
        centered card) - they get the whole screen instead of the compact
        card sizing the simple screens use."""
        if self.state() != "zoomed":
            self.state("zoomed")

        self.update_idletasks()

    def _size_to_fixed(self, frame_name):
        """Login's initial window size - just big enough to fit its card
        with no backdrop margin at startup. The card itself stays this
        fixed size afterward regardless of the window's own size (see
        LoginFrame), so unlike every other screen's sizing method this one
        never needs to re-run after the first show_frame("login").

        Measured from the card's own actual winfo_reqwidth()/reqheight()
        (like _size_to_content below) rather than a hardcoded constant -
        widget_scaling (see MAX_WIDGET_SCALE) inflates the card's real
        rendered size well past its nominal LOGIN_WINDOW_WIDTH/HEIGHT, and
        a stale hardcoded window size silently clipped the oversized card."""
        if self.state() == "zoomed":
            self.state("normal")

        self.update_idletasks()

        card = self.frames[frame_name].card
        width = card.winfo_reqwidth()
        height = card.winfo_reqheight()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")
        self.update_idletasks()

    def _size_to_content(self, frame_name):
        """Resize (and center) the window to snugly fit a screen's card,
        instead of a fixed guessed geometry - avoids empty dead space
        around a small screen like Login."""
        if self.state() == "zoomed":
            self.state("normal")

        self.update_idletasks()

        card = self.frames[frame_name].card
        width = card.winfo_reqwidth() + 100
        # Extra vertical margin (beyond the topbar) so the floating
        # settings/account icon stack in the bottom-right corner has room
        # to sit clear of the card's rounded corner instead of overlapping
        # it - the card is centered in this space, so the margin splits
        # evenly above and below it. Kept just big enough for that
        # clearance (not more) - a larger margin left the icon stack
        # looking disconnected, floating in a mostly-empty gap below the
        # card instead of sitting close to it.
        height = card.winfo_reqheight() + TOPBAR_HEIGHT + 100

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")
        self.update_idletasks()

    def _size_to_frame(self, frame_name):
        """Like _size_to_content, but measures the frame's own natural size
        directly rather than a nested self.card - Diagnostics packs its
        columns straight onto self instead of a centered card (see
        ActuatorDebugFrame), so sizing off its actual content instead of
        maximizing avoids the large empty gap that used to sit below it on
        a full-height monitor."""
        if self.state() == "zoomed":
            self.state("normal")

        self.update_idletasks()

        frame = self.frames[frame_name]
        width = frame.winfo_reqwidth()
        # Extra bottom margin - the floating settings/account icon stack
        # (see _build_ui) is anchored to the whole window's bottom-right
        # corner, not this frame, so without slack below the content it
        # overlapped the Light Control panel's Set Brightness button.
        height = frame.winfo_reqheight() + TOPBAR_HEIGHT + 90

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")
        self.update_idletasks()

    def _on_close(self):
        home_frame = self.frames.get("home")
        if home_frame is not None and hasattr(home_frame, "shutdown"):
            home_frame.shutdown()

        self.destroy()

    def _on_resize(self, event):
        if event.widget is not self:
            return

        frame = self.frames.get(self._current_frame_name)
        if frame is not None and hasattr(frame, "on_app_resize"):
            frame.on_app_resize()

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

    def _make_icon_button(self, master, image, command, size=ICON_BUTTON_SIZE):
        """A truly circular icon button. CTkButton's own text/image padding
        grows width and height by different, unpredictable amounts once
        there's content, so a plain CTkButton can't be forced into a
        perfect circle - instead, a fixed-size frame (pack_propagate off)
        draws the circle, and the icon is just a label centered on top of
        it, decoupling the shape from the icon's natural size."""
        frame = ctk.CTkFrame(
            master,
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color=CARD_COLOR,
            border_width=1,
            border_color=CARD_BORDER_COLOR,
        )
        frame.pack_propagate(False)

        label = ctk.CTkLabel(frame, text="", image=image)
        label.place(relx=0.5, rely=0.5, anchor="center")

        def on_enter(_event):
            frame.configure(fg_color=("gray85", "gray25"))

        def on_leave(_event):
            frame.configure(fg_color=CARD_COLOR)

        for widget in (frame, label):
            widget.bind("<Button-1>", lambda _event: command())
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        return frame

    def _build_ui(self):
        # Solid, not transparent - the topbar sits right where the
        # background gradient is strongest (top edge), so a transparent fill
        # let the gradient wash through the header and made it look like its
        # own separate gradient box. A flat surface keeps the header reading
        # as chrome, with the gradient only visible in the actual content area.
        self.topbar = ctk.CTkFrame(self, fg_color=CARD_COLOR, height=44, corner_radius=12)
        self.topbar.pack(fill="x", padx=8, pady=(6, 0))
        self.topbar.pack_propagate(False)

        ctk.CTkLabel(self.topbar, image=self.demeter_logo, text="").pack(side="left", padx=(2, 0))

        self.screen_title_label = ctk.CTkLabel(
            self.topbar, text="", font=ctk.CTkFont(size=18, weight="bold"), text_color=primary_color()
        )
        self.screen_title_label.place(relx=0.5, rely=0.5, anchor="center")

        self.topbar_divider = ctk.CTkFrame(self, fg_color=CARD_BORDER_COLOR, height=1)
        self.topbar_divider.pack(fill="x", padx=8, pady=(6, 0))

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Floating overlay pinned to the bottom-right corner of the whole
        # window (not the topbar), so it stays put regardless of which
        # frame is showing and however the window is resized.
        self.icon_stack = ctk.CTkFrame(self, fg_color="transparent")
        self.icon_stack.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")
        self.icon_stack.lift()

        self.settings_button = self._make_icon_button(self.icon_stack, gear_icon(size=20), self._toggle_settings)
        self.settings_button.pack(side="top")

        self.account_button = self._make_icon_button(self.icon_stack, person_icon(size=20), self._toggle_account)

        self.frames = {
            "login": LoginFrame(self.container, self),
            "variant_selection": VariantSelectionFrame(self.container, self),
            "manage_variant": ManageVariantFrame(self.container, self),
            "settings": SettingsFrame(self.container, self),
            "home": MainFrame(self.container, self),
            "debug": ActuatorDebugFrame(self.container, self),
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
        title_font_size = SCREEN_TITLE_FONT_SIZE_OVERRIDES.get(name, SCREEN_TITLE_FONT_SIZE)
        self.screen_title_label.configure(
            text=SCREEN_TITLES.get(name, ""), font=ctk.CTkFont(size=title_font_size, weight="bold")
        )
        self.title(WINDOW_TITLES.get(name, "Stencil Inspection"))

        # The topbar (shared Demeter logo + screen title strip) is hidden for
        # Login's own hero panel, which already carries its own branding and
        # needs the full window height for the branded photo - re-shown (in
        # the same top/before-container order) for every other screen.
        self.topbar.pack_forget()
        self.topbar_divider.pack_forget()
        self.container.pack_forget()
        if name not in FIXED_SIZE_FRAMES:
            self.topbar.pack(fill="x", padx=8, pady=(6, 0))
            self.topbar_divider.pack(fill="x", padx=8, pady=(6, 0))
        self.container.pack(fill="both", expand=True)

        if name in FIXED_SIZE_FRAMES:
            # Resizable (not locked) so the title bar's maximize button
            # stays enabled like every other screen - the hero photo just
            # regenerates to fit via LoginFrame.on_app_resize instead of
            # being a truly fixed canvas.
            self.resizable(True, True)
            self._size_to_fixed(name)
        elif name in CARD_SIZED_FRAMES:
            self.resizable(True, True)
            self._size_to_content(name)
        elif name in SIZE_TO_FIT_FRAMES:
            self.resizable(True, True)
            self._size_to_frame(name)
        else:
            self.resizable(True, True)
            self._maximize()

    def _update_account_icon(self):
        # Manage Users already has its own "Back to Dashboard" link - the
        # floating account/logout button there was a second, redundant way
        # back (and out), so it's hidden on that screen specifically.
        show_account = self.auth_service.current_user is not None and self._current_frame_name != "admin_panel"

        if show_account:
            self.account_button.pack(side="top", pady=(4, 0), after=self.settings_button)
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
        set_accent(value)

        self._close_settings()
        self._close_account_popup()
        self.topbar.destroy()
        self.topbar_divider.destroy()
        self.container.destroy()
        self._build_ui()
