from tkinter import messagebox

import customtkinter as ctk

from app.services.variant_service import VariantError
from app.ui.icons import gear_icon
from app.ui.common import (
    BaseFrame,
    CARD_BORDER_COLOR,
    ERROR_TEXT_COLOR,
    HINT_TEXT_COLOR,
    SUCCESS_TEXT_COLOR,
    link_button,
    primary_button,
    secondary_button,
    styled_option_menu,
)

NO_VARIANTS_PLACEHOLDER = "No variants yet"


class VariantSelectionFrame(BaseFrame):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = self.content

        ctk.CTkLabel(c, text="Select Variant", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 2))
        ctk.CTkLabel(
            c,
            text="Choose an existing variant to continue,\nor manage the variant list below.",
            font=ctk.CTkFont(size=12),
            text_color=HINT_TEXT_COLOR,
            width=260,
            justify="center",
        ).pack(pady=(0, 20))

        ctk.CTkLabel(c, text="Variant", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        self.variant_var = ctk.StringVar(value=NO_VARIANTS_PLACEHOLDER)
        self.variant_menu = styled_option_menu(
            c,
            values=[NO_VARIANTS_PLACEHOLDER],
            variable=self.variant_var,
            width=260,
            height=36,
            command=self._on_variant_change,
        )
        self.variant_menu.pack(pady=(4, 10))

        self.status_label = ctk.CTkLabel(c, text="", text_color=ERROR_TEXT_COLOR)
        self.status_label.pack(pady=(0, 8))

        primary_button(c, "Continue  →", self._continue, height=40).pack(pady=(8, 8))
        secondary_button(c, "\U0001F5C2  Manage Variants", self._manage_variants).pack(pady=4)

        divider_row = ctk.CTkFrame(c, fg_color="transparent")
        divider_row.pack(fill="x", pady=(16, 10))
        ctk.CTkFrame(divider_row, fg_color=CARD_BORDER_COLOR, height=1).pack(fill="x")

        # Settings and Diagnostics jump to their own big, full-page screens
        # (not the compact card flow above) - grouped side by side below a
        # divider to set them apart from the Continue/Manage Variants pair.
        big_screen_row = ctk.CTkFrame(c, fg_color="transparent")
        big_screen_row.pack()

        self.settings_button = secondary_button(
            big_screen_row, "  Settings", self._open_settings, width=125, image=gear_icon(size=18)
        )
        self.settings_button.configure(state="disabled")
        self.settings_button.pack(side="left", padx=(0, 5))
        secondary_button(big_screen_row, "\U0001F527  Diagnostics", self._open_diagnostics, width=125).pack(
            side="left", padx=(5, 0)
        )

    def on_show(self):
        self.status_label.configure(text="")
        names = [variant.name for variant in self.app.variant_service.list_variants()]

        if names:
            self.variant_menu.configure(values=names)
            if self.variant_var.get() not in names:
                self.variant_var.set(names[0])
        else:
            self.variant_menu.configure(values=[NO_VARIANTS_PLACEHOLDER])
            self.variant_var.set(NO_VARIANTS_PLACEHOLDER)

        self._on_variant_change()

    def _on_variant_change(self, _selected=None):
        has_real_variant = self.variant_var.get() != NO_VARIANTS_PLACEHOLDER
        self.settings_button.configure(state="normal" if has_real_variant else "disabled")

    def _continue(self):
        names = [variant.name for variant in self.app.variant_service.list_variants()]

        if not names:
            self.status_label.configure(text="Add a variant first using Manage Variants.")
            return

        self.app.show_frame("home", variant_name=self.variant_var.get())

    def _open_settings(self):
        self.app.show_frame("settings", variant_name=self.variant_var.get())

    def _manage_variants(self):
        self.app.show_frame("manage_variant")

    def _open_diagnostics(self):
        self.app.show_frame("debug")


class ManageVariantFrame(BaseFrame):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = self.content

        ctk.CTkLabel(c, text="Manage Variants", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 2))
        ctk.CTkLabel(
            c,
            text="Add, edit, or remove variants below,\nthen Save to write them to disk.",
            font=ctk.CTkFont(size=12),
            text_color=HINT_TEXT_COLOR,
            width=260,
            justify="center",
        ).pack(pady=(0, 18))

        ctk.CTkLabel(c, text="Model", font=ctk.CTkFont(size=12), anchor="w", width=260).pack()
        input_row = ctk.CTkFrame(c, fg_color="transparent")
        input_row.pack(pady=(4, 8))

        self.model_entry = ctk.CTkEntry(input_row, placeholder_text="Type variant name here", width=194, height=36)
        self.model_entry.pack(side="left")
        self.model_entry.bind("<Return>", lambda _event: self._add())

        primary_button(input_row, "Add", self._add, width=60, height=36).pack(side="left", padx=(6, 0))

        self.status_label = ctk.CTkLabel(c, text="", text_color=ERROR_TEXT_COLOR)
        self.status_label.pack(pady=(0, 8))

        self.list_frame = ctk.CTkScrollableFrame(c, width=300, height=280)
        self.list_frame.pack(pady=(0, 12))

        primary_button(c, "Save", self._save, height=40).pack(pady=(4, 4))
        link_button(c, "Back to Variant Selection", self._back).pack(pady=4)

    def on_show(self):
        self.status_label.configure(text="")
        self.model_entry.delete(0, "end")
        self._refresh()

    def _refresh(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for variant in self.app.variant_service.list_variants():
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=4)

            ctk.CTkLabel(row, text=variant.name, anchor="w").pack(side="left", fill="x", expand=True)

            ctk.CTkButton(
                row,
                text="Delete",
                width=60,
                fg_color="darkred",
                hover_color="#8b0000",
                command=lambda name=variant.name: self._delete(name),
            ).pack(side="right")

            ctk.CTkButton(
                row,
                text="Edit",
                width=50,
                command=lambda name=variant.name: self._edit(name),
            ).pack(side="right", padx=(0, 4))

    def _add(self):
        name = self.model_entry.get()

        try:
            self.app.variant_service.add(name)
        except VariantError as error:
            self.status_label.configure(text=str(error), text_color=ERROR_TEXT_COLOR)
            return

        self.status_label.configure(text="")
        self.model_entry.delete(0, "end")
        self._refresh()

    def _edit(self, name):
        RenameVariantDialog(self.app, self, name)

    def _delete(self, name):
        if not messagebox.askyesno("Delete Variant", f"Delete '{name}'?"):
            return

        self.app.variant_service.delete(name)
        self._refresh()

    def _save(self):
        self.app.variant_service.save()
        self.status_label.configure(text="Saved.", text_color=SUCCESS_TEXT_COLOR)

    def _back(self):
        self.app.show_frame("variant_selection")


