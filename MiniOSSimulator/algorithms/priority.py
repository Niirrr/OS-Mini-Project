"""
Priority Scheduling - Non-Preemptive
Lower priority number = higher priority (standard OS convention).
At every decision point, pick the arrived process with the best (lowest) priority.
"""


def priority_scheduling(processes):
    """
    processes: list of dicts -> {"pid": str, "arrival": int, "burst": int, "priority": int}
    returns same shape as fcfs_scheduling
    """
    procs = [dict(p) for p in processes]
    n = len(procs)
    completed = []
    time = 0
    gantt = []

    remaining = procs[:]
    while remaining:
        available = [p for p in remaining if p["arrival"] <= time]
        if not available:
            time = min(p["arrival"] for p in remaining)
            available = [p for p in remaining if p["arrival"] <= time]

        # pick best (lowest) priority number; tie-break by arrival, then pid
        chosen = min(available, key=lambda p: (p["priority"], p["arrival"], p["pid"]))
        remaining.remove(chosen)

        start = max(time, chosen["arrival"])
        finish = start + chosen["burst"]
        waiting = start - chosen["arrival"]
        turnaround = finish - chosen["arrival"]

        completed.append({
            "pid": chosen["pid"],
            "arrival": chosen["arrival"],
            "burst": chosen["burst"],
            "priority": chosen["priority"],
            "start": start,
            "finish": finish,
            "waiting": waiting,
            "turnaround": turnaround,
        })
        gantt.append({"pid": chosen["pid"], "start": start, "end": finish})
        time = finish

    avg_wait = sum(r["waiting"] for r in completed) / n
    avg_turnaround = sum(r["turnaround"] for r in completed) / n

    return {"table": completed, "gantt": gantt,
            "avg_waiting": avg_wait, "avg_turnaround": avg_turnaround}
