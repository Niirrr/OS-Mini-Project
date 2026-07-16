import ttkbootstrap as tb
from gui.home import HomePage
from gui.cpu import CPUPage


class MiniOSSimulatorApp(tb.Window):
    def __init__(self):
        super().__init__(
            title="Mini OS Simulator",
            themename="darkly",
            size=(1050, 750),
            minsize=(900, 680)
        )

        container = tb.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for PageClass in (HomePage, CPUPage):
            page_name = PageClass.__name__
            frame = PageClass(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        # Call refresh method if page needs to update layout on show
        if hasattr(frame, "on_show"):
            frame.on_show()


if __name__ == "__main__":
    app = MiniOSSimulatorApp()
    app.mainloop()

