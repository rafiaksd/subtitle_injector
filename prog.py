import time
loop_range = 5
max_bars_num = 50

for i in range(loop_range):
    # Calculate bars_num to reach max_bars_num only at i == loop_range - 1
    bars_num = int((i / (loop_range - 1)) * max_bars_num)
    bars = "#"
    no_bars = "*"
    print(f"\r{bars * bars_num + no_bars * (max_bars_num - bars_num)}\t{i+1}", end="", flush=True)
    time.sleep(0.5)  # Small delay to see the progress