class RenameVariantDialog(ctk.CTkToplevel):
    def __init__(self, app, frame, old_name):
        super().__init__(app)

        self.app = app
        self.frame = frame
        self.old_name = old_name

        self.title("Edit Variant")
        self.geometry("300x170")
        self.resizable(False, False)
        self.transient(app)
        self.grab_set()

        ctk.CTkLabel(self, text="Variant name", font=ctk.CTkFont(size=12)).pack(pady=(16, 4), padx=20, anchor="w")

        self.entry = ctk.CTkEntry(self, width=260)
        self.entry.insert(0, old_name)
        self.entry.pack(padx=20)
        self.entry.bind("<Return>", lambda _event: self._save())
        self.entry.focus_set()

        self.status_label = ctk.CTkLabel(self, text="", text_color=ERROR_TEXT_COLOR)
        self.status_label.pack(pady=(4, 0))

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=12)

        primary_button(button_row, "Save", self._save, width=100).pack(side="left", padx=6)
        secondary_button(button_row, "Cancel", self.destroy, width=100).pack(side="left", padx=6)

    def _save(self):
        new_name = self.entry.get()

        try:
            self.app.variant_service.rename(self.old_name, new_name)
        except VariantError as error:
            self.status_label.configure(text=str(error))
            return

        self.destroy()
        self.frame._refresh()
