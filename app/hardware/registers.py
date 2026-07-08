"""Modbus coil/register/discrete-input addresses for the X/Y actuator drives.

Ported as-is from the working control app - these values are specific to the
drive configuration on the physical machine and must not be changed without
confirming against the drive documentation.
"""

X_AXIS = {
    "servo_on": 2054,
    "reset": 2053,
    "origin": 2052,
    "start": 3073,
    "stop": 3075,
    "zero": 3076,
    "pos": 2560,
    "speed": 2564,
    "feedback": 3905,
}

Y_AXIS = {
    "servo_on": 2057,
    "reset": 2056,
    "origin": 2055,
    "start": 3081,
    "stop": 3083,
    "zero": 3084,
    "pos": 2568,
    "speed": 2572,
    "feedback": 3921,
}

# Discrete-input status blocks: each read returns 8 bits, of which
# bit 1 = busy, bit 3 = inp, bit 4 = svre, bit 5 = estop, bit 6 = alarm.
# (Machine status - Emergency..Door Lock - lives at the same base address,
# 2048, and is fully covered by DI_PORT_0 below.)
X_STATUS_ADDRESS = 2056
Y_STATUS_ADDRESS = 2064

# ---------------------------------------------------------------------------
# Raw diagnostic I/O map (Debug screen). Each list is (address, label), one
# entry per bit, in address order. Coils (DO) are individually writable;
# discrete inputs (DI) are read-only. "NA"/"Spare" entries exist on the wire
# but have no assigned function yet.
# ---------------------------------------------------------------------------

DO_PORT_0 = [
    (2048, "PP X"),
    (2049, "NP X"),
    (2050, "PP Y"),
    (2051, "NP Y"),
    (2052, "Origin X"),
    (2053, "Reset X"),
    (2054, "SVON X"),
    (2055, "Origin Y"),
]

DO_PORT_1 = [
    (2056, "Reset Y"),
    (2057, "SVON Y"),
    (2058, "Top Cylinder"),
    (2059, "Spare"),
    (2060, "Tower Red"),
    (2061, "Tower Amber"),
    (2062, "Tower Green"),
    (2063, "Buzzer"),
]

DO_X_AXIS = [
    (3072, "NA"),
    (3073, "Start"),
    (3074, "Reset"),
    (3075, "Stop"),
    (3076, "Current Position Zero"),
    (3077, "Pulse Reset Axis"),
    (3078, "NA"),
    (3079, "NA"),
]

# NOTE: addresses 3080-3087 (8 slots) - Start/Stop/Zero here match the
# already-confirmed Y_AXIS start/stop/zero (3081/3083/3084), so the base is
# taken as 3080 even though only "3080 to 3086" was given.
DO_Y_AXIS = [
    (3080, "NA"),
    (3081, "Start"),
    (3082, "Reset"),
    (3083, "Stop"),
    (3084, "Current Position Zero"),
    (3085, "Pulse Reset Axis"),
    (3086, "NA"),
    (3087, "NA"),
]

DI_PORT_0 = [
    (2048, "Emergency"),
    (2049, "Control ON"),
    (2050, "Start"),
    (2051, "Stop"),
    (2052, "Safety Curtain"),
    (2053, "Cylinder Down"),
    (2054, "Cylinder Up"),
    (2055, "Door Lock"),
]

DI_PORT_1 = [
    (2056, "WAREA X"),
    (2057, "BUSY X"),
    (2058, "SETON X"),
    (2059, "INP X"),
    (2060, "SVRE X"),
    (2061, "ESTOP X"),
    (2062, "ALARM X"),
    (2063, "AREA X"),
]

DI_PORT_2 = [
    (2064, "WAREA Y"),
    (2065, "BUSY Y"),
    (2066, "SETON Y"),
    (2067, "INP Y"),
    (2068, "SVRE Y"),
    (2069, "ESTOP Y"),
    (2070, "ALARM Y"),
    (2071, "AREA Y"),
]

CRITICAL_DI_NAMES = {"Emergency", "Safety Curtain", "ESTOP X", "ALARM X", "ESTOP Y", "ALARM Y"}
