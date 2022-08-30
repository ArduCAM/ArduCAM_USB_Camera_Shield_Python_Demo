import ArducamSDK
import arducam_config_parser
import time


def configBoard(handle, config):
    ArducamSDK.Py_ArduCam_setboardConfig(handle, config.params[0],
                                         config.params[1], config.params[2], config.params[3],
                                         config.params[4:config.params_length])


def camera_initFromFile(fileName, index):
    # load config file
    config = arducam_config_parser.LoadConfigFile(fileName)

    camera_parameter = config.camera_param.getdict()
    width = camera_parameter["WIDTH"]
    height = camera_parameter["HEIGHT"]

    BitWidth = camera_parameter["BIT_WIDTH"]
    ByteLength = 1
    if BitWidth > 8 and BitWidth <= 16:
        ByteLength = 2
    FmtMode = camera_parameter["FORMAT"][0]
    color_mode = camera_parameter["FORMAT"][1]
    print("color mode", color_mode)

    I2CMode = camera_parameter["I2C_MODE"]
    I2cAddr = camera_parameter["I2C_ADDR"]
    TransLvl = camera_parameter["TRANS_LVL"]
    cfg = {"u32CameraType": 0x00,
           "u32Width": width, "u32Height": height,
           "usbType": 0,
           "u8PixelBytes": ByteLength,
           "u16Vid": 0,
           "u32Size": 0,
           "u8PixelBits": BitWidth,
           "u32I2cAddr": I2cAddr,
           "emI2cMode": I2CMode,
           "emImageFmtMode": FmtMode,
           "u32TransLvl": TransLvl}

    ret, handle, rtn_cfg = ArducamSDK.Py_ArduCam_open(cfg, index)
    # ret, handle, rtn_cfg = ArducamSDK.Py_ArduCam_autoopen(cfg)
    if ret == 0:

        # ArducamSDK.Py_ArduCam_writeReg_8_8(handle,0x46,3,0x00)
        usb_version = rtn_cfg['usbType']
        configs = config.configs
        configs_length = config.configs_length
        for i in range(configs_length):
            type = configs[i].type
            if ((type >> 16) & 0xFF) != 0 and ((type >> 16) & 0xFF) != usb_version:
                continue
            if type & 0xFFFF == arducam_config_parser.CONFIG_TYPE_REG:
                ArducamSDK.Py_ArduCam_writeSensorReg(
                    handle, configs[i].params[0], configs[i].params[1])
            elif type & 0xFFFF == arducam_config_parser.CONFIG_TYPE_DELAY:
                time.sleep(float(configs[i].params[0])/1000)
            elif type & 0xFFFF == arducam_config_parser.CONFIG_TYPE_VRCMD:
                configBoard(handle, configs[i])

        ArducamSDK.Py_ArduCam_registerCtrls(
            handle, config.controls, config.controls_length)

        rtn_val, datas = ArducamSDK.Py_ArduCam_readUserData(
            handle, 0x400-16, 16)
        print("Serial: %c%c%c%c-%c%c%c%c-%c%c%c%c" % (datas[0], datas[1], datas[2], datas[3],
                                                      datas[4], datas[5], datas[6], datas[7],
                                                      datas[8], datas[9], datas[10], datas[11]))

        return (True, handle, rtn_cfg, color_mode)

    print("open fail,rtn_val = ", ret)
    return (False, handle, rtn_cfg, color_mode)
