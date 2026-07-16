# Mini OS Simulator — CPU Scheduling Module

A GUI-based simulator for core Operating System scheduling concepts, built with
Python and Tkinter. This first module covers **Process Management & CPU
Scheduling**; Memory, Disk, and File modules follow the same pattern and will
slot into the existing structure.

## How to Run

No external libraries needed — only Tkinter, which ships with Python.

```bash
cd MiniOSSimulator
python main.py
```

(If `tkinter` isn't found on Linux: `sudo apt install python3-tk`)

## What's Implemented

- **FCFS** (First Come First Serve)
- **SJF** (Shortest Job First, non-preemptive)
- **Priority Scheduling** (non-preemptive, lower number = higher priority)
- **Round Robin** (with configurable time quantum)

Each algorithm computes Start/Finish/Waiting/Turnaround time per process,
average waiting & turnaround time, and renders a color-coded **Gantt chart**.

## Project Structure

```
MiniOSSimulator/
├── main.py                # App entry point — creates the window, switches pages
├── gui/
│   ├── home.py             # Landing page with navigation buttons
│   └── cpu.py              # CPU scheduling page: inputs, Gantt chart, results table
├── algorithms/
│   ├── fcfs.py
│   ├── sjf.py
│   ├── priority.py
│   └── rr.py
├── models/                 # (reserved for Memory/Disk/File data models)
├── assets/                 # (reserved for icons/images)
└── README.md
```

## Design Notes (for your viva)

- **Separation of concerns**: `algorithms/*.py` contain pure functions with no
  GUI code — each takes a list of process dicts and returns a results dict
  (`table`, `gantt`, `avg_waiting`, `avg_turnaround`). This means you can unit
  test scheduling logic independently of Tkinter, and reuse the same
  algorithm functions from a CLI or a different GUI later.
- **Page controller pattern**: `main.py` holds all page frames (`HomePage`,
  `CPUPage`, ...) in a dict and raises one at a time with `show_frame()` —
  the standard multi-page Tkinter architecture. Adding `MemoryPage`,
  `DiskPage`, `FilePage` later just means writing the class and registering
  it in `main.py`.
- **Round Robin correctness**: processes are enqueued strictly by arrival
  time (a process arriving *during* another's time-slice is enqueued before
  that process is re-added to the back of the queue after being preempted —
  this matches standard textbook RR behavior).
- **Priority convention**: lower number = higher priority (matches how most
  OS textbooks and this course define it). State this explicitly in your
  demo since some textbooks use the opposite convention.

## How to Extend (Memory / Disk / File modules)

1. Add algorithm logic in `algorithms/` (e.g. `firstfit.py`, `sstf.py`) as a
   pure function, same pattern as the CPU ones.
2. Add a page in `gui/` (e.g. `memory.py`) that imports it, subclassing
   `tk.Frame` the same way `CPUPage` does.
3. Register the new page class in the `for PageClass in (...)` loop in
   `main.py`.
4. Wire up the corresponding button in `gui/home.py` (currently marked
   "coming soon").

## Sample Test Case (used to validate the algorithms)

| PID | Arrival | Burst | Priority |
|-----|---------|-------|----------|
| P1  | 0       | 5     | 2        |
| P2  | 1       | 3     | 1        |
| P3  | 2       | 8     | 3        |
| P4  | 3       | 6     | 2        |

Verified results:
- FCFS → avg waiting 5.75, avg turnaround 11.25
- SJF → avg waiting 5.25, avg turnaround 10.75
- Priority → avg waiting 5.25, avg turnaround 10.75
- Round Robin (q=2) → avg waiting 9.75, avg turnaround 15.25
