import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox

from algorithms.fcfs import fcfs_scheduling
from algorithms.sjf import sjf_scheduling
from algorithms.priority import priority_scheduling
from algorithms.rr import rr_scheduling

GANTT_COLORS = ["#89b4fa", "#f38ba8", "#a6e3a1", "#f9e2af",
                "#cba6f7", "#fab387", "#94e2d5", "#eba0ac"]


class CPUPage(tb.Frame):
    """CPU Scheduling simulator: FCFS, SJF, Priority, Round Robin."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.row_widgets = []  # holds (pid_entry, arrival_entry, burst_entry, priority_entry)
        self.pid_colors = {}

        self._build_header()
        self._build_controls()
        self._build_table_input()
        self._build_output()

        # Add sample processes to help user get started quickly
        self._add_row(pid="P1", arrival="0", burst="5", priority="2")
        self._add_row(pid="P2", arrival="1", burst="3", priority="1")
        self._add_row(pid="P3", arrival="2", burst="8", priority="3")
        self._add_row(pid="P4", arrival="3", burst="6", priority="2")

        # Initial refresh
        self._refresh_column_visibility()

    def on_show(self):
        """Called by controller when this frame is raised."""
        self._refresh_column_visibility()

    # ---------- UI construction ----------

    def _build_header(self):
        top = tb.Frame(self)
        top.pack(fill="x", padx=20, pady=(15, 10))

        btn_back = tb.Button(
            top, text="← Dashboard", bootstyle="outline-light",
            command=lambda: self.controller.show_frame("HomePage"),
            cursor="hand2"
        )
        btn_back.pack(side="left")

        lbl_title = tb.Label(
            top, text="CPU Scheduling Simulator", font=("Segoe UI", 18, "bold"),
            bootstyle="light"
        )
        lbl_title.pack(side="left", padx=15)

    def _build_controls(self):
        bar = tb.Frame(self)
        bar.pack(fill="x", padx=20, pady=10)

        # Gridding controls for a clean layout that doesn't jump
        bar.columnconfigure(5, weight=1)

        lbl_algo = tb.Label(bar, text="Algorithm:", font=("Segoe UI", 10, "bold"))
        lbl_algo.grid(row=0, column=0, padx=(0, 8), pady=5, sticky="w")

        self.algo_var = tb.StringVar(value="FCFS")
        self.algo_menu = tb.Combobox(
            bar, textvariable=self.algo_var, state="readonly", width=22,
            values=["FCFS", "SJF (Non-Preemptive)", "Priority (Non-Preemptive)", "Round Robin"]
        )
        self.algo_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.algo_menu.bind("<<ComboboxSelected>>", lambda e: self._refresh_column_visibility())

        # Quantum Container (Col 2)
        self.quantum_container = tb.Frame(bar)
        lbl_q = tb.Label(self.quantum_container, text="Quantum:", font=("Segoe UI", 10, "bold"))
        lbl_q.pack(side="left", padx=(0, 5))
        self.quantum_var = tb.StringVar(value="2")
        self.quantum_entry = tb.Entry(self.quantum_container, textvariable=self.quantum_var, width=5, justify="center")
        self.quantum_entry.pack(side="left")
        
        # Grid initially (visibility toggled dynamically)
        self.quantum_container.grid(row=0, column=2, padx=15, pady=5, sticky="w")

        # Action Buttons (Cols 3 & 4)
        btn_add = tb.Button(bar, text="+ Add Process", bootstyle="success", command=self._add_row, cursor="hand2")
        btn_add.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        btn_rem = tb.Button(bar, text="- Remove Last", bootstyle="danger", command=self._remove_row, cursor="hand2")
        btn_rem.grid(row=0, column=4, padx=5, pady=5, sticky="w")

        # Run Button aligned to the right (Col 5)
        btn_run = tb.Button(
            bar, text="▶ Run Simulation", bootstyle="primary", 
            command=self._run, cursor="hand2"
        )
        btn_run.grid(row=0, column=5, padx=5, pady=5, sticky="e")

    def _build_table_input(self):
        self.input_frame = tb.Labelframe(self, text=" Process Configuration ", padding=15, bootstyle="secondary")
        self.input_frame.pack(fill="x", padx=20, pady=10)

        self.table_grid = tb.Frame(self.input_frame)
        self.table_grid.pack(fill="x")

        # Configure columns to expand nicely
        self.table_grid.columnconfigure(0, weight=1, minsize=80)   # PID
        self.table_grid.columnconfigure(1, weight=2, minsize=120)  # Arrival Time
        self.table_grid.columnconfigure(2, weight=2, minsize=120)  # Burst Time
        self.table_grid.columnconfigure(3, weight=2, minsize=120)  # Priority

        # Headers
        self.hdr_pid = tb.Label(self.table_grid, text="Process ID", font=("Segoe UI", 10, "bold"), anchor="center", bootstyle="light")
        self.hdr_arr = tb.Label(self.table_grid, text="Arrival Time", font=("Segoe UI", 10, "bold"), anchor="center", bootstyle="light")
        self.hdr_bst = tb.Label(self.table_grid, text="Burst Time", font=("Segoe UI", 10, "bold"), anchor="center", bootstyle="light")
        self.hdr_pri = tb.Label(self.table_grid, text="Priority", font=("Segoe UI", 10, "bold"), anchor="center", bootstyle="light")

        # Grid the headers initially in row 0
        self.hdr_pid.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.hdr_arr.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.hdr_bst.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.hdr_pri.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

    def _build_output(self):
        out = tb.Frame(self)
        out.pack(fill="both", expand=True, padx=20, pady=10)

        # Gantt Chart Card
        gantt_card = tb.Labelframe(out, text=" Gantt Chart Visualization ", padding=10, bootstyle="info")
        gantt_card.pack(fill="x", pady=(0, 15))

        # Horizontal Scrollbar and Canvas container
        self.gantt_container = tb.Frame(gantt_card)
        self.gantt_container.pack(fill="x", expand=True)

        self.canvas = tk.Canvas(self.gantt_container, height=90, bg="#181825", highlightthickness=0)
        self.canvas.pack(fill="x", expand=True)

        self.hbar = tb.Scrollbar(self.gantt_container, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.hbar.set)
        self.hbar.pack(fill="x", pady=(5, 0))

        # Results Labelframe
        results_card = tb.Labelframe(out, text=" Simulation Results ", padding=10, bootstyle="success")
        results_card.pack(fill="both", expand=True)

        # Scrollable Treeview Container
        tree_container = tb.Frame(results_card)
        tree_container.pack(fill="both", expand=True, pady=(0, 8))

        cols = ("pid", "arrival", "burst", "start", "finish", "turnaround", "waiting")
        self.tree = tb.Treeview(tree_container, columns=cols, show="headings", height=5, bootstyle="success")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = tb.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        headings = ["PID", "Arrival Time", "Burst Time", "Start Time", "Completion Time", "Turnaround Time", "Waiting Time"]
        for c, h in zip(cols, headings):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=100, anchor="center")

        # Stats Cards Footer
        self.stats_frame = tb.Frame(results_card)
        self.stats_frame.pack(fill="x", pady=(5, 0))

        self.wait_card = tb.Frame(self.stats_frame, bootstyle="dark", padding=10)
        self.wait_card.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.wait_title = tb.Label(self.wait_card, text="Average Waiting Time", font=("Segoe UI", 9), bootstyle="secondary")
        self.wait_title.pack(anchor="w")
        self.wait_val = tb.Label(self.wait_card, text="0.00 ms", font=("Segoe UI", 16, "bold"), bootstyle="info")
        self.wait_val.pack(anchor="w", pady=(2, 0))

        self.turn_card = tb.Frame(self.stats_frame, bootstyle="dark", padding=10)
        self.turn_card.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.turn_title = tb.Label(self.turn_card, text="Average Turnaround Time", font=("Segoe UI", 9), bootstyle="secondary")
        self.turn_title.pack(anchor="w")
        self.turn_val = tb.Label(self.turn_card, text="0.00 ms", font=("Segoe UI", 16, "bold"), bootstyle="success")
        self.turn_val.pack(anchor="w", pady=(2, 0))

    # ---------- dynamic rows ----------

    def _add_row(self, pid=None, arrival="0", burst="5", priority="1"):
        idx = len(self.row_widgets)
        row_num = idx + 1

        pid_val = pid if pid else f"P{idx + 1}"

        pid_e = tb.Entry(self.table_grid, justify="center")
        pid_e.insert(0, pid_val)

        arr_e = tb.Entry(self.table_grid, justify="center")
        arr_e.insert(0, str(arrival))

        burst_e = tb.Entry(self.table_grid, justify="center")
        burst_e.insert(0, str(burst))

        pri_e = tb.Entry(self.table_grid, justify="center")
        pri_e.insert(0, str(priority))

        # Grid layout
        pid_e.grid(row=row_num, column=0, padx=5, pady=4, sticky="ew")
        arr_e.grid(row=row_num, column=1, padx=5, pady=4, sticky="ew")
        burst_e.grid(row=row_num, column=2, padx=5, pady=4, sticky="ew")
        pri_e.grid(row=row_num, column=3, padx=5, pady=4, sticky="ew")

        self.row_widgets.append((pid_e, arr_e, burst_e, pri_e))
        self._refresh_column_visibility()

    def _remove_row(self):
        if len(self.row_widgets) <= 1:
            return
        pid_e, arr_e, burst_e, pri_e = self.row_widgets.pop()
        pid_e.destroy()
        arr_e.destroy()
        burst_e.destroy()
        pri_e.destroy()

    def _refresh_column_visibility(self):
        algo = self.algo_var.get()

        # Priority Visibility
        show_priority = (algo == "Priority (Non-Preemptive)")
        if show_priority:
            self.hdr_pri.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
            for idx, (_, _, _, pri_e) in enumerate(self.row_widgets):
                row_num = idx + 1
                pri_e.grid(row=row_num, column=3, padx=5, pady=4, sticky="ew")
            self.table_grid.columnconfigure(3, weight=2, minsize=120)
        else:
            self.hdr_pri.grid_forget()
            for (_, _, _, pri_e) in self.row_widgets:
                pri_e.grid_forget()
            self.table_grid.columnconfigure(3, weight=0, minsize=0)

        # Quantum Visibility
        show_quantum = (algo == "Round Robin")
        if show_quantum:
            self.quantum_container.grid(row=0, column=2, padx=15, pady=5, sticky="w")
        else:
            self.quantum_container.grid_forget()

    # ---------- run & render ----------

    def _read_processes(self):
        processes = []
        algo = self.algo_var.get()
        is_priority_algo = algo.startswith("Priority")

        for pid_e, arr_e, burst_e, pri_e in self.row_widgets:
            pid = pid_e.get().strip()
            if not pid:
                raise ValueError("Process IDs cannot be empty.")
            try:
                arrival = int(arr_e.get().strip())
                burst = int(burst_e.get().strip())

                if is_priority_algo:
                    priority = int(pri_e.get().strip())
                else:
                    try:
                        priority = int(pri_e.get().strip())
                    except ValueError:
                        priority = 1
            except ValueError:
                raise ValueError(f"Invalid number in row for '{pid}'. Use integers only.")
            if burst <= 0:
                raise ValueError(f"Burst time for '{pid}' must be positive.")
            if arrival < 0:
                raise ValueError(f"Arrival time for '{pid}' cannot be negative.")
            processes.append({"pid": pid, "arrival": arrival, "burst": burst, "priority": priority})

        pids = [p["pid"] for p in processes]
        if len(set(pids)) != len(pids):
            raise ValueError("Process IDs (PIDs) must be unique.")
        if not processes:
            raise ValueError("Add at least one process.")
        return processes

    def _run(self):
        try:
            processes = self._read_processes()
            algo = self.algo_var.get()

            if algo == "FCFS":
                result = fcfs_scheduling(processes)
            elif algo.startswith("SJF"):
                result = sjf_scheduling(processes)
            elif algo.startswith("Priority"):
                result = priority_scheduling(processes)
            else:
                try:
                    quantum = int(self.quantum_var.get().strip())
                    if quantum <= 0:
                        raise ValueError
                except ValueError:
                    raise ValueError("Quantum must be a positive whole number.")
                result = rr_scheduling(processes, quantum)

            self._render_result(result)
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def _color_for(self, pid):
        if pid not in self.pid_colors:
            self.pid_colors[pid] = GANTT_COLORS[len(self.pid_colors) % len(GANTT_COLORS)]
        return self.pid_colors[pid]

    def _render_result(self, result):
        # Clear & fill Results Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in result["table"]:
            self.tree.insert("", "end", values=(
                r["pid"], r["arrival"], r["burst"], r["start"], r["finish"],
                r["turnaround"], r["waiting"]
            ))

        # Update Summary Stats
        self.wait_val.config(text=f"{result['avg_waiting']:.2f} ms")
        self.turn_val.config(text=f"{result['avg_turnaround']:.2f} ms")

        # Render Gantt Chart
        self.canvas.delete("all")
        gantt = result["gantt"]
        if not gantt:
            return

        # Calculate time segments including idle times
        full_timeline = []
        current_time = 0
        for seg in gantt:
            if seg["start"] > current_time:
                # CPU was idle
                full_timeline.append({
                    "pid": "IDLE", 
                    "start": current_time, 
                    "end": seg["start"], 
                    "idle": True
                })
            full_timeline.append({
                "pid": seg["pid"], 
                "start": seg["start"], 
                "end": seg["end"], 
                "idle": False
            })
            current_time = seg["end"]

        total_time = current_time
        
        # Scaling logic: make the segments look nicely sized (min width of 800)
        pixel_per_unit = max(40, 800 / total_time) if total_time > 0 else 40
        canvas_width = total_time * pixel_per_unit + 100
        
        margin_x = 30
        y0, y1 = 15, 55

        for seg in full_timeline:
            x0 = margin_x + seg["start"] * pixel_per_unit
            x1 = margin_x + seg["end"] * pixel_per_unit
            
            if seg.get("idle"):
                # Draw idle block (dashed boundary)
                self.canvas.create_rectangle(x0, y0, x1, y1, fill="#2b303c", outline="#4f5b66", width=1, dash=(4, 4))
                self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text="IDLE", fill="#65737e", font=("Segoe UI", 9, "bold"))
            else:
                color = self._color_for(seg["pid"])
                # Clean rectangular block
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="#11121d", width=2)
                # Label
                self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=seg["pid"], fill="#11121d", font=("Segoe UI", 10, "bold"))
            
            # Start time marker
            self.canvas.create_text(x0, y1 + 12, text=str(seg["start"]), fill="#cdd6f4", font=("Segoe UI", 8))

        # Final end time marker
        if full_timeline:
            x_end = margin_x + full_timeline[-1]["end"] * pixel_per_unit
            self.canvas.create_text(x_end, y1 + 12, text=str(full_timeline[-1]["end"]), fill="#cdd6f4", font=("Segoe UI", 8))

        # Update Canvas configuration for scrollbar
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=(0, 0, canvas_width, 90))
