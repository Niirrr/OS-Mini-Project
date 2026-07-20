"""
gui/compare.py
──────────────
CompareWindow – a self-contained Toplevel that runs every scheduling
algorithm on the same process set and displays:
  • A metrics table  (with the best row highlighted in green)
  • Two embedded bar charts  (avg waiting time / avg turnaround time)

No existing files are modified; this module is only imported by cpu.py.
"""

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from algorithms.fcfs     import fcfs_scheduling
from algorithms.sjf      import sjf_scheduling
from algorithms.srtf     import srtf_scheduling
from algorithms.priority import priority_scheduling
from algorithms.priority_preemptive import priority_preemptive_scheduling
from algorithms.rr       import rr_scheduling


# ── colour palette (aligned with the "darkly" ttkbootstrap theme) ────────
_BG_ROW   = "#1e2030"
_BG_BEST  = "#1a3a1e"
_FG_BEST  = "#a6e3a1"
_BAR_COLS = ["#89b4fa", "#f38ba8", "#a6e3a1", "#f9e2af", "#cba6f7", "#fab387"]

# ── algorithm registry ───────────────────────────────────────────────────
_ALGORITHMS = [
    ("FCFS",                 lambda p, q: fcfs_scheduling(p)),
    ("SJF (Non-Preemptive)", lambda p, q: sjf_scheduling(p)),
    ("SRTF",                 lambda p, q: srtf_scheduling(p)),
    ("Priority (Non-Prem.)", lambda p, q: priority_scheduling(p)),
    ("Priority (Preempt.)",  lambda p, q: priority_preemptive_scheduling(p)),
    ("Round Robin",          lambda p, q: rr_scheduling(p, q)),
]


