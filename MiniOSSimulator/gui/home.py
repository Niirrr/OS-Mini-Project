import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox


class HomePage(tb.Frame):
    """Landing page with modern dashboard navigation to each simulator module."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Main wrapper with padding
        wrapper = tb.Frame(self)
        wrapper.pack(fill=BOTH, expand=YES, padx=40, pady=40)

        # Header Section
        header_frame = tb.Frame(wrapper)
        header_frame.pack(fill=X, pady=(20, 30))

        title = tb.Label(
            header_frame,
            text="💻 Mini OS Simulator",
            font=("Segoe UI", 32, "bold"),
            bootstyle="light"
        )
        title.pack(anchor=CENTER)

        subtitle = tb.Label(
            header_frame,
            text="An interactive visual environment for operating system concepts",
            font=("Segoe UI", 13),
            bootstyle="secondary"
        )
        subtitle.pack(anchor=CENTER, pady=(10, 0))

        # Grid Container for the 4 modules
        grid_frame = tb.Frame(wrapper)
        grid_frame.pack(fill=BOTH, expand=YES, pady=10)

        # Configure columns and rows for 2x2 grid
        grid_frame.columnconfigure(0, weight=1, uniform="equal")
        grid_frame.columnconfigure(1, weight=1, uniform="equal")
        grid_frame.rowconfigure(0, weight=1, uniform="equal")
        grid_frame.rowconfigure(1, weight=1, uniform="equal")

        # Define modules data
        modules = [
            {
                "title": "⚙️  CPU Scheduling",
                "desc": "Simulate and visualize CPU scheduling algorithms including FCFS, SJF, Priority, and Round Robin. Detailed statistics and dynamic Gantt chart visualization.",
                "action_text": "Launch Simulator",
                "bootstyle": "primary",
                "active": True,
                "command": lambda: controller.show_frame("CPUPage")
            },
            {
                "title": "🧱  Memory Management",
                "desc": "Simulate memory allocation policies (First Fit, Best Fit, Worst Fit) and page replacement policies (FIFO, LRU, Optimal). Under active development.",
                "action_text": "Coming Soon",
                "bootstyle": "secondary",
                "active": False,
                "command": lambda: messagebox.showinfo("Coming Soon", "Memory Management module is currently in development!")
            },
            {
                "title": "💽  Disk Scheduling",
                "desc": "Simulate and compare disk head movement algorithms including FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK. Under active development.",
                "action_text": "Coming Soon",
                "bootstyle": "secondary",
                "active": False,
                "command": lambda: messagebox.showinfo("Coming Soon", "Disk Scheduling module is currently in development!")
            },
            {
                "title": "📁  File Management",
                "desc": "Simulate directory structures (single-level, two-level, tree-structured) and file allocation methods (contiguous, linked, indexed). Under active development.",
                "action_text": "Coming Soon",
                "bootstyle": "secondary",
                "active": False,
                "command": lambda: messagebox.showinfo("Coming Soon", "File Management module is currently in development!")
            }
        ]

        # Draw cards
        for i, mod in enumerate(modules):
            row = i // 2
            col = i % 2

            # Use Labelframe or Frame as card container
            card = tb.Labelframe(
                grid_frame,
                text=f"  {mod['title']}  ",
                bootstyle="primary" if mod["active"] else "dark",
                padding=20
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

            # Description
            desc_lbl = tb.Label(
                card,
                text=mod["desc"],
                font=("Segoe UI", 10),
                wraplength=380,
                bootstyle="light" if mod["active"] else "secondary",
                justify=LEFT
            )
            desc_lbl.pack(fill=BOTH, expand=YES, pady=(0, 15))

            # Launch/Coming Soon Button
            btn = tb.Button(
                card,
                text=mod["action_text"],
                command=mod["command"],
                bootstyle=mod["bootstyle"] if mod["active"] else "outline-secondary",
                cursor="hand2" if mod["active"] else "arrow"
            )
            btn.pack(fill=X, side=BOTTOM)

        # Footer Section
        footer = tb.Label(
            wrapper,
            text="Kathmandu University · Department of Computer Science & Engineering",
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        footer.pack(side=BOTTOM, pady=(20, 0))
