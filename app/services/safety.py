def is_axis_ready(status):
    if status is None:
        return False
    return status["svre"] and status["inp"] and status["estop"] and status["alarm"]