# ════════════════════════════════════════════════════════════════════════
class CompareWindow(tb.Toplevel):
    """
    Popup comparison window.

    Parameters
    ----------
    parent    : tk widget  – the widget that owns this popup
    processes : list[dict] – same format fed to individual algorithms
    quantum   : int        – time-quantum used for Round Robin
    """

    def __init__(self, parent, processes: list, quantum: int = 2):
        super().__init__(parent)
        self.title("Algorithm Comparison")
        self.geometry("1060x680")
        self.minsize(860, 560)
        self.resizable(True, True)

        self._results = self._run_all(processes, quantum)
        self._build_ui()

    # ── algorithm runner ────────────────────────────────────────────────

    def _run_all(self, processes: list, quantum: int) -> list:
        """Run all registered algorithms; silently skip any that raise."""
        out = []
        for name, fn in _ALGORITHMS:
            try:
                r = fn(processes, quantum)
                out.append({
                    "name":            name,
                    "avg_waiting":     r["avg_waiting"],
                    "avg_turnaround":  r["avg_turnaround"],
                    "avg_response":    r["avg_response"],
                    "cpu_utilization": r["cpu_utilization"],
                    "throughput":      r["throughput"],
                })
            except Exception:
                pass   # skip gracefully if algorithm cannot handle this input
        return out

    # ── UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────
        hdr = tb.Frame(self, padding=(22, 14, 22, 6))
        hdr.pack(fill="x")

        tb.Label(
            hdr, text="Algorithm Comparison",
            font=("Segoe UI", 18, "bold"), bootstyle="light"
        ).pack(side="left")

        tb.Label(
            hdr,
            text="All six algorithms evaluated on identical process inputs   ·   ★ = lowest avg waiting time",
            font=("Segoe UI", 9), foreground="#a6adc8"
        ).pack(side="left", padx=16, pady=(5, 0))

        tb.Separator(self).pack(fill="x", padx=20, pady=(2, 0))

        # ── Metrics table ────────────────────────────────────────────────
        tbl_card = tb.Labelframe(
            self, text=" Metrics Summary ", padding=10, bootstyle="info"
        )
        tbl_card.pack(fill="x", padx=20, pady=(10, 8))
        self._build_table(tbl_card)

        # ── Bar charts ───────────────────────────────────────────────────
        chart_card = tb.Labelframe(
            self, text=" Visual Comparison ", padding=12, bootstyle="primary"
        )
        chart_card.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self._build_charts(chart_card)

    # ── metrics table ───────────────────────────────────────────────────

    def _build_table(self, parent):
        cols     = ("algorithm", "avg_wait", "avg_tat", "avg_resp", "cpu_util", "throughput")
        headings = [
            "Algorithm", "Avg Wait (ms)", "Avg Turnaround (ms)",
            "Avg Response (ms)", "CPU Util (%)", "Throughput (p/ms)"
        ]
        widths   = [200, 120, 165, 155, 115, 145]

        frm = tb.Frame(parent)
        frm.pack(fill="x")

        tree = tb.Treeview(
            frm, columns=cols, show="headings",
            height=len(self._results), bootstyle="info"
        )
        tree.pack(side="left", fill="x", expand=True)

        sb = tb.Scrollbar(frm, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        for c, h, w in zip(cols, headings, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="center", minwidth=80)

        # Row styling
        tree.tag_configure("best",   background=_BG_BEST, foreground=_FG_BEST)
        tree.tag_configure("normal", background=_BG_ROW)

        best_idx = (
            min(range(len(self._results)),
                key=lambda i: self._results[i]["avg_waiting"])
            if self._results else -1
        )

        for i, r in enumerate(self._results):
            is_best  = (i == best_idx)
            tag      = "best" if is_best else "normal"
            disp_name = ("★ " + r["name"]) if is_best else r["name"]
            tree.insert("", "end", tags=(tag,), values=(
                disp_name,
                f"{r['avg_waiting']:.2f}",
                f"{r['avg_turnaround']:.2f}",
                f"{r['avg_response']:.2f}",
                f"{r['cpu_utilization']:.2f}",
                f"{r['throughput']:.4f}",
            ))

    # ── bar charts ──────────────────────────────────────────────────────

    def _build_charts(self, parent):
        # Lazy-import matplotlib so the rest of the app still works
        # even if matplotlib is missing (shows a friendly message instead).
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            tb.Label(
                parent,
                text="matplotlib is not installed.\n"
                     "Run:   uv pip install matplotlib   then restart the simulator.",
                font=("Segoe UI", 11), bootstyle="warning"
            ).pack(expand=True)
            return

        if not self._results:
            tb.Label(parent, text="No results to chart.",
                     bootstyle="secondary").pack(expand=True)
            return

        names     = [r["name"] for r in self._results]
        wait_vals = [r["avg_waiting"]    for r in self._results]
        tat_vals  = [r["avg_turnaround"] for r in self._results]
        colors    = _BAR_COLS[:len(names)]

        # Shorten long names for x-axis ticks
        tick_labels = [
            n.replace(" (Non-Preemptive)", "\n(Non-Preemptive)")
             .replace("Round Robin",       "Round\nRobin")
             .replace("Priority (Non-Prem.)", "Priority\n(Non-Prem.)")
             .replace("Priority (Preempt.)", "Priority\n(Preempt.)")
            for n in names
        ]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.8, 3.6))
        fig.patch.set_facecolor("#1e2030")

        def _draw(ax, vals, title, ylabel):
            ax.set_facecolor("#181825")
            bars = ax.bar(
                range(len(names)), vals,
                color=colors, edgecolor="#11121d",
                linewidth=1.3, width=0.55
            )
            ax.set_title(title, color="#cdd6f4",
                         fontsize=10, fontweight="bold", pad=8)
            ax.set_xticks(range(len(names)))
            ax.set_xticklabels(tick_labels, color="#a6adc8", fontsize=7.5)
            ax.set_ylabel(ylabel, color="#a6adc8", fontsize=8.5)
            ax.tick_params(axis="y", colors="#a6adc8", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#313244")
            ax.set_axisbelow(True)
            ax.yaxis.grid(True, color="#313244", linewidth=0.7, linestyle="--")

            cap = max(vals) if vals else 1
            for bar, val in zip(bars, vals):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + cap * 0.025,
                    f"{val:.2f}",
                    ha="center", va="bottom",
                    color="#cdd6f4", fontsize=8, fontweight="bold"
                )

        _draw(ax1, wait_vals, "Average Waiting Time",    "Time (ms)")
        _draw(ax2, tat_vals,  "Average Turnaround Time", "Time (ms)")

        fig.tight_layout(pad=1.8)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
