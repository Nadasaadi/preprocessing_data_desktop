import tkinter as tk
from auth_window import AuthWindow

def main():
    root = tk.Tk()
    app = AuthWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
