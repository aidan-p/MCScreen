from screengrab import *
import time
import threading
import queue
import socket
from mcrcon import MCRcon

# === CONFIGURATION ===
USE_FAST_PLUGIN = True  # Set to False to use RCON, otherwise True to use plugin
HOST = "localhost"
RCON_PORT = 25575
PLUGIN_PORT = 25566
PASSWORD = "yourpassword"
FRAME_RATE = 30
START_X, START_Y, START_Z = 0, 20, 0
NUM_WORKERS = 16
COLOR_DIFF_THRESHOLD = 20

previous_block_map = None
worker_queues = [queue.Queue() for _ in range(NUM_WORKERS)]
thread_local = threading.local()

# === CONNECTION SETUP ===
def get_connection():
    if not hasattr(thread_local, "conn") or thread_local.conn is None:
        try:
            if USE_FAST_PLUGIN:
                thread_local.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                thread_local.conn.connect((HOST, PLUGIN_PORT))
            else:
                thread_local.conn = MCRcon(HOST, PASSWORD, port=RCON_PORT)
                thread_local.conn.connect()
        except Exception as e:
            print(f"[{threading.current_thread().name}] Connection error: {e}")
            thread_local.conn = None
    return thread_local.conn

def block_worker(queue_index):
    q = worker_queues[queue_index]
    conn = get_connection()

    while True:
        try:
            x1, y1, x2, y2, block = q.get(timeout=1)
        except queue.Empty:
            continue

        if conn:
            cmd = f"setblock {START_X + x1} {START_Y + y1} {START_Z} {block}" if x1 == x2 and y1 == y2 else \
                  f"fill {START_X + x1} {START_Y + y1} {START_Z} {START_X + x2} {START_Y + y2} {START_Z} {block}"
            try:
                if USE_FAST_PLUGIN:
                    conn.sendall((cmd + "\n").encode())
                else:
                    conn.command(cmd)
            except Exception as e:
                print(f"[Thread {queue_index}] Command failed: {e}")
                thread_local.conn = None
                conn = get_connection()

        q.task_done()

def send_blocks():
    global previous_block_map
    block_map = get_minecraft_block_map()
    total_rows = len(block_map)

    if previous_block_map is None:
        previous_block_map = [row[:] for row in block_map]

    for y, row in enumerate(block_map):
        flipped_y = total_rows - y - 1
        worker_index = y % NUM_WORKERS

        for x, current_block in enumerate(row):
            prev_block = previous_block_map[y][x]
            if current_block != prev_block:
                worker_queues[worker_index].put((x, flipped_y, x, flipped_y, current_block))
                previous_block_map[y][x] = current_block

def main():
    for i in range(NUM_WORKERS):
        threading.Thread(target=block_worker, args=(i,), daemon=True).start()

    while True:
        start_time = time.time()
        send_blocks()
        for q in worker_queues:
            q.join()
        elapsed = time.time() - start_time
        time.sleep(max(0, 1 / FRAME_RATE - elapsed))

if __name__ == "__main__":
    main()