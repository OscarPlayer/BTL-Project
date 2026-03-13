import os
import minecraft_launcher_lib
import json

def setup_minecraft_folder(chosen_folder):
    """
    Prepares the Minecraft folder with everything it needs
    """
    print(f"Preparing folder: {chosen_folder}")
    
    # Creates the necessary folder structure
    folders = [
        "versions",
        "libraries", 
        "assets",
        "natives",
        "crash-reports",
        "logs",
        "mods",  # for when you add mods
        "resourcepacks",
        "saves",
        "screenshots"
    ]
    
    for folder in folders:
        path = os.path.join(chosen_folder, folder)
        os.makedirs(path, exist_ok=True)
        print(f"  ✓ Created: {folder}")
    
    # Creates a basic launcher configuration file
    launcher_config = {
        "launcher_name": "Better Launcher",
        "launcher_version": "1.0.0",
        "minecraft_directory": chosen_folder
    }
    
    with open(os.path.join(chosen_folder, "launcher_profiles.json"), "w") as f:
        json.dump(launcher_config, f, indent=2)
    
    print("\n✅ Folder prepared successfully!")
    return True

# If you run this file directly
if __name__ == "__main__":
    from tkinter import filedialog
    import tkinter as tk
    
    root = tk.Tk()
    root.withdraw()  # Hides the main window
    
    folder = filedialog.askdirectory(title="Select your launcher folder")
    if folder:
        setup_minecraft_folder(folder)
        input("\nPress Enter to exit...")