from tkinter import filedialog

import customtkinter as ctk

from app.models.settings import (
    AdditionalSettings,
    AdminSettings,
    DeviceAddressSettings,
    DutSettings,
    MesServerSettings,
    ReportPathSettings,
    Settings,
)
from app.ui.common import ADAPTIVE_TEXT_COLOR, BaseFrame, HINT_TEXT_COLOR, IPAddressEntry, PasswordEntry, SUCCESS_TEXT_COLOR
from app.ui.ports import list_serial_ports

NO_PORTS_PLACEHOLDER = "No ports found"

SECTION_TITLE_COLOR = ("#1e6eb5", "#4da3e0")


def _section(master, title):
    frame = ctk.CTkFrame(master, border_width=1, corner_radius=10)
    ctk.CTkLabel(
        frame, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=SECTION_TITLE_COLOR, anchor="w"
    ).pack(fill="x", padx=14, pady=(10, 4))
    return frame


def _field_row(master, label_text, value="", is_password=False):
    row = ctk.CTkFrame(master, fg_color="transparent")
    row.pack(fill="x", padx=14, pady=4)

    ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=11), anchor="w", width=150).pack(side="left")

    entry = PasswordEntry(row, width=200) if is_password else ctk.CTkEntry(row, width=200)
    entry.insert(0, value)
    entry.pack(side="left", fill="x", expand=True)
    return entry


def _ip_field_row(master, label_text):
    row = ctk.CTkFrame(master, fg_color="transparent")
    row.pack(fill="x", padx=14, pady=4)

    ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=11), anchor="w", width=150).pack(side="left")

    entry = IPAddressEntry(row, width=200)
    entry.pack(side="left")
    return entry


def _check_row(master, label_text, checked=False):
    var = ctk.BooleanVar(value=checked)
    ctk.CTkCheckBox(master, text=label_text, variable=var).pack(anchor="w", padx=14, pady=3)
    return var


def _spacer(master, height=8):
    ctk.CTkFrame(master, fg_color="transparent", height=height).pack()


def _set_entry(entry, value):
    entry.delete(0, "end")
    entry.insert(0, value)


