def _from_dict(cls, data):
    """Build cls from a dict, ignoring any keys that aren't (or are no
    longer) accepted parameters - keeps old saved JSON loadable across
    field additions/removals."""
    valid_keys = cls.__init__.__code__.co_varnames[1 : cls.__init__.__code__.co_argcount]
    return cls(**{key: value for key, value in data.items() if key in valid_keys})


class AdditionalSettings:
    def __init__(
        self,
        usb_scanner=False,
        continue_on_fail=False,
        cylinder_down=False,
        retest_access=False,
        buzzer=False,
        safety_curtain=False,
        record=False,
        master=False,
        station_id="30",
        database="Poka-Yoke",
    ):
        self.usb_scanner = usb_scanner
        self.continue_on_fail = continue_on_fail
        self.cylinder_down = cylinder_down
        self.retest_access = retest_access
        self.buzzer = buzzer
        self.safety_curtain = safety_curtain
        self.record = record
        self.master = master
        self.station_id = station_id
        self.database = database

    def to_dict(self):
        return dict(vars(self))

    @classmethod
    def from_dict(cls, data):
        return _from_dict(cls, data)


class ReportPathSettings:
    def __init__(self, local_path="", server_path="", save_to_server=False):
        self.local_path = local_path
        self.server_path = server_path
        self.save_to_server = save_to_server

    def to_dict(self):
        return dict(vars(self))

    @classmethod
    def from_dict(cls, data):
        return _from_dict(cls, data)


class AdminSettings:
    def __init__(self, password=""):
        self.password = password

    def to_dict(self):
        return dict(vars(self))

    @classmethod
    def from_dict(cls, data):
        return _from_dict(cls, data)


class DeviceAddressSettings:
    def __init__(self, plc="", port="", camera_ip="", light_com="", host_addr="", db_addr="", username="", password=""):
        self.plc = plc
        self.port = port
        self.camera_ip = camera_ip
        self.light_com = light_com
        self.host_addr = host_addr
        self.db_addr = db_addr
        self.username = username
        self.password = password

    def to_dict(self):
        return dict(vars(self))

    @classmethod
    def from_dict(cls, data):
        return _from_dict(cls, data)


class DutSettings:
    def __init__(
        self,
        master_ng="",
        verify_sn="",
        barcode_len="1",
        ip_address="",
        mes_station_id="",
        script_path="",
    ):
        self.master_ng = master_ng
        self.verify_sn = verify_sn
        self.barcode_len = barcode_len
        self.ip_address = ip_address
        self.mes_station_id = mes_station_id
        self.script_path = script_path

    def to_dict(self):
        return dict(vars(self))

    @classmethod
    def from_dict(cls, data):
        return _from_dict(cls, data)


class MesServerSettings:
    def __init__(self, enabled=False, status_url="", auth_url="", prev_station_url="", result_url=""):
        self.enabled = enabled
        self.status_url = status_url
        self.auth_url = auth_url
        self.prev_station_url = prev_station_url
        self.result_url = result_url

    def to_dict(self):
        return dict(vars(self))

    @classmethod
    def from_dict(cls, data):
        return _from_dict(cls, data)


class Settings:
    """All configuration for a single variant, grouped the same way the
    settings screen presents them."""

    def __init__(
        self,
        variant_name,
        additional=None,
        report_path=None,
        admin=None,
        device_address=None,
        dut=None,
        mes_server=None,
    ):
        self.variant_name = variant_name
        self.additional = additional or AdditionalSettings()
        self.report_path = report_path or ReportPathSettings()
        self.admin = admin or AdminSettings()
        self.device_address = device_address or DeviceAddressSettings()
        self.dut = dut or DutSettings()
        self.mes_server = mes_server or MesServerSettings()

    def to_dict(self):
        return {
            "variant_name": self.variant_name,
            "additional": self.additional.to_dict(),
            "report_path": self.report_path.to_dict(),
            "admin": self.admin.to_dict(),
            "device_address": self.device_address.to_dict(),
            "dut": self.dut.to_dict(),
            "mes_server": self.mes_server.to_dict(),
        }

    @classmethod
    def from_dict(cls, variant_name, data):
        return cls(
            variant_name,
            AdditionalSettings.from_dict(data.get("additional", {})),
            ReportPathSettings.from_dict(data.get("report_path", {})),
            AdminSettings.from_dict(data.get("admin", {})),
            DeviceAddressSettings.from_dict(data.get("device_address", {})),
            DutSettings.from_dict(data.get("dut", {})),
            MesServerSettings.from_dict(data.get("mes_server", {})),
        )
