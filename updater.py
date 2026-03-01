import requests
import tkinter as tk
from tkinter import messagebox
import webbrowser
import os

# --- CONFIGURATION ---
# Replace this with YOUR actual Raw URL from Step 1
VERSION_URL = "https://raw.githubusercontent.com/NIcepacific/PDF-Master-Suite/refs/heads/main/version.json"
CURRENT_VERSION = "2.0.0" 

def check_for_updates(silent=False):
    """
    Checks GitHub for a newer version.
    If silent=True, it won't show a 'You are up to date' message (good for startup).
    """
    try:
        response = requests.get(VERSION_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            remote_version = data.get("version", "2.0.0")
            # Updated username based on VERSION_URL
            download_page = "https://github.com/NIcepacific/PDF-Master-Suite/releases"

            if remote_version > CURRENT_VERSION:
                # If an update is found, ask the user
                answer = messagebox.askyesno(
                    "Update Available", 
                    f"A new version ({remote_version}) is available!\n\nWould you like to go to the download page?"
                )
                if answer:
                    webbrowser.open(download_page)
            else:
                if not silent:
                    messagebox.showinfo("Update Check", f"You are using the latest version ({CURRENT_VERSION}).")
        else:
            if not silent:
                messagebox.showerror("Error", "Could not reach the update server.")
    except Exception as e:
        if not silent:
            messagebox.showerror("Update Error", f"An error occurred: {e}")