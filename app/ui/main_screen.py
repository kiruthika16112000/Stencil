import os
from datetime import datetime

import customtkinter as ctk
from PIL import Image

from app.ui.common import (
    BaseFrame,
    CARD_BORDER_COLOR,
    ERROR_TEXT_COLOR,
    HINT_TEXT_COLOR,
    SUCCESS_TEXT_COLOR,
    primary_button,
)

# Jog step and travel limits for the arrow-key/arrow-button jog controls.
# Ported as-is from the working control app.
STEP = 200
MIN_POS = 0
MAX_POS = 48000

# Default/fallback camera box size, used only before the first resolution
# based sizing pass runs. Actual size is computed in _resize_camera_area().
CAM_WIDTH = 480
CAM_HEIGHT = 270

# height / width, taken from the original camera's working resolution
# (1850 x 750) so the feed doesn't get visually stretched.
CAM_ASPECT_RATIO = 750 / 1850

SAVE_DIR = "saved_images"

POSITION_COLOR = ("#1f6aa5", "#3b8ed0")


class MainFrame(BaseFrame):
    """Live camera feed + X/Y actuator jog controls. Bypasses self.content
    (like SettingsFrame) since this is a dense, full-page layout."""

    def __init__(self, master, app):
        super().__init__(master, app)

        self.variant_name = ""
        self.system_started = False
        self.current_frame = None
        self._frame_job = None
        self._position_job = None
        self._cam_width = CAM_WIDTH
        self._cam_height = CAM_HEIGHT

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(10, 4))
        self.variant_label = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(size=16, weight="bold"), text_color=HINT_TEXT_COLOR
        )
        self.variant_label.pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="Press START to begin", text_color=HINT_TEXT_COLOR)
        self.status_label.pack(pady=(0, 6))

        # The camera box is the *only* widget below that expands/fills - so
        # the header/status/position/button rows always get their natural
        # size first, and the preview just takes whatever space is left.
        # This guarantees the buttons stay visible regardless of monitor
        # resolution or DPI scaling, instead of relying on a pre-computed
        # size budget.
        self.camera_area = ctk.CTkFrame(
            self, fg_color=("gray85", "gray17"), corner_radius=14, border_width=1, border_color=CARD_BORDER_COLOR
        )
        self.camera_area.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        self.feed_label = ctk.CTkLabel(self.camera_area, text="Press START to begin", text_color=HINT_TEXT_COLOR)
        self.feed_label.place(relx=0.5, rely=0.5, anchor="center")

        arrow_pad = ctk.CTkFrame(self.camera_area, fg_color="transparent", corner_radius=12)
        arrow_pad.place(relx=0.0, rely=1.0, x=12, y=-12, anchor="sw")

        ctk.CTkButton(arrow_pad, text="▲", width=36, height=30, command=lambda: self._move_y(-STEP)).grid(
            row=0, column=1, padx=2, pady=2
        )
        ctk.CTkButton(arrow_pad, text="◀", width=36, height=30, command=lambda: self._move_x(-STEP)).grid(
            row=1, column=0, padx=2, pady=2
        )
        ctk.CTkButton(arrow_pad, text="▶", width=36, height=30, command=lambda: self._move_x(STEP)).grid(
            row=1, column=2, padx=2, pady=2
        )
        ctk.CTkButton(arrow_pad, text="▼", width=36, height=30, command=lambda: self._move_y(STEP)).grid(
            row=2, column=1, padx=2, pady=2
        )

        position_row = ctk.CTkFrame(self, fg_color="transparent")
        position_row.pack(pady=(0, 10))
        self.x_position_label = ctk.CTkLabel(
            position_row, text="X: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color=POSITION_COLOR
        )
        self.x_position_label.pack(side="left", padx=12)
        self.y_position_label = ctk.CTkLabel(
            position_row, text="Y: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color=POSITION_COLOR
        )
        self.y_position_label.pack(side="left", padx=12)

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=(0, 16))
        self.start_button = primary_button(button_row, "START", self._start_system, width=100)
        self.start_button.pack(side="left", padx=6)
        ctk.CTkButton(
            button_row, text="SAVE", width=100, fg_color="#2e7d32", hover_color="#1b5e20", command=self._save_image
        ).pack(side="left", padx=6)

        # Bound once on the app window itself (present in every widget's
        # bindtags), guarded by _is_active()/system_started, rather than
        # relying on button focus policy the way the original Qt app did.
        self.app.bind("<Left>", lambda _event: self._move_x(-STEP))
        self.app.bind("<Right>", lambda _event: self._move_x(STEP))
        self.app.bind("<Up>", lambda _event: self._move_y(-STEP))
        self.app.bind("<Down>", lambda _event: self._move_y(STEP))

    def on_show(self, variant_name=None):
        self.variant_name = variant_name or ""
        self.variant_label.configure(text=f"Variant: {self.variant_name}" if self.variant_name else "")

        # The app window has just been (or is about to be) maximized to the
        # monitor's resolution for this screen - defer so the camera_area's
        # real, laid-out size is available before fitting the feed to it.
        self.after(120, self._resize_camera_area)

    def on_app_resize(self):
        """Called by App whenever the window is resized while this screen
        is active, so the camera feed keeps tracking the available space."""
        self._resize_camera_area()

    def _is_active(self):
        return self.app._current_frame_name == "home"

    def _resize_camera_area(self):
        # camera_area is the only widget that fills/expands (see __init__),
        # so its actual laid-out size already accounts for every other row
        # on the screen - no separate budget/estimate needed. Just fit the
        # feed's aspect ratio inside whatever box it was actually given.
        self.camera_area.update_idletasks()
        box_width = self.camera_area.winfo_width()
        box_height = self.camera_area.winfo_height()

        if box_width <= 1 or box_height <= 1:
            return

        width = box_width
        height = int(width * CAM_ASPECT_RATIO)
        if height > box_height:
            height = box_height
            width = int(height / CAM_ASPECT_RATIO)

        width = max(160, width)
        height = max(120, height)

        if (width, height) == (self._cam_width, self._cam_height):
            return

        # This only sizes the rendered video image (letterboxed, centered
        # via feed_label's place()) - camera_area's own box size is left to
        # the pack fill/expand layout above, not set here.
        self._cam_width, self._cam_height = width, height

    # ---- movement (exact port of auto_screen.py move_x/move_y) ----
    def _move_x(self, delta):
        if not self._is_active() or not self.system_started:
            return

        service = self.app.actuator_service
        status = service.get_x_status()
        if status and (status["busy"] or not status["inp"]):
            print("X still moving")
            return

        cur = service.get_x_position()
        target = cur + delta
        if target < MIN_POS or target > MAX_POS:
            return

        service.x.set_position(target)
        service.x.set_speed(10000)
        service.x.start()

    def _move_y(self, delta):
        if not self._is_active() or not self.system_started:
            return

        service = self.app.actuator_service
        status = service.get_y_status()
        if status and (status["busy"] or not status["inp"]):
            print("Y still moving")
            return

        cur = service.get_y_position()
        target = cur + delta
        if target < MIN_POS or target > MAX_POS:
            return

        service.y.set_position(target)
        service.y.set_speed(10000)
        service.y.start()

    # ---- start/stop ----
    def _start_system(self):
        if self.system_started:
            return

        service = self.app.actuator_service
        service.toggle_servo_x(True)
        service.toggle_servo_y(True)

        if self.app.camera.open():
            self.feed_label.configure(text="")
        else:
            self.feed_label.configure(text="Camera not available")

        self.system_started = True
        self.start_button.configure(text="Running", state="disabled")
        self.status_label.configure(text="Running", text_color=SUCCESS_TEXT_COLOR)

        self._update_frame()
        self._update_position()

    def _update_frame(self):
        if not self.system_started:
            return

        frame = self.app.camera.grab_frame()
        if frame is not None:
            self.current_frame = frame
            image = Image.fromarray(frame[:, :, ::-1])  # BGR -> RGB
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(self._cam_width, self._cam_height))
            self.feed_label.configure(image=ctk_image, text="")

        self._frame_job = self.after(30, self._update_frame)

    def _update_position(self):
        if not self.system_started:
            return

        service = self.app.actuator_service
        self.x_position_label.configure(text=f"X: {service.get_x_position()}")
        self.y_position_label.configure(text=f"Y: {service.get_y_position()}")

        self._position_job = self.after(100, self._update_position)

    def _save_image(self):
        if self.current_frame is None:
            self.status_label.configure(text="No frame to save yet.", text_color=ERROR_TEXT_COLOR)
            return

        os.makedirs(SAVE_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SAVE_DIR, f"capture_{timestamp}.png")
        Image.fromarray(self.current_frame[:, :, ::-1]).save(path)
        self.status_label.configure(text=f"Saved {path}", text_color=SUCCESS_TEXT_COLOR)

    def shutdown(self):
        """Called on app close: stop polling loops and release the camera."""
        if self._frame_job is not None:
            self.after_cancel(self._frame_job)
            self._frame_job = None

        if self._position_job is not None:
            self.after_cancel(self._position_job)
            self._position_job = None

        self.app.camera.close()
