from blocks import MINECRAFT_BLOCKS
from PIL import Image
import mss
import numpy as np

# Change these values to the size you wish for your screen to be downscaled to
# (Try to make it the same as your aspect ratio)
desiredWidth = 64
desiredHeight = 36

# Convert MINECRAFT_BLOCKS to NumPy array for fast color distance computation
BLOCK_NAMES = list(MINECRAFT_BLOCKS.keys())
BLOCK_COLORS = np.array(list(MINECRAFT_BLOCKS.values()))  # shape: (num_blocks, 3)

def closest_block_color(rgb):
    """Vectorized color distance computation."""
    color = np.array(rgb)
    distances = np.linalg.norm(BLOCK_COLORS - color, axis=1)
    return BLOCK_NAMES[np.argmin(distances)]

def get_downscaled_screen(res=(desiredWidth, desiredHeight)):
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # main monitor
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)
        img = img.resize(res, Image.NEAREST)
        return img

def get_minecraft_block_map(res=(desiredWidth, desiredHeight)):
    img = get_downscaled_screen(res)
    img = img.convert("RGB")
    np_pixels = np.array(img)  # shape: (height, width, 3)
    height, width = np_pixels.shape[:2]

    block_map = [
        [closest_block_color(tuple(np_pixels[y, x])) for x in range(width)]
        for y in range(height)
    ]

    return block_map