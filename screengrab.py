from blocks import MINECRAFT_BLOCKS
from PIL import Image
import mss
import numpy as np

DESIRED_WIDTH = 64
DESIRED_HEIGHT = 36

BLOCK_NAMES = np.array(list(MINECRAFT_BLOCKS.keys()))
BLOCK_COLORS = np.array(list(MINECRAFT_BLOCKS.values()), dtype=np.int32)  # Prevent overflow

def get_downscaled_screen(res=(DESIRED_WIDTH, DESIRED_HEIGHT)):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)
        img = img.resize(res, Image.NEAREST)  # Fast resizing
        return img

def get_minecraft_block_map(res=(DESIRED_WIDTH, DESIRED_HEIGHT)):
    img = get_downscaled_screen(res)
    np_pixels = np.asarray(img, dtype=np.int32)  # Prevent overflow
    h, w = np_pixels.shape[:2]
    flat_pixels = np_pixels.reshape(-1, 3)
    dists = np.sum((flat_pixels[:, None, :] - BLOCK_COLORS[None, :, :]) ** 2, axis=2)
    closest_indices = np.argmin(dists, axis=1)
    block_names = BLOCK_NAMES[closest_indices]
    return block_names.reshape(h, w).tolist()