import customtkinter as ctk

from app.hardware.registers import (
    CRITICAL_DI_NAMES,
    DI_PORT_0,
    DI_PORT_1,
    DI_PORT_2,
    DO_PORT_0,
    DO_PORT_1,
    DO_X_AXIS,
    DO_Y_AXIS,
)
from app.ui.common import (
    ADAPTIVE_TEXT_COLOR,
    BaseFrame,
    CARD_BORDER_COLOR,
    ERROR_TEXT_COLOR,
    HINT_TEXT_COLOR,
    primary_button,
    secondary_button,
)

DI_COLUMNS = [
    ("DI PORT 0", DI_PORT_0),
    ("DI PORT 1", DI_PORT_1),
    ("DI PORT 2", DI_PORT_2),
]

DO_COLUMNS = [
    ("DO PORT 0", DO_PORT_0),
    ("DO PORT 1", DO_PORT_1),
    ("X Axis", DO_X_AXIS),
    ("Y Axis", DO_Y_AXIS),
]

# Section header colors - one accent per section type, so the seven
# columns plus the two bottom panels are easy to tell apart at a glance.
# ACTUATOR uses the app's primary indigo/violet accent to mark it as the
# main action panel; DO/DI/LIGHT stay in their own distinct hues.
DO_HEADER_COLOR = "#c9862f"
DI_HEADER_COLOR = "#2f9e6f"
ACTUATOR_HEADER_COLOR = "#5B4FE0"
LIGHT_HEADER_COLOR = "#8e44ad"
HEADER_TEXT_COLOR = "white"

DI_ON_COLOR = ("#e6f7ee", "#1f9d55")
DI_OFF_COLOR = ("#fdecea", "#d9534f")
DI_ON_CRITICAL = ("#d1fae5", "#047857")
DI_OFF_CRITICAL = ("#fee2e2", "#991b1b")
DO_ON_COLOR = ("#1f9d55", "#1f9d55")
DO_OFF_COLOR = ("gray80", "gray30")


