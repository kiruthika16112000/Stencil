try:
    from pypylon import pylon

    PYLON_AVAILABLE = True
except ImportError:
    pylon = None
    PYLON_AVAILABLE = False


class CameraController:
    """Wraps a single Basler camera via pypylon.

    Mirrors app.ui.ports's handling of a missing serial port: if the SDK
    isn't installed or no camera is plugged in, `open()` returns False and
    the rest of the app degrades gracefully instead of crashing.
    """

    def __init__(self):
        self._camera = None
        self._converter = None

    @property
    def available(self):
        return PYLON_AVAILABLE

    @property
    def is_open(self):
        return self._camera is not None and self._camera.IsGrabbing()

    def open(self):
        if not PYLON_AVAILABLE:
            return False

        try:
            factory = pylon.TlFactory.GetInstance()
            devices = factory.EnumerateDevices()
            if not devices:
                print("No Basler camera found")
                return False

            self._camera = pylon.InstantCamera(factory.CreateDevice(devices[0]))
            self._camera.Open()

            self._converter = pylon.ImageFormatConverter()
            self._converter.OutputPixelFormat = pylon.PixelType_BGR8packed

            self._camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            return True
        except Exception as error:
            print("Camera open error:", error)
            self._camera = None
            self._converter = None
            return False

    def grab_frame(self):
        """Returns a BGR numpy array for the latest frame, or None if one
        isn't available right now."""
        if not self.is_open:
            return None

        try:
            grab_result = self._camera.RetrieveResult(1000, pylon.TimeoutHandling_Return)
            try:
                if grab_result.GrabSucceeded():
                    return self._converter.Convert(grab_result).GetArray()
            finally:
                grab_result.Release()
        except Exception as error:
            print("Camera grab error:", error)

        return None

    def close(self):
        if self._camera is None:
            return

        try:
            if self._camera.IsGrabbing():
                self._camera.StopGrabbing()
            self._camera.Close()
        except Exception as error:
            print("Camera close error:", error)

        self._camera = None
        self._converter = None
