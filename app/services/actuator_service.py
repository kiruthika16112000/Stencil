import time

from app.hardware.registers import X_STATUS_ADDRESS, Y_STATUS_ADDRESS
from app.services.safety import is_axis_ready


class ActuatorService:
    """Business logic wrapping the X/Y AxisController pair: servo control,
    guarded start (checks safety + busy status), and status/position
    polling. Ported as-is from the working control app."""

    def __init__(self, x_axis, y_axis):
        self.x = x_axis
        self.y = y_axis

        self.DEFAULT_SPEED = 2000

        self.x_target_set = False
        self.y_target_set = False

    # ---- servo ----
    def toggle_servo_x(self, state):
        if state:
            print("X Servo ON")
            self.x.servo_on()
        else:
            print("X Servo OFF")
            self.x.servo_off()

    def toggle_servo_y(self, state):
        if state:
            print("Y Servo ON")
            self.y.servo_on()
        else:
            print("Y Servo OFF")
            self.y.servo_off()

    # ---- basic pulses ----
    def origin_x(self):
        print("X ORIGIN")
        self.x.origin()

    def origin_y(self):
        print("Y ORIGIN")
        self.y.origin()

    def reset_x(self):
        print("X RESET")
        self.x.reset_axis()

    def reset_y(self):
        print("Y RESET")
        self.y.reset_axis()

    def zero_x(self):
        print("X ZERO")
        self.x.zero()

    def zero_y(self):
        print("Y ZERO")
        self.y.zero()

    # ---- guarded start ----
    def start_x(self):
        print(">>> START_X CALLED")

        status = self.get_x_status()
        if not status:
            print("X status not available")
            return

        print("X DI:", status)

        if not self.x_target_set:
            print("X start ignored (no position set)")
            return

        if not is_axis_ready(status):
            print("X NOT READY")
            return

        if status["busy"]:
            print("X is already moving (BUSY)")
            return

        print("Starting X")
        self.x.set_speed(self.DEFAULT_SPEED)
        time.sleep(0.05)
        self.x.start()

    def start_y(self):
        print(">>> START_Y CALLED")

        status = self.get_y_status()
        if not status:
            print("Y status not available")
            return

        print("Y DI:", status)

        if not self.y_target_set:
            print("Y start ignored (no position set)")
            return

        if not is_axis_ready(status):
            print("Y NOT READY")
            return

        if status["busy"]:
            print("Y is already moving (BUSY)")
            return

        print("Starting Y")
        self.y.set_speed(self.DEFAULT_SPEED)
        time.sleep(0.05)
        self.y.start()

    # ---- stop ----
    def stop_x(self):
        print("STOP X")
        self.x.stop()

    def stop_y(self):
        print("STOP Y")
        self.y.stop()

    # ---- set target position ----
    def move_x(self, pos):
        print(f"Set X Position -> {pos}")
        self.x.set_position(pos)
        self.x_target_set = True

    def move_y(self, pos):
        print(f"Set Y Position -> {pos}")
        self.y.set_position(pos)
        self.y_target_set = True

    # ---- position feedback ----
    def get_x_position(self):
        return self.x.get_position()

    def get_y_position(self):
        return self.y.get_position()

    # ---- discrete-input status ----
    def get_x_status(self):
        if not self.x.connected:
            return None
        try:
            res = self.x.client.read_discrete_inputs(address=X_STATUS_ADDRESS, count=8)
            if res and not res.isError():
                bits = res.bits
                return {
                    "busy": bits[1],
                    "inp": bits[3],
                    "svre": bits[4],
                    "estop": bits[5],
                    "alarm": bits[6],
                }
        except Exception as e:
            print("X DI error:", e)

        return None

    def get_y_status(self):
        if not self.y.connected:
            return None
        try:
            res = self.y.client.read_discrete_inputs(address=Y_STATUS_ADDRESS, count=8)
            if res and not res.isError():
                bits = res.bits
                return {
                    "busy": bits[1],
                    "inp": bits[3],
                    "svre": bits[4],
                    "estop": bits[5],
                    "alarm": bits[6],
                }
        except Exception as e:
            print("Y DI error:", e)

        return None
