import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
from ttkbootstrap.widgets.scrolled import ScrolledFrame

from algorithms.fcfs import fcfs_scheduling
from algorithms.sjf import sjf_scheduling
from algorithms.srtf import srtf_scheduling
from algorithms.priority import priority_scheduling
from algorithms.priority_preemptive import priority_preemptive_scheduling
from algorithms.rr import rr_scheduling
from gui.compare import CompareWindow

GANTT_COLORS = ["#89b4fa", "#f38ba8", "#a6e3a1", "#f9e2af",
                "#cba6f7", "#fab387", "#94e2d5", "#eba0ac"]


class CPUPage(tb.Frame):
    """CPU Scheduling simulator: FCFS, SJF, Priority, Round Robin."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.row_widgets = []  # holds (pid_entry, arrival_entry, burst_entry, priority_entry)
        self.pid_colors = {}
        self._anim_id   = None  # tracks the running after() animation

        # Scrollable container to make the entire window display scrollable
        self.scroll_container = ScrolledFrame(self, autohide=True)
        self.scroll_container.pack(fill="both", expand=True)

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
        top = tb.Frame(self.scroll_container)
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
        bar = tb.Frame(self.scroll_container)
        bar.pack(fill="x", padx=20, pady=10)

        # Gridding controls for a clean layout that doesn't jump
        bar.columnconfigure(5, weight=1)

        lbl_algo = tb.Label(bar, text="Algorithm:", font=("Segoe UI", 10, "bold"))
        lbl_algo.grid(row=0, column=0, padx=(0, 8), pady=5, sticky="w")

        self.algo_var = tb.StringVar(value="FCFS")
        self.algo_menu = tb.Combobox(
            bar, textvariable=self.algo_var, state="readonly", width=24,
            values=["FCFS", "SJF (Non-Preemptive)", "SJF (Preemptive)", "Priority (Non-Preemptive)", "Priority (Preemptive)", "Round Robin"]
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

        # Run Button (Col 5, right-aligned)
        btn_run = tb.Button(
            bar, text="▶ Run Simulation", bootstyle="primary", 
            command=self._run, cursor="hand2"
        )
        btn_run.grid(row=0, column=5, padx=5, pady=5, sticky="e")

        # Compare Button (Col 6, right of Run)
        btn_compare = tb.Button(
            bar, text="⚖ Compare", bootstyle="outline-info",
            command=self._compare, cursor="hand2"
        )
        btn_compare.grid(row=0, column=6, padx=(0, 5), pady=5, sticky="e")

    def _build_table_input(self):
        self.input_frame = tb.Labelframe(self.scroll_container, text=" Process Configuration ", padding=15, bootstyle="secondary")
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
        # Outer container — horizontal split: left (charts+results) | right (queue panel)
        out = tb.Frame(self.scroll_container)
        out.pack(fill="both", expand=True, padx=20, pady=10)

        # Left column: all existing Gantt + Results content
        left_col = tb.Frame(out)
        left_col.pack(side="left", fill="both", expand=True)

        # Right column: live queue panel (fixed width)
        right_col = tb.Frame(out, width=235)
        right_col.pack(side="right", fill="y", padx=(12, 0))
        right_col.pack_propagate(False)

        # ── Gantt Chart Card (unchanged, now inside left_col) ──
        gantt_card = tb.Labelframe(left_col, text=" Gantt Chart Visualization ", padding=10, bootstyle="info")
        gantt_card.pack(fill="x", pady=(0, 15))

        self.gantt_container = tb.Frame(gantt_card)
        self.gantt_container.pack(fill="x", expand=True)

        self.canvas = tk.Canvas(self.gantt_container, height=90, bg="#181825", highlightthickness=0)
        self.canvas.pack(fill="x", expand=True)

        self.hbar = tb.Scrollbar(self.gantt_container, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.hbar.set)
        self.hbar.pack(fill="x", pady=(5, 0))

        # ── Results Labelframe (unchanged, now inside left_col) ──
        results_card = tb.Labelframe(left_col, text=" Simulation Results ", padding=10, bootstyle="success")
        results_card.pack(fill="both", expand=True)

        tree_container = tb.Frame(results_card)
        tree_container.pack(fill="both", expand=True, pady=(0, 8))

        cols = ("pid", "arrival", "burst", "start", "finish", "turnaround", "waiting", "response")
        self.tree = tb.Treeview(tree_container, columns=cols, show="headings", height=5, bootstyle="success")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = tb.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        headings  = ["PID", "Arrival Time", "Burst Time", "Start Time", "Completion Time",
                     "Turnaround Time", "Waiting Time", "Response Time"]
        col_widths = [70, 90, 80, 80, 120, 110, 90, 100]
        for c, h, w in zip(cols, headings, col_widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="center")

        # Stats Cards Footer
        self.stats_frame = tb.Frame(results_card)
        self.stats_frame.pack(fill="x", pady=(5, 0))

        row1 = tb.Frame(self.stats_frame)
        row1.pack(fill="x", pady=(0, 8))

        self.wait_card = tb.Frame(row1, bootstyle="dark", padding=10)
        self.wait_card.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.wait_title = tb.Label(self.wait_card, text="Avg Waiting Time", font=("Segoe UI", 9), bootstyle="light")
        self.wait_title.pack(anchor="w")
        self.wait_val = tb.Label(self.wait_card, text="—", font=("Segoe UI", 16, "bold"), bootstyle="info")
        self.wait_val.pack(anchor="w", pady=(2, 0))

        self.turn_card = tb.Frame(row1, bootstyle="dark", padding=10)
        self.turn_card.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.turn_title = tb.Label(self.turn_card, text="Avg Turnaround Time", font=("Segoe UI", 9), bootstyle="light")
        self.turn_title.pack(anchor="w")
        self.turn_val = tb.Label(self.turn_card, text="—", font=("Segoe UI", 16, "bold"), bootstyle="success")
        self.turn_val.pack(anchor="w", pady=(2, 0))

        row2 = tb.Frame(self.stats_frame)
        row2.pack(fill="x")

        self.resp_card = tb.Frame(row2, bootstyle="dark", padding=10)
        self.resp_card.pack(side="left", fill="x", expand=True, padx=(0, 6))
        tb.Label(self.resp_card, text="Avg Response Time", font=("Segoe UI", 9), bootstyle="light").pack(anchor="w")
        self.resp_val = tb.Label(self.resp_card, text="—", font=("Segoe UI", 16, "bold"), bootstyle="warning")
        self.resp_val.pack(anchor="w", pady=(2, 0))

        self.util_card = tb.Frame(row2, bootstyle="dark", padding=10)
        self.util_card.pack(side="left", fill="x", expand=True, padx=(6, 6))
        tb.Label(self.util_card, text="CPU Utilization", font=("Segoe UI", 9), bootstyle="light").pack(anchor="w")
        self.util_val = tb.Label(self.util_card, text="—", font=("Segoe UI", 16, "bold"), bootstyle="danger")
        self.util_val.pack(anchor="w", pady=(2, 0))

        self.thru_card = tb.Frame(row2, bootstyle="dark", padding=10)
        self.thru_card.pack(side="left", fill="x", expand=True, padx=(6, 0))
        tb.Label(self.thru_card, text="Throughput", font=("Segoe UI", 9), bootstyle="light").pack(anchor="w")
        self.thru_val = tb.Label(self.thru_card, text="—", font=("Segoe UI", 16, "bold"), bootstyle="secondary")
        self.thru_val.pack(anchor="w", pady=(2, 0))

        # ── Live Queue Panel (new, right column) ──
        self._build_queue_panel(right_col)

    # ---------- Live Queue Panel ----------

    def _build_queue_panel(self, parent):
        """Create the static skeleton of the live queue monitor."""
        panel = tb.Labelframe(
            parent, text=" Live Queue Monitor ",
            padding=(10, 8), bootstyle="warning"
        )
        panel.pack(fill="both", expand=True)

        # ── Current Time ──────────────────────────────────────
        tb.Label(panel, text="⏱  Current Time",
                 font=("Segoe UI", 8, "bold"), bootstyle="secondary").pack(anchor="w")
        self._panel_time_val = tb.Label(
            panel, text="—",
            font=("Segoe UI", 26, "bold"), bootstyle="warning"
        )
        self._panel_time_val.pack(anchor="w", pady=(0, 6))
        tb.Separator(panel).pack(fill="x", pady=(0, 8))

        # ── Running Process ───────────────────────────────────
        tb.Label(panel, text="▶  Running Process",
                 font=("Segoe UI", 8, "bold"), bootstyle="secondary").pack(anchor="w")
        self._panel_running_val = tb.Label(
            panel, text="—",
            font=("Segoe UI", 15, "bold"), bootstyle="secondary",
            padding=(6, 3)
        )
        self._panel_running_val.pack(anchor="w", pady=(4, 8))
        tb.Separator(panel).pack(fill="x", pady=(0, 8))

        # ── Ready Queue ───────────────────────────────────────
        tb.Label(panel, text="📋  Ready Queue",
                 font=("Segoe UI", 8, "bold"), bootstyle="secondary").pack(anchor="w")
        self._panel_queue_inner = tb.Frame(panel)
        self._panel_queue_inner.pack(fill="x", pady=(6, 8))
        tb.Label(self._panel_queue_inner, text="—",
                 font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w")
        tb.Separator(panel).pack(fill="x", pady=(0, 8))

        # ── Completed Processes ───────────────────────────────
        tb.Label(panel, text="✓  Completed",
                 font=("Segoe UI", 8, "bold"), bootstyle="secondary").pack(anchor="w")
        self._panel_completed_inner = tb.Frame(panel)
        self._panel_completed_inner.pack(fill="x", pady=(6, 0))
        tb.Label(self._panel_completed_inner, text="—",
                 font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w")

    def _reset_queue_panel(self):
        """Restore panel to its initial blank state."""
        self._panel_time_val.config(text="—")
        self._panel_running_val.config(text="—", bootstyle="secondary")
        for w in self._panel_queue_inner.winfo_children():
            w.destroy()
        tb.Label(self._panel_queue_inner, text="—",
                 font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w")
        for w in self._panel_completed_inner.winfo_children():
            w.destroy()
        tb.Label(self._panel_completed_inner, text="—",
                 font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w")

    def _update_queue_panel(self, t, running_pid, ready, completed):
        """Refresh all live-panel widgets for one animation frame."""
        # Current time
        self._panel_time_val.config(text=str(t))

        # Running process
        if running_pid:
            self._panel_running_val.config(text=running_pid, bootstyle="success")
        else:
            self._panel_running_val.config(text="CPU Idle", bootstyle="secondary")

        # Ready queue chips
        for w in self._panel_queue_inner.winfo_children():
            w.destroy()
        if ready:
            grid_frame = tb.Frame(self._panel_queue_inner)
            grid_frame.pack(fill="x")
            for idx, p in enumerate(ready):
                color = self._color_for(p["pid"])
                chip = tk.Label(
                    grid_frame,
                    text=p["pid"],
                    font=("Segoe UI", 9, "bold"),
                    bg=color, fg="#11121d",
                    padx=7, pady=3,
                    relief="flat"
                )
                chip.grid(row=idx // 3, column=idx % 3, padx=3, pady=3, sticky="w")
        else:
            tb.Label(self._panel_queue_inner, text="Empty",
                     font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w")

        # Completed list
        for w in self._panel_completed_inner.winfo_children():
            w.destroy()
        if completed:
            for p in completed:
                tb.Label(
                    self._panel_completed_inner,
                    text=f"✓  {p['pid']}",
                    font=("Segoe UI", 9),
                    bootstyle="success"
                ).pack(anchor="w", pady=1)
        else:
            tb.Label(self._panel_completed_inner, text="None yet",
                     font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w")

    # ---------- Animation ----------

    def _start_animation(self, result):
        """Cancel any in-progress animation and replay the new result."""
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None

        gantt = result.get("gantt", [])
        table = result.get("table", [])
        if not gantt or not table:
            self._reset_queue_panel()
            return

        max_time  = max(seg["end"]   for seg in gantt)
        proc_info = {p["pid"]: p for p in table}

        # Adaptive frame interval: fast for long simulations, slow for short ones
        step_ms = max(80, min(500, 5000 // max_time)) if max_time > 0 else 300

        self._anim_step(0, max_time, gantt, proc_info, step_ms)

    def _anim_step(self, t, max_time, gantt, proc_info, step_ms):
        """Execute one animation frame then schedule the next."""
        # Find which process the CPU is running at time t
        running_pid = None
        for seg in gantt:
            if seg["start"] <= t < seg["end"]:
                running_pid = seg["pid"]
                break

        # Categorise processes
        arrived        = [p for p in proc_info.values() if p["arrival"] <= t]
        completed      = [p for p in proc_info.values() if p["finish"]  <= t]
        completed_pids = {p["pid"] for p in completed}
        ready          = [
            p for p in arrived
            if p["pid"] not in completed_pids and p["pid"] != running_pid
        ]
        ready.sort(key=lambda p: (p["arrival"], p["pid"]))

        self._update_queue_panel(t, running_pid, ready, completed)

        if t < max_time:
            self._anim_id = self.after(
                step_ms,
                lambda: self._anim_step(t + 1, max_time, gantt, proc_info, step_ms)
            )
        else:
            self._anim_id = None

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
        show_priority = algo.startswith("Priority")
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
            elif algo == "SJF (Non-Preemptive)":
                result = sjf_scheduling(processes)
            elif algo == "SJF (Preemptive)":
                result = srtf_scheduling(processes)
            elif algo == "Priority (Non-Preemptive)":
                result = priority_scheduling(processes)
            elif algo == "Priority (Preemptive)":
                result = priority_preemptive_scheduling(processes)
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

    def _compare(self):
        """Read current process inputs and open the comparison window."""
        try:
            processes = self._read_processes()
            quantum = 2
            try:
                q = int(self.quantum_var.get().strip())
                if q > 0:
                    quantum = q
            except ValueError:
                pass
            CompareWindow(self, processes, quantum)
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def _color_for(self, pid):
        if pid not in self.pid_colors:
            self.pid_colors[pid] = GANTT_COLORS[len(self.pid_colors) % len(GANTT_COLORS)]
        return self.pid_colors[pid]

    def _render_result(self, result):
        # Kick off the queue animation immediately (resets panel + replays)
        self._start_animation(result)

        # Clear & fill Results Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in result["table"]:
            self.tree.insert("", "end", values=(
                r["pid"], r["arrival"], r["burst"], r["start"], r["finish"],
                r["turnaround"], r["waiting"], r["response"]
            ))

        # Update Summary Stats
        self.wait_val.config(text=f"{result['avg_waiting']:.2f} ms")
        self.turn_val.config(text=f"{result['avg_turnaround']:.2f} ms")
        self.resp_val.config(text=f"{result['avg_response']:.2f} ms")
        self.util_val.config(text=f"{result['cpu_utilization']:.2f}%")
        self.thru_val.config(text=f"{result['throughput']:.4f} p/ms")

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
