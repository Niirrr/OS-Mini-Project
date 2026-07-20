"""
Priority Scheduling - Preemptive

Higher priority number = Higher priority.

Algorithm:
1. At every time unit, consider all arrived processes.
2. Select the process with the highest priority.
3. If a newly arrived process has a higher priority than the currently
   running process, it immediately preempts the CPU.
4. If multiple processes have the same priority, continue running the
   current process. Otherwise, choose the earliest arrived process.
"""


def priority_preemptive_scheduling(processes):
    """
    processes: list of dicts
        {
            "pid": str,
            "arrival": int,
            "burst": int,
            "priority": int
        }

    returns:
        {
            "table": [...],
            "gantt": [...],
            "avg_waiting": float,
            "avg_turnaround": float,
            "avg_response": float,
            "cpu_utilization": float,
            "throughput": float
        }
    """

    if not processes:
        return {
            "table": [],
            "gantt": [],
            "avg_waiting": 0.0,
            "avg_turnaround": 0.0,
            "avg_response": 0.0,
            "cpu_utilization": 0.0,
            "throughput": 0.0,
        }

    # Copy and sort processes by arrival time
    procs = sorted([dict(p) for p in processes],
                   key=lambda p: (p["arrival"], p["pid"]))

    n = len(procs)

    remaining = {p["pid"]: p["burst"] for p in procs}
    arrival = {p["pid"]: p["arrival"] for p in procs}
    burst = {p["pid"]: p["burst"] for p in procs}
    priority = {p["pid"]: p["priority"] for p in procs}

    finish_time = {}
    first_start = {}

    time = 0
    gantt = []

    current_pid = None
    segment_start = 0

    while len(finish_time) < n:

        # Get all arrived and unfinished processes
        available = [
            p for p in procs
            if p["arrival"] <= time and remaining[p["pid"]] > 0
        ]

        # CPU is idle
        if not available:

            if current_pid is not None:
                gantt.append({
                    "pid": current_pid,
                    "start": segment_start,
                    "end": time
                })
                current_pid = None

            next_arrival = min(
                p["arrival"]
                for p in procs
                if remaining[p["pid"]] > 0
            )

            time = next_arrival
            continue

        # -------------------------------------------------
        # Select process (Higher number = Higher priority)
        # -------------------------------------------------

        highest_priority = max(priority[p["pid"]] for p in available)

        candidates = [
            p for p in available
            if priority[p["pid"]] == highest_priority
        ]

        chosen = None

        # Keep current process if it has the same priority
        if current_pid is not None:
            for p in candidates:
                if p["pid"] == current_pid:
                    chosen = p
                    break

        # Otherwise choose earliest arrival, then PID
        if chosen is None:
            chosen = min(
                candidates,
                key=lambda p: (p["arrival"], p["pid"])
            )

        pid = chosen["pid"]

        # Record response time
        if pid not in first_start:
            first_start[pid] = time

        # Context switch
        if pid != current_pid:

            if current_pid is not None:
                gantt.append({
                    "pid": current_pid,
                    "start": segment_start,
                    "end": time
                })

            current_pid = pid
            segment_start = time

        # Execute for one unit
        remaining[pid] -= 1
        time += 1

        # Process completed
        if remaining[pid] == 0:

            finish_time[pid] = time

            gantt.append({
                "pid": pid,
                "start": segment_start,
                "end": time
            })

            current_pid = None
            segment_start = time

    # ----------------------------
    # Build result table
    # ----------------------------

    completed = []

    for p in procs:

        pid = p["pid"]

        ft = finish_time[pid]
        at = arrival[pid]
        bt = burst[pid]
        pr = priority[pid]

        tat = ft - at
        wt = tat - bt
        rt = first_start[pid] - at

        completed.append({
            "pid": pid,
            "arrival": at,
            "burst": bt,
            "priority": pr,
            "start": first_start[pid],
            "finish": ft,
            "waiting": wt,
            "turnaround": tat,
            "response": rt,
        })

    avg_waiting = sum(p["waiting"] for p in completed) / n
    avg_turnaround = sum(p["turnaround"] for p in completed) / n
    avg_response = sum(p["response"] for p in completed) / n

    first_arrival = min(arrival.values())
    last_finish = max(finish_time.values())

    total_time = last_finish - first_arrival
    busy_time = sum(burst.values())

    cpu_utilization = (
        (busy_time / total_time) * 100
        if total_time > 0 else 0.0
    )

    throughput = (
        n / last_finish
        if last_finish > 0 else 0.0
    )

    return {
        "table": completed,
        "gantt": gantt,
        "avg_waiting": avg_waiting,
        "avg_turnaround": avg_turnaround,
        "avg_response": avg_response,
        "cpu_utilization": cpu_utilization,
        "throughput": throughput,
    }