import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import os


from organizer import run_organizer

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

BLOCKED_PATHS = [
    "C:/Windows",
    "C:/Program Files",
    "C:/Program Files (x86)",
    "C:/System32",
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\System32",
]

#checks if destination is safe
def is_safe_path(folder):
    if not os.path.exists(folder):
        return False, "Selected folder does not exist."
    
    for blocked in BLOCKED_PATHS:
        if os.path.normpath(folder).startswith(os.path.normpath(blocked)):
            return False, f"Cannot organize system directory: {blocked}"
        
    return True, ""

#confirmation dialog
def show_confirmation(folder):
    dialog = ctk.CTkToplevel(root)
    dialog.title("Confirm")
    dialog.geometry("400x150")
    dialog.grab_set() #blocks interaction with main window until closed

    confirmed = tk.BooleanVar(value=False)

    ctk.CTkLabel(dialog, text=f"Organize files in:\n{folder}", wraplength=360).pack(pady=20)

    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack()

    ctk.CTkButton(btn_frame, text="Cancel", fg_color="gray", command=dialog.destroy).pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text="Confirm", command=lambda: [confirmed.set(True), dialog.destroy()]).pack(side="left", padx=10)

    dialog.wait_window() #wait for dialog to close
    return confirmed.get()

#function to start organizer in a separate thread
def start_organizer():
    folder = folder_var.get()
    if not folder:
        log_box.insert(ctk.END, "Please select a folder to organize.\n")
        return

    safe, reason = is_safe_path(folder)
    if not safe:
        log_box.insert("end", f"Error: {reason}\n")
        return
    
    if not show_confirmation(folder):
        return

    #clear previous run
    log_box.configure(state="normal")
    log_box.delete(1.0, ctk.END)
    log_box.configure(state="disabled")

    summary_box.configure(state="normal")
    summary_box.delete(1.0, ctk.END)
    summary_box.configure(state="disabled")

    organize_btn.configure(state="disabled")
    save_btn.configure(state="disabled")
    progress_bar.start()

    def run():
        def log_callback(msg):
            log_box.configure(state="normal")
            log_box.insert(ctk.END, msg + "\n")
            log_box.see(ctk.END)
            log_box.configure(state="disabled")

        summary = run_organizer(folder, log_callback)

        summary_box.configure(state="normal")
        summary_box.insert(ctk.END, summary)
        summary_box.configure(state="disabled")

        progress_bar.stop()
        organize_btn.configure(state="normal")
        save_btn.configure(state="normal")

    threading.Thread(target=run, daemon=True).start()

#window setup
root = ctk.CTk()
root.title("File Organizer")
root.geometry("650x620")
root.resizable(False, False)

#folder input row
folder_var = ctk.StringVar()

ctk.CTkLabel(root, text="Target Folder:").pack(anchor="w", padx=20, pady=(20, 0))

input_frame = ctk.CTkFrame(root, fg_color="transparent")
input_frame.pack(fill="x", padx=20)

ctk.CTkEntry(input_frame, textvariable=folder_var, width=480).pack(side="left", expand=True, fill="x")
ctk.CTkButton(input_frame, text="Browse", width=80, command=browse_folder).pack(side="left", padx=(10, 0))

#organize button
organize_btn = ctk.CTkButton(root, text="Organize Files", command=start_organizer)
organize_btn.pack(pady=15)
root.bind("<Return>", lambda event: start_organizer())  #bind Enter key to start

#progress bar
progress_bar = ctk.CTkProgressBar(root, mode="indeterminate")
progress_bar.pack(fill="x", padx=20, pady=(0, 10))

#log box
ctk.CTkLabel(root, text="Activity Log:").pack(anchor="w", padx=20)
log_box = ctk.CTkTextbox(root, height=200, font=("Courier", 12), fg_color="#0a0a0a", text_color="#00ff00", state="disabled")
log_box.pack(fill="x", padx=20)

#summary area
ctk.CTkLabel(root, text="Summary:").pack(anchor="w", padx=20, pady=(15, 0))
summary_box = ctk.CTkTextbox(root, height=120, font=("Courier", 12), state="disabled")
summary_box.pack(fill="x", padx=20, pady=(0, 20))

#function to save log and summary to a text file
def save_log():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt")],
        initialfile="organizer_log.txt"
    )

    if file_path:
        with open(file_path, "w") as f:
            f.write("ACTIVITY LOG:\n")
            f.write(log_box.get("1.0", "end"))
            f.write("\n\nSUMMARY:\n")
            f.write(summary_box.get("1.0", "end"))

#save button
save_btn = ctk.CTkButton(root, text="Save Log", command=save_log, state="disabled")
save_btn.pack(pady=(0, 10))

root.mainloop()