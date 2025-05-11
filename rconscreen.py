from screengrab import *
import time
from mcrcon import MCRcon
import threading
import queue

HOST = "localhost"
PORT = 25575
PASSWORD = "yourpassword"

frame_duration = 1.0 / 30
START_X, START_Y, START_Z = 0, 20, 0
NUM_WORKERS = 9  # For 16:9 aspect ratio
previous_block_map = None

# Each worker gets its own task queue
worker_queues = [queue.Queue() for _ in range(NUM_WORKERS)]

thread_local = threading.local()

def get_rcon():
    """Get or create a persistent RCON connection per thread."""
    if not hasattr(thread_local, "rcon") or thread_local.rcon is None:
        try:
            rcon = MCRcon(HOST, PASSWORD, port=PORT)
            rcon.connect()
            thread_local.rcon = rcon
        except Exception as e:
            print(f"[{threading.current_thread().name}] Failed to connect RCON: {e}")
            thread_local.rcon = None
    return thread_local.rcon

def block_worker(queue_index):
    q = worker_queues[queue_index]
    rcon = get_rcon()

    while True:
        try:
            x, y, block = q.get(timeout=1)
        except queue.Empty:
            continue

        if rcon:
            cmd = f"setblock {START_X + x} {START_Y + y} {START_Z} {block}"
            try:
                rcon.command(cmd)
            except Exception as e:
                print(f"[Thread {queue_index}] Command failed at ({x},{y}): {e}")
                thread_local.rcon = None  # Reset and reconnect
                rcon = get_rcon()

        q.task_done()

def send_blocks():
    global previous_block_map
    block_map = get_minecraft_block_map()
    total_rows = len(block_map)

    # First frame: send everything
    if previous_block_map is None:
        previous_block_map = [["" for _ in row] for row in block_map]

    # We are only sending rcon commands for blocks that are different
    for y, row in enumerate(block_map):
        flipped_y = total_rows - y - 1
        worker_index = y % NUM_WORKERS
        for x, block in enumerate(row):
            if previous_block_map[y][x] != block:
                worker_queues[worker_index].put((x, flipped_y, block))
                previous_block_map[y][x] = block  # Update the cache

def wait_for_workers():
    for q in worker_queues:
        q.join()

if __name__ == "__main__":
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=block_worker, args=(i,), daemon=True)
        t.start()

    while True:
        start_time = time.time()

        send_blocks()
        wait_for_workers()

        elapsed = time.time() - start_time
        time_to_sleep = frame_duration - elapsed
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)