import argparse
import time
import signal
import cv2

from Arducam import *
from ImageConvert import *

exit_ = False


def sigint_handler(signum, frame):
    global exit_
    exit_ = True


signal.signal(signal.SIGINT, sigint_handler)
signal.signal(signal.SIGTERM, sigint_handler)


def display_fps(index):
    display_fps.frame_count += 1

    current = time.time()
    if current - display_fps.start >= 1:
        print("fps: {}".format(display_fps.frame_count))
        display_fps.frame_count = 0
        display_fps.start = current


display_fps.start = time.time()
display_fps.frame_count = 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--config-file', type=str, required=True, help='Specifies the configuration file.')
    parser.add_argument('-v', '--verbose', action='store_true', required=False, help='Output device information.')
    parser.add_argument('--preview-width', type=int, required=False, default=-1, help='Set the display width')
    parser.add_argument('-n', '--nopreview', action='store_true', required=False, help='Disable preview windows.')
    parser.add_argument('-m', '--mode', type=str, required=False, default = 'CONTINUOUS_MODE', help='Mode, CONTINOUS_MODE or EXTERNAL_TRIGGER_MODE.')

    args = parser.parse_args()
    config_file = args.config_file
    verbose = args.verbose
    preview_width = args.preview_width
    no_preview = args.nopreview
    mode = args.mode

    camera = ArducamCamera()

    if not camera.openCamera(config_file):
        raise RuntimeError("Failed to open camera.")

    if verbose:
        camera.dumpDeviceInfo()

    camera.start(mode = mode)

    # camera.setCtrl("setFramerate", 2)
    camera.setCtrl("setExposureTime", 1000)
    camera.setCtrl("setDigitalGainR", 150)
    camera.setCtrl("setDigitalGainB", 150)
    camera.setCtrl("setAnalogueGain", 800)


    scale_width = preview_width

    while not exit_:
        ret, data, cfg = camera.read()

        if mode == 'CONTINUOUS_MODE':
            display_fps(0)

        if no_preview:
            continue

        if ret:
            image = convert_image(data, cfg, camera.color_mode)

            if scale_width != -1:
                scale = scale_width / image.shape[1]
                image = cv2.resize(image, None, fx=scale, fy=scale)

            cv2.imshow("Arducam", image)
            print('image!')
            np.array(data, dtype=np.uint8).tofile("image.raw")
        else:
            if mode == 'CONTINOUS_MODE':
                print("timeout")

        key = cv2.waitKey(1)
        if key == ord('q'):
            exit_ = True
        elif key == ord('s'):
            np.array(data, dtype=np.uint8).tofile("image.raw")

    camera.stop()
    camera.closeCamera()