class ActuatorDebugFrame(BaseFrame):
    """Raw Modbus I/O diagnostics: every DO coil / DI discrete-input on the
    machine, plus the same X/Y "set position+speed" convenience the Main
    screen uses. Bypasses self.content since this is a dense, full-page
    layout (like SettingsFrame) that maximizes to the monitor resolution."""

    def __init__(self, master, app):
        super().__init__(master, app)

        self._update_job = None
        self._do_state = {}
        self._do_widgets = {}
        self._di_rows = {}

        secondary_button(self, "< Back", self._back, width=80).pack(anchor="w", padx=12, pady=(10, 6))

        io_row = ctk.CTkFrame(self, fg_color="transparent")
        io_row.pack(fill="x", padx=10)

        for title, items in DO_COLUMNS:
            self._build_do_column(io_row, title, items)

        for title, items in DI_COLUMNS:
            base_address = items[0][0]
            self._di_rows[base_address] = self._build_di_column(io_row, title, items)

        bottom_row = ctk.CTkFrame(self, fg_color="transparent")
        bottom_row.pack(fill="x", padx=10, pady=10)

        self._build_actuator_section(bottom_row)
        self._build_light_control_section(bottom_row)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=14, pady=(0, 10))

        self.status_label = ctk.CTkLabel(footer, text="Ready", text_color=HINT_TEXT_COLOR, anchor="w")
        self.status_label.pack(side="left")

    # ---- column builders ----
    def _build_column_frame(self, master, title, header_color):
        col = ctk.CTkFrame(master, border_width=1, border_color=CARD_BORDER_COLOR, corner_radius=10)
        col.pack(side="left", fill="both", expand=True, padx=4)

        header = ctk.CTkFrame(col, fg_color=header_color, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=HEADER_TEXT_COLOR
        ).pack(pady=6)

        return col

    def _build_do_column(self, master, title, items):
        col = self._build_column_frame(master, title, DO_HEADER_COLOR)

        for address, label in items:
            row = ctk.CTkFrame(col, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=3)

            button = ctk.CTkButton(
                row,
                text=f"OFF {label}",
                anchor="w",
                fg_color=DO_OFF_COLOR,
                hover_color=("gray70", "gray35"),
                text_color=ADAPTIVE_TEXT_COLOR,
                command=lambda addr=address, name=label: self._toggle_do(addr, name),
            )
            button.pack(fill="x")

            self._do_state[address] = False
            self._do_widgets[address] = (label, button)

        return col

    def _build_di_column(self, master, title, items):
        col = self._build_column_frame(master, title, DI_HEADER_COLOR)
        rows = []

        for address, label in items:
            row = ctk.CTkFrame(col, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=3)

            widget = ctk.CTkLabel(row, text=label, anchor="w", corner_radius=4)
            widget.pack(fill="x")

            rows.append((address, label, widget))

        return rows

    def _build_actuator_section(self, master):
        section = ctk.CTkFrame(master, border_width=1, border_color=CARD_BORDER_COLOR, corner_radius=10)
        section.pack(side="left", fill="both", expand=True, padx=(0, 6))

        header = ctk.CTkFrame(section, fg_color=ACTUATOR_HEADER_COLOR)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="ACTUATOR", font=ctk.CTkFont(size=13, weight="bold"), text_color=HEADER_TEXT_COLOR
        ).pack(pady=6)

        axes_row = ctk.CTkFrame(section, fg_color="transparent")
        axes_row.pack(fill="both", expand=True, padx=10, pady=10)

        self.x_pos_entry, self.x_speed_entry, self.lbl_feedback_x = self._build_actuator_axis(
            axes_row, "X Axis", "x"
        )
        self.y_pos_entry, self.y_speed_entry, self.lbl_feedback_y = self._build_actuator_axis(
            axes_row, "Y Axis", "y"
        )

    def _build_actuator_axis(self, master, title, axis):
        box = ctk.CTkFrame(master, fg_color="transparent")
        box.pack(side="left", fill="both", expand=True, padx=6)

        ctk.CTkLabel(box, text=title, font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(0, 4))

        fields_row = ctk.CTkFrame(box, fg_color="transparent")
        fields_row.pack(fill="x")

        pos_col = ctk.CTkFrame(fields_row, fg_color="transparent")
        pos_col.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(pos_col, text="Position", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x")
        pos_entry = ctk.CTkEntry(pos_col)
        pos_entry.insert(0, "0")
        pos_entry.pack(fill="x")

        speed_col = ctk.CTkFrame(fields_row, fg_color="transparent")
        speed_col.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(speed_col, text="Speed", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x")
        speed_entry = ctk.CTkEntry(speed_col)
        speed_entry.insert(0, "10000")
        speed_entry.pack(fill="x")

        primary_button(box, f"Set {title}", lambda: self._set_axis(axis), width=140).pack(fill="x", pady=(8, 4))

        feedback = ctk.CTkLabel(box, text=f"{title}: 0", font=ctk.CTkFont(size=13, weight="bold"))
        feedback.pack(pady=(0, 4))

        return pos_entry, speed_entry, feedback

    def _build_light_control_section(self, master):
        section = ctk.CTkFrame(master, border_width=1, border_color=CARD_BORDER_COLOR, corner_radius=10, width=220)
        section.pack(side="left", fill="y", padx=(6, 0))
        section.pack_propagate(False)

        header = ctk.CTkFrame(section, fg_color=LIGHT_HEADER_COLOR)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="LIGHT CONTROL", font=ctk.CTkFont(size=13, weight="bold"), text_color=HEADER_TEXT_COLOR
        ).pack(pady=6)

        body = ctk.CTkFrame(section, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(body, text="Channel", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x")
        self.light_channel_entry = ctk.CTkEntry(body)
        self.light_channel_entry.insert(0, "CH 1")
        self.light_channel_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(body, text="Brightness", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x")
        self.light_brightness_entry = ctk.CTkEntry(body)
        self.light_brightness_entry.insert(0, "0")
        self.light_brightness_entry.pack(fill="x", pady=(0, 8))

        primary_button(body, "Set Brightness", self._set_brightness, width=140).pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            body, text="Live Video", fg_color="#2e7d32", hover_color="#1b5e20", command=self._toggle_live_video
        ).pack(fill="x")

    # ---- lifecycle ----
    def on_show(self):
        self._set_status("Ready")
        self._update_ui()

    def _back(self):
        self._stop_updates()
        self.app.show_frame("variant_selection")

    def _stop_updates(self):
        if self._update_job is not None:
            self.after_cancel(self._update_job)
            self._update_job = None

    def _service(self):
        return self.app.actuator_service

    def _client(self):
        service = self._service()
        return service.x.client if service.x.connected else None

    def _set_status(self, text, is_error=False):
        self.status_label.configure(text=text, text_color=ERROR_TEXT_COLOR if is_error else HINT_TEXT_COLOR)

    # ---- raw DO coil toggles ----
    def _toggle_do(self, address, name):
        client = self._client()
        if client is None:
            self._set_status("No Modbus connection.", is_error=True)
            return

        new_state = not self._do_state.get(address, False)
        try:
            client.write_coil(address, new_state)
        except Exception as error:
            self._set_status(f"Write failed ({name}): {error}", is_error=True)
            return

        self._do_state[address] = new_state
        label, button = self._do_widgets[address]
        button.configure(
            text=f"{'ON' if new_state else 'OFF'} {label}",
            fg_color=DO_ON_COLOR if new_state else DO_OFF_COLOR,
            text_color="white" if new_state else ADAPTIVE_TEXT_COLOR,
        )

    # ---- ACTUATOR set position/speed ----
    def _set_axis(self, axis):
        pos_entry = self.x_pos_entry if axis == "x" else self.y_pos_entry
        speed_entry = self.x_speed_entry if axis == "x" else self.y_speed_entry

        try:
            pos = int(pos_entry.get())
            speed = int(speed_entry.get())
        except ValueError:
            self._set_status("Invalid position/speed value.", is_error=True)
            return

        self._set_status("Ready")
        service = self._service()
        axis_controller = service.x if axis == "x" else service.y

        (service.move_x if axis == "x" else service.move_y)(pos)
        axis_controller.set_speed(speed)

    # ---- Light Control (not wired up yet - addresses TBD) ----
    def _set_brightness(self):
        self._set_status("Light control isn't wired up yet - addresses TBD.")

    def _toggle_live_video(self):
        self._set_status("Light control isn't wired up yet - addresses TBD.")

    # ---- polling ----
    def _update_ui(self):
        for base_address, rows in self._di_rows.items():
            self._read_di_port(base_address, rows)

        service = self._service()
        x_position = service.get_x_position()
        y_position = service.get_y_position()

        self.lbl_feedback_x.configure(text=f"X Axis: {x_position}")
        self.lbl_feedback_y.configure(text=f"Y Axis: {y_position}")

        self._update_job = self.after(300, self._update_ui)

    def _read_di_port(self, base_address, rows):
        client = self._client()
        if client is None:
            return

        try:
            result = client.read_discrete_inputs(address=base_address, count=8)
            if result and not result.isError():
                for (_address, label, widget), state in zip(rows, result.bits):
                    critical = label in CRITICAL_DI_NAMES
                    if critical:
                        bg, color = DI_ON_CRITICAL if state else DI_OFF_CRITICAL
                    else:
                        bg, color = DI_ON_COLOR if state else DI_OFF_COLOR

                    widget.configure(fg_color=bg, text_color=color)
        except Exception as error:
            print(f"DI read error @ {base_address}:", error)