class SettingsFrame(BaseFrame):
    def __init__(self, master, app):
        super().__init__(master, app)

        self.variant_name = ""

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(10, 4))

        self.variant_label = ctk.CTkLabel(header, text="", font=ctk.CTkFont(size=12), text_color=HINT_TEXT_COLOR)
        self.variant_label.pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="", text_color=SUCCESS_TEXT_COLOR)
        self.status_label.pack(pady=(0, 4))

        body = ctk.CTkScrollableFrame(self, width=760, height=520)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(body, fg_color="transparent")
        left.grid(row=0, column=0, sticky="new", padx=(0, 8))

        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="new", padx=(8, 0))

        self._build_left(left)
        self._build_right(right)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkButton(
            footer,
            text="Cancel",
            fg_color="transparent",
            border_width=1,
            text_color=ADAPTIVE_TEXT_COLOR,
            command=self._cancel,
        ).pack(side="right", padx=(6, 0))
        ctk.CTkButton(footer, text="Save Settings", command=self._save).pack(side="right")

    def _build_left(self, parent):
        additional = _section(parent, "ADDITIONAL SETTINGS")
        additional.pack(fill="x", pady=(0, 10))
        self.chk_usb = _check_row(additional, "USB Scanner")
        self.chk_continue = _check_row(additional, "Continue Test if Failed")
        self.chk_cylinder = _check_row(additional, "Cylinder Down?")
        self.chk_retest = _check_row(additional, "Retest Access to User")
        self.chk_buzzer = _check_row(additional, "Buzzer")
        self.chk_safety = _check_row(additional, "Safety Line Curtain")
        self.chk_record = _check_row(additional, "Record")
        self.chk_master = _check_row(additional, "Master")
        self.f_station_id = _field_row(additional, "Station ID", "30")

        db_row = ctk.CTkFrame(additional, fg_color="transparent")
        db_row.pack(fill="x", padx=14, pady=(4, 10))
        ctk.CTkLabel(db_row, text="Database", font=ctk.CTkFont(size=11), width=150, anchor="w").pack(side="left")
        self.database_var = ctk.StringVar(value="Poka-Yoke")
        ctk.CTkOptionMenu(
            db_row, values=["Poka-Yoke", "Production", "Test"], variable=self.database_var, width=200
        ).pack(side="left")

        report = _section(parent, "REPORT PATH")
        report.pack(fill="x", pady=(0, 10))
        self.f_local_path = self._path_field(report, "Local Path", self._browse_local)
        self.f_server_path = self._path_field(report, "Server Path", self._browse_server)
        self.chk_save_server = _check_row(report, "Save to Server")
        _spacer(report)

        admin = _section(parent, "ADMIN")
        admin.pack(fill="x", pady=(0, 10))
        self.f_admin_password = _field_row(admin, "Password", is_password=True)
        _spacer(admin)

        device = _section(parent, "DEVICE ADDRESS")
        device.pack(fill="x", pady=(0, 10))
        self.f_plc = _ip_field_row(device, "PLC")
        self.f_port = _field_row(device, "Port")
        self.f_camera_ip = _field_row(device, "Camera IP")
        self.light_com_var, self.light_com_menu = self._port_row(device, "Light Port")
        self.f_host_addr = _field_row(device, "Host Address")
        self.f_db_addr = _field_row(device, "Database")
        self.f_username = _field_row(device, "Username")
        self.f_device_password = _field_row(device, "Password", is_password=True)
        _spacer(device)

    def _build_right(self, parent):
        dut = _section(parent, "DUT SETTINGS")
        dut.pack(fill="x", pady=(0, 10))
        self.f_master_ng = _field_row(dut, "Master & NG Sample")
        self.f_verify_sn = _field_row(dut, "Verify Serial Number")
        self.f_barcode_len = _field_row(dut, "Barcode Length", "1")
        self.f_ip_address = _ip_field_row(dut, "IP Address")
        self.f_mes_station_id = _field_row(dut, "MES Station ID")
        self.f_script_path = self._path_field(dut, "Script Path", self._browse_script)
        _spacer(dut)

        mes = _section(parent, "MES SERVER SETTINGS")
        mes.pack(fill="x", pady=(0, 10))
        self.chk_mes_enable = _check_row(mes, "MES Server Enable")
        self.f_mes_status_url = _field_row(mes, "MES Server Status Check")
        self.f_mes_auth_url = _field_row(mes, "User Authentication API")
        self.f_mes_prev_url = _field_row(mes, "Previous Station Check")
        self.f_mes_result_url = _field_row(mes, "Station Result Posting API")
        _spacer(mes)

    def _path_field(self, master, label_text, browse_command):
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=11), width=150, anchor="w").pack(side="left")

        entry = ctk.CTkEntry(row, width=150)
        entry.pack(side="left")

        ctk.CTkButton(row, text="Browse", width=60, command=lambda: browse_command(entry)).pack(
            side="left", padx=(6, 0)
        )
        return entry

    def _port_row(self, master, label_text):
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=11), width=150, anchor="w").pack(side="left")

        var = ctk.StringVar(value=NO_PORTS_PLACEHOLDER)
        menu = ctk.CTkOptionMenu(row, values=[NO_PORTS_PLACEHOLDER], variable=var, width=150)
        menu.pack(side="left")

        ctk.CTkButton(row, text="Scan", width=60, command=lambda: self._refresh_light_com_ports()).pack(
            side="left", padx=(6, 0)
        )
        return var, menu

    def _refresh_light_com_ports(self, keep_value=None):
        keep_value = keep_value if keep_value is not None else self.light_com_var.get()
        ports = list_serial_ports()
        values = ports if ports else [NO_PORTS_PLACEHOLDER]

        # Keep a previously configured port visible/selectable even if it's
        # not currently plugged in, instead of silently discarding it.
        if keep_value and keep_value != NO_PORTS_PLACEHOLDER and keep_value not in values:
            values = [keep_value] + values

        self.light_com_menu.configure(values=values)
        self.light_com_var.set(keep_value if keep_value in values else values[0])

    def _selected_light_com(self):
        value = self.light_com_var.get()
        return "" if value == NO_PORTS_PLACEHOLDER else value

    def _browse_local(self, entry):
        path = filedialog.askdirectory(title="Select Local Report Folder")
        if path:
            _set_entry(entry, path)

    def _browse_server(self, entry):
        path = filedialog.askdirectory(title="Select Server Report Folder")
        if path:
            _set_entry(entry, path)

    def _browse_script(self, entry):
        path = filedialog.askopenfilename(title="Select Script File")
        if path:
            _set_entry(entry, path)

    def on_show(self, variant_name):
        self.variant_name = variant_name
        self.variant_label.configure(text=f"Variant: {variant_name}")
        self.status_label.configure(text="")
        self._populate(self.app.settings_service.load(variant_name))

    def _populate(self, settings):
        a = settings.additional
        self.chk_usb.set(a.usb_scanner)
        self.chk_continue.set(a.continue_on_fail)
        self.chk_cylinder.set(a.cylinder_down)
        self.chk_retest.set(a.retest_access)
        self.chk_buzzer.set(a.buzzer)
        self.chk_safety.set(a.safety_curtain)
        self.chk_record.set(a.record)
        self.chk_master.set(a.master)
        _set_entry(self.f_station_id, a.station_id)
        self.database_var.set(a.database)

        r = settings.report_path
        _set_entry(self.f_local_path, r.local_path)
        _set_entry(self.f_server_path, r.server_path)
        self.chk_save_server.set(r.save_to_server)

        _set_entry(self.f_admin_password, settings.admin.password)

        d = settings.device_address
        _set_entry(self.f_plc, d.plc)
        _set_entry(self.f_port, d.port)
        _set_entry(self.f_camera_ip, d.camera_ip)
        self._refresh_light_com_ports(keep_value=d.light_com)
        _set_entry(self.f_host_addr, d.host_addr)
        _set_entry(self.f_db_addr, d.db_addr)
        _set_entry(self.f_username, d.username)
        _set_entry(self.f_device_password, d.password)

        dut = settings.dut
        _set_entry(self.f_master_ng, dut.master_ng)
        _set_entry(self.f_verify_sn, dut.verify_sn)
        _set_entry(self.f_barcode_len, dut.barcode_len)
        _set_entry(self.f_ip_address, dut.ip_address)
        _set_entry(self.f_mes_station_id, dut.mes_station_id)
        _set_entry(self.f_script_path, dut.script_path)

        m = settings.mes_server
        self.chk_mes_enable.set(m.enabled)
        _set_entry(self.f_mes_status_url, m.status_url)
        _set_entry(self.f_mes_auth_url, m.auth_url)
        _set_entry(self.f_mes_prev_url, m.prev_station_url)
        _set_entry(self.f_mes_result_url, m.result_url)

    def _collect(self):
        additional = AdditionalSettings(
            usb_scanner=self.chk_usb.get(),
            continue_on_fail=self.chk_continue.get(),
            cylinder_down=self.chk_cylinder.get(),
            retest_access=self.chk_retest.get(),
            buzzer=self.chk_buzzer.get(),
            safety_curtain=self.chk_safety.get(),
            record=self.chk_record.get(),
            master=self.chk_master.get(),
            station_id=self.f_station_id.get(),
            database=self.database_var.get(),
        )

        report_path = ReportPathSettings(
            local_path=self.f_local_path.get(),
            server_path=self.f_server_path.get(),
            save_to_server=self.chk_save_server.get(),
        )

        admin = AdminSettings(password=self.f_admin_password.get())

        device_address = DeviceAddressSettings(
            plc=self.f_plc.get(),
            port=self.f_port.get(),
            camera_ip=self.f_camera_ip.get(),
            light_com=self._selected_light_com(),
            host_addr=self.f_host_addr.get(),
            db_addr=self.f_db_addr.get(),
            username=self.f_username.get(),
            password=self.f_device_password.get(),
        )

        dut = DutSettings(
            master_ng=self.f_master_ng.get(),
            verify_sn=self.f_verify_sn.get(),
            barcode_len=self.f_barcode_len.get(),
            ip_address=self.f_ip_address.get(),
            mes_station_id=self.f_mes_station_id.get(),
            script_path=self.f_script_path.get(),
        )

        mes_server = MesServerSettings(
            enabled=self.chk_mes_enable.get(),
            status_url=self.f_mes_status_url.get(),
            auth_url=self.f_mes_auth_url.get(),
            prev_station_url=self.f_mes_prev_url.get(),
            result_url=self.f_mes_result_url.get(),
        )

        return Settings(self.variant_name, additional, report_path, admin, device_address, dut, mes_server)

    def _save(self):
        self.app.settings_service.update(self._collect())
        self.app.settings_service.save()
        self.status_label.configure(text="Settings saved.", text_color=SUCCESS_TEXT_COLOR)

    def _cancel(self):
        self.app.show_frame("variant_selection")
