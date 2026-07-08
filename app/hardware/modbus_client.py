from pymodbus.client import ModbusTcpClient

IP = "192.168.1.7"
PORT = 502


def create_client(ip=IP, port=PORT):
    """Connects to the Modbus TCP server for the actuator drives.

    Returns None instead of raising if the drive isn't reachable, so the
    rest of the app can still launch without the hardware connected -
    AxisController.connected then reports False and every hardware call
    becomes a safe no-op.
    """
    client = ModbusTcpClient(ip, port=port)

    if not client.connect():
        print(f"Cannot connect to Modbus server ({ip}:{port})")
        return None

    print("Modbus Connected")
    return client
