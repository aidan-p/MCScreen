from blocks import MINECRAFT_BLOCKS
from PIL import Image
import mss
import math

# Change these values to the size you wish for your screen to be downscaled to
# (Try to keep it as close to your aspect ratio as possible)
desiredWidth = 128
desiredHeight = 72

def closest_block_color(rgb):
    r, g, b = rgb
    closest_block = None
    min_distance = float("inf")
    for block, (br, bg, bb) in MINECRAFT_BLOCKS.items():
        distance = math.sqrt((r - br)**2 + (g - bg)**2 + (b - bb)**2)
        if distance < min_distance:
            min_distance = distance
            closest_block = block
    return closest_block

def get_downscaled_screen(res=(desiredWidth, desiredHeight)):
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # main monitor
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)
        img = img.resize(res, Image.BILINEAR)
        return img

def get_minecraft_block_map(res=(desiredWidth, desiredHeight)):
    img = get_downscaled_screen(res)
    pixels = img.load()
    width, height = img.size

    block_map = []
    for y in range(height):
        row = []
        for x in range(width):
            rgb = pixels[x, y]
            block = closest_block_color(rgb)
            row.append(block)
        block_map.append(row)

    return block_map