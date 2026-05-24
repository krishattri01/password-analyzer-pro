import tkinter as tk
from gui.app import PasswordAnalyzerApp

if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordAnalyzerApp(root)
    root.mainloop()