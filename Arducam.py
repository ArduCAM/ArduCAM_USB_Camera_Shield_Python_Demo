import threading

import ArducamSDK
from utils import *


class ArducamCamera(object):
    def __init__(self):
        self.isOpened = False
        self.running_ = False
        self.signal_ = threading.Condition()
        pass

    def openCamera(self, fname, index=0):
        self.isOpened, self.handle, self.cameraCfg, self.color_mode = camera_initFromFile(
            fname, index)

        return self.isOpened

    def start(self):
        if not self.isOpened:
            raise RuntimeError("The camera has not been opened.")
        
        self.running_ = True
        ArducamSDK.Py_ArduCam_setMode(self.handle, ArducamSDK.CONTINUOUS_MODE)
        self.capture_thread_ = threading.Thread(target=self.capture_thread)
        self.capture_thread_.daemon = True
        self.capture_thread_.start()

    def read(self, timeout=1500):
        if not self.running_:
            raise RuntimeError("The camera is not running.")

        if ArducamSDK.Py_ArduCam_availableImage(self.handle) <= 0:
            with self.signal_:
                self.signal_.wait(timeout/1000.0)

        if ArducamSDK.Py_ArduCam_availableImage(self.handle) <= 0:
            return (False, None, None)

        ret, data, cfg = ArducamSDK.Py_ArduCam_readImage(self.handle)
        ArducamSDK.Py_ArduCam_del(self.handle)
        size = cfg['u32Size']
        if ret != 0 or size == 0:
            return (False, data, cfg)
    
        return (True, data, cfg)

    def stop(self):
        if not self.running_:
            raise RuntimeError("The camera is not running.")

        self.running_ = False
        self.capture_thread_.join()

    def closeCamera(self):
        if not self.isOpened:
            raise RuntimeError("The camera has not been opened.")

        if (self.running_):
            self.stop()
        self.isOpened = False
        ArducamSDK.Py_ArduCam_close(self.handle)
        self.handle = None


    def capture_thread(self):
        ret = ArducamSDK.Py_ArduCam_beginCaptureImage(self.handle)

        if ret != 0:
            self.running_ = False
            raise RuntimeError("Error beginning capture, Error : {}".format(ErrorCode_toString(ret)))

        print("Capture began, Error :", ErrorCode_toString(ret))
        
        while self.running_:
            ret = ArducamSDK.Py_ArduCam_captureImage(self.handle)
            if ret > 255:
                print("Error capture image, Error :", ErrorCode_toString(ret))
                if ret == ArducamSDK.USB_CAMERA_USB_TASK_ERROR:
                    break
            elif ret > 0:
                with self.signal_:
                    self.signal_.notify()
            
        self.running_ = False
        ArducamSDK.Py_ArduCam_endCaptureImage(self.handle)

    def setCtrl(self, func_name, val):
        return ArducamSDK.Py_ArduCam_setCtrl(self.handle, func_name, val)

    def dumpDeviceInfo(self):
        USB_CPLD_I2C_ADDRESS=0x46
        cpld_info={}
        ret, version = ArducamSDK.Py_ArduCam_readReg_8_8(
            self.handle, USB_CPLD_I2C_ADDRESS, 0x00)
        ret, year = ArducamSDK.Py_ArduCam_readReg_8_8(
            self.handle, USB_CPLD_I2C_ADDRESS, 0x05)
        ret, mouth = ArducamSDK.Py_ArduCam_readReg_8_8(
            self.handle, USB_CPLD_I2C_ADDRESS, 0x06)
        ret, day = ArducamSDK.Py_ArduCam_readReg_8_8(
            self.handle, USB_CPLD_I2C_ADDRESS, 0x07)

        cpld_info["version"] = "v{}.{}".format(version>>4, version & 0x0F)
        cpld_info["year"] = year
        cpld_info["mouth"] = mouth
        cpld_info["day"] = day

        print(cpld_info)

        ret, data = ArducamSDK.Py_ArduCam_getboardConfig(
            self.handle, 0x80, 0x00, 0x00, 2
        )

        usb_info={}
        usb_info["fw_version"] = "v{}.{}".format((data[0] & 0xFF), (data[1] & 0xFF))
        usb_info["interface"] = 2 if self.cameraCfg["usbType"] == 4 else 3
        usb_info["device"] = 3 if self.cameraCfg["usbType"] == 3 or self.cameraCfg["usbType"] == 4 else 2

        print(usb_info)

