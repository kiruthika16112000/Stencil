try:
    from serial.tools import list_ports
except ImportError:
    list_ports = None


def list_serial_ports():
    """Available COM/serial ports on this machine. Empty if pyserial isn't
    installed or nothing is currently connected."""
    if list_ports is None:
        return []

    return sorted(port.device for port in list_ports.comports())
