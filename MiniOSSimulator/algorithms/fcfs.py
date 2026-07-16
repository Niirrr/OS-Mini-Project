"""
First Come First Serve (FCFS) CPU Scheduling
Non-preemptive. Processes run strictly in order of arrival time.
"""


def fcfs_scheduling(processes):
    """
    processes: list of dicts -> {"pid": str, "arrival": int, "burst": int}
    returns: list of dicts with scheduling results + gantt chart segments
             gantt segment: {"pid": str, "start": int, "end": int}
    """
    procs = sorted(processes, key=lambda p: (p["arrival"], p["pid"]))
    time = 0
    result = []
    gantt = []

    for p in procs:
        start = max(time, p["arrival"])
        finish = start + p["burst"]
        waiting = start - p["arrival"]
        turnaround = finish - p["arrival"]

        result.append({
            "pid": p["pid"],
            "arrival": p["arrival"],
            "burst": p["burst"],
            "start": start,
            "finish": finish,
            "waiting": waiting,
            "turnaround": turnaround,
        })
        gantt.append({"pid": p["pid"], "start": start, "end": finish})
        time = finish

    avg_wait = sum(r["waiting"] for r in result) / len(result)
    avg_turnaround = sum(r["turnaround"] for r in result) / len(result)

    return {"table": result, "gantt": gantt,
            "avg_waiting": avg_wait, "avg_turnaround": avg_turnaround}
