from screengrab import *
import time
from mcrcon import MCRcon
import threading
import queue

# Change values to correct host (if it is not local), port, and RCON password
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
            x1, y1, x2, y2, block = q.get(timeout=1)
        except queue.Empty:
            continue

        if rcon:
            if x1 == x2 and y1 == y2:
                cmd = f"setblock {START_X + x1} {START_Y + y1} {START_Z} {block}"
            else:
                cmd = f"fill {START_X + x1} {START_Y + y1} {START_Z} {START_X + x2} {START_Y + y2} {START_Z} {block}"

            try:
                rcon.command(cmd)
            except Exception as e:
                print(f"[Thread {queue_index}] Command failed: {e}")
                thread_local.rcon = None
                rcon = get_rcon()

        q.task_done()

def color_distance(c1, c2):
    """Euclidean distance between two RGB tuples."""
    return ((c1[0] - c2[0]) ** 2 +
            (c1[1] - c2[1]) ** 2 +
            (c1[2] - c2[2]) ** 2) ** 0.5

COLOR_DIFF_THRESHOLD = 20  # Adjust as needed

def send_blocks():
    """Distribute horizontal runs of same block using 'fill' commands."""
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

            # Build run of same block
            while x + 1 < len(row) and row[x + 1] == current_block and previous_block_map[y][x + 1] != current_block:
                x += 1

            # Only send if block differs from previous frame
            run_end = x
            changed = any(previous_block_map[y][xi] != current_block for xi in range(run_start, run_end + 1))

            if changed:
                if run_end > run_start:
                    # Send fill command for run
                    worker_queues[worker_index].put((run_start, flipped_y, run_end, flipped_y, current_block))
                else:
                    # Send single setblock-like fill
                    worker_queues[worker_index].put((run_start, flipped_y, run_start, flipped_y, current_block))

                # Update previous map
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
        time_to_sleep = frame_duration - elapsed
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)