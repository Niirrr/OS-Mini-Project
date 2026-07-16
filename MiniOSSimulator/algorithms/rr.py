"""
Round Robin CPU Scheduling
Each process gets a fixed time quantum in a circular queue.
"""
from collections import deque


def rr_scheduling(processes, quantum):
    """
    processes: list of dicts -> {"pid": str, "arrival": int, "burst": int}
    quantum: int, time slice
    returns same shape as fcfs_scheduling (gantt has one entry per time-slice run)
    """
    procs = sorted([dict(p) for p in processes], key=lambda p: (p["arrival"], p["pid"]))
    n = len(procs)
    remaining_burst = {p["pid"]: p["burst"] for p in procs}
    first_start = {}
    finish_time = {}

    time = 0
    queue = deque()
    gantt = []
    i = 0  # pointer into procs sorted by arrival, for enqueuing new arrivals

    # enqueue all processes that have arrived by current time
    def enqueue_arrivals(current_time):
        nonlocal i
        while i < n and procs[i]["arrival"] <= current_time:
            queue.append(procs[i])
            i += 1

    # start the clock at the first process's arrival
    time = procs[0]["arrival"]
    enqueue_arrivals(time)

    while queue:
        p = queue.popleft()
        pid = p["pid"]

        if pid not in first_start:
            first_start[pid] = max(time, p["arrival"])

        start = time
        run_time = min(quantum, remaining_burst[pid])
        finish = start + run_time
        remaining_burst[pid] -= run_time
        gantt.append({"pid": pid, "start": start, "end": finish})
        time = finish

        # enqueue any processes that arrived during this run, before re-adding current
        enqueue_arrivals(time)

        if remaining_burst[pid] > 0:
            queue.append(p)
        else:
            finish_time[pid] = finish

        # if queue is empty but processes still remain (haven't arrived yet), jump time
        if not queue and i < n:
            time = procs[i]["arrival"]
            enqueue_arrivals(time)

    completed = []
    for p in procs:
        pid = p["pid"]
        turnaround = finish_time[pid] - p["arrival"]
        waiting = turnaround - p["burst"]
        completed.append({
            "pid": pid,
            "arrival": p["arrival"],
            "burst": p["burst"],
            "start": first_start[pid],
            "finish": finish_time[pid],
            "waiting": waiting,
            "turnaround": turnaround,
        })

    avg_wait = sum(r["waiting"] for r in completed) / n
    avg_turnaround = sum(r["turnaround"] for r in completed) / n

    return {"table": completed, "gantt": gantt,
            "avg_waiting": avg_wait, "avg_turnaround": avg_turnaround}
