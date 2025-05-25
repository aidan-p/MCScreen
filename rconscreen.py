from screengrab import *
import time
import threading
import queue
import socket
from mcrcon import MCRcon

# === CONFIGURATION ===
USE_FAST_PLUGIN = True  # Set to False to use RCON
HOST = "localhost"
RCON_PORT = 25575
PLUGIN_PORT = 25566
PASSWORD = "yourpassword"
frame_duration = 1.0 / 165
START_X, START_Y, START_Z = 0, 20, 0
NUM_WORKERS = 16  # For 16:9 aspect ratio
COLOR_DIFF_THRESHOLD = 20

previous_block_map = None
worker_queues = [queue.Queue() for _ in range(NUM_WORKERS)]
thread_local = threading.local()

# === CONNECTION SETUP ===
def get_connection():
    if not hasattr(thread_local, "conn") or thread_local.conn is None:
        try:
            if USE_FAST_PLUGIN:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((HOST, PLUGIN_PORT))
                thread_local.conn = s
            else:
                rcon = MCRcon(HOST, PASSWORD, port=RCON_PORT)
                rcon.connect()
                thread_local.conn = rcon
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
            if x1 == x2 and y1 == y2:
                cmd = f"setblock {START_X + x1} {START_Y + y1} {START_Z} {block}"
            else:
                cmd = f"fill {START_X + x1} {START_Y + y1} {START_Z} {START_X + x2} {START_Y + y2} {START_Z} {block}"

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

def color_distance(c1, c2):
    return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5

def send_blocks():
    global previous_block_map
    block_map = get_minecraft_block_map()
    total_rows = len(block_map)

    if previous_block_map is None:
        previous_block_map = [["" for _ in row] for row in block_map]

    for y, row in enumerate(block_map):
        flipped_y = total_rows - y - 1
        worker_index = y % NUM_WORKERS

        x = 0
        while x < len(row):
            current_block = row[x]
            prev_block = previous_block_map[y][x]
            run_start = x

            while x + 1 < len(row) and row[x + 1] == current_block and previous_block_map[y][x + 1] != current_block:
                x += 1

            run_end = x
            changed = any(previous_block_map[y][xi] != current_block for xi in range(run_start, run_end + 1))

            if changed:
                if run_end > run_start:
                    worker_queues[worker_index].put((run_start, flipped_y, run_end, flipped_y, current_block))
                else:
                    worker_queues[worker_index].put((run_start, flipped_y, run_start, flipped_y, current_block))

                for xi in range(run_start, run_end + 1):
                    previous_block_map[y][xi] = current_block

            x += 1

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
        time.sleep(max(0, frame_duration - elapsed))