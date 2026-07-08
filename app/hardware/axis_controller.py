import time


class AxisController:
    """Thin wrapper around a single Modbus axis drive (coil/register I/O).

    Ported as-is from the working control app - the pulse timings
    (write True, sleep, write False) match the drive's expected input
    pulse width and should not be changed.
    """

    def __init__(self, client, cfg):
        self.client = client

        self.servo = cfg["servo_on"]
        self.reset = cfg["reset"]
        self.origin_addr = cfg["origin"]

        self.start_addr = cfg["start"]
        self.stop_addr = cfg["stop"]
        self.zero_addr = cfg["zero"]

        self.pos = cfg["pos"]
        self.speed = cfg["speed"]
        self.feedback = cfg["feedback"]

    @property
    def connected(self):
        return self.client is not None

    def servo_on(self):
        if not self.connected:
            return
        print("Servo ON")
        self.client.write_coil(self.servo, True)

    def servo_off(self):
        if not self.connected:
            return
        print("Servo OFF")
        self.client.write_coil(self.servo, False)

    def reset_axis(self):
        if not self.connected:
            return
        print("RESET")
        self.client.write_coil(self.reset, False)
        time.sleep(0.05)
        self.client.write_coil(self.reset, True)
        time.sleep(0.2)
        self.client.write_coil(self.reset, False)

    def origin(self):
        if not self.connected:
            return
        print("ORIGIN")
        self.client.write_coil(self.origin_addr, False)
        time.sleep(0.05)
        self.client.write_coil(self.origin_addr, True)
        time.sleep(0.1)
        self.client.write_coil(self.origin_addr, False)

    def start(self):
        if not self.connected:
            return
        print("START pulse")
        self.client.write_coil(self.start_addr, False)
        time.sleep(0.05)
        self.client.write_coil(self.start_addr, True)
        time.sleep(0.2)
        self.client.write_coil(self.start_addr, False)

    def stop(self):
        if not self.connected:
            return
        print("STOP")
        self.client.write_coil(self.start_addr, False)
        time.sleep(0.05)
        self.client.write_coil(self.stop_addr, True)
        time.sleep(0.1)
        self.client.write_coil(self.stop_addr, False)

    def zero(self):
        if not self.connected:
            return
        print("ZERO pulse")
        self.client.write_coil(self.zero_addr, False)
        time.sleep(0.05)
        self.client.write_coil(self.zero_addr, True)
        time.sleep(0.3)
        self.client.write_coil(self.zero_addr, False)

    def set_position(self, value):
        if not self.connected:
            return
        print("[WRITE] POS =", value)
        self.client.write_register(self.pos, int(value))

    def set_speed(self, value=10000):
        if not self.connected:
            return
        print("[WRITE] SPEED =", value)
        self.client.write_register(self.speed, int(value))

    def get_position(self):
        if not self.connected:
            return 0
        try:
            res = self.client.read_holding_registers(address=self.feedback, count=1)
            if res and not res.isError():
                return res.registers[0]
        except Exception as e:
            print("Read position error:", e)
        return 0
