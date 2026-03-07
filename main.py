import customtkinter as ctk
from tkinter import messagebox, filedialog
import config
import minecraft_manager
import forge_manager
import os

# Load config
current_config = config.load()
minecraft_directory = current_config.get("minecraft_directory")
current_ram = current_config.get("ram", 4)
current_theme = current_config.get("theme", "dark") 

# NOVO: Aplica o tema salvo
ctk.set_appearance_mode(current_theme)

# Main window
window = ctk.CTk()
window.geometry("520x600")
window.title("Better Launcher")

# UI Variables
folder_text = ctk.StringVar(value=minecraft_directory or "No folder selected")
versions = minecraft_manager.get_versions(minecraft_directory)
selected_version = ctk.StringVar(value=versions[0] if versions else "No versions")
version_display_map = {}

# NOVO: Variável pra acompanhar o tema atual
theme_var = ctk.StringVar(value=current_theme)

# Tabs
tabs = ctk.CTkTabview(window, width=500, height=570)
tabs.pack(pady=10)

home_tab = tabs.add("Home")
versions_tab = tabs.add("Versions")
settings_tab = tabs.add("Settings")

# ========== FUNCTIONS ==========
def select_folder():
    global minecraft_directory
    folder = filedialog.askdirectory()
    if folder:
        minecraft_directory = folder
        folder_text.set(folder)
        current_config["minecraft_directory"] = folder
        config.save(current_config)
        
        # Prepare folder
        minecraft_manager.setup_folder(folder)
        
        refresh_versions()
        messagebox.showinfo("Success", "Folder prepared! Now you can install versions.")

def refresh_versions():
    global versions, version_display_map
    versions = minecraft_manager.get_versions(minecraft_directory)
    
    # Cria um dicionário: nome bonito -> id real
    version_display_map = {}
    display_list = []
    for v in versions:
        display = minecraft_manager.get_display_name(v)
        version_display_map[display] = v
        display_list.append(display)
    
    # Atualiza o menu com os nomes bonitos
    version_menu.configure(values=display_list)
    if display_list:
        selected_version.set(display_list[0])  # seleciona o primeiro

def launch_game():
    if not minecraft_directory:
        messagebox.showerror("Error", "Select a folder first!")
        return
    
    username = username_entry.get().strip()
    ram = ram_entry.get().strip()
    display_name = selected_version.get()
    version = version_display_map.get(display_name, display_name)  # Pega o ID real
    
    if version == "No versions" or display_name == "No versions":
        messagebox.showerror("Error", "No version installed!")
        return
    
    # Verifica se a versão realmente existe
    version_dir = os.path.join(minecraft_directory, "versions", version)
    json_file = os.path.join(version_dir, f"{version}.json")
    if not os.path.exists(json_file):
        messagebox.showerror("Error", f"Version {version} is missing its JSON file. Try reinstalling.")
        return
    
    if not username or not ram.isdigit():
        messagebox.showerror("Error", "Username and RAM are required!")
        return
    
    ram_int = int(ram)
    if ram_int < 1 or ram_int > 32:
        messagebox.showerror("Error", "RAM must be between 1 and 32!")
        return
    
    current_config["ram"] = ram_int
    config.save(current_config)
    
    window.destroy()
    minecraft_manager.launch(minecraft_directory, username, ram_int, version)

def open_install_window():
    if not minecraft_directory:
        messagebox.showerror("Error", "Select a folder first!")
        return
    
    install_window = ctk.CTkToplevel(window)
    install_window.geometry("300x150")
    install_window.title("Install Version")
    
    def on_closing():
        try:
            install_window.destroy()
        except:
            pass
    
    install_window.protocol("WM_DELETE_WINDOW", on_closing)
    
    ctk.CTkLabel(install_window, text="Version (ex: 1.8.9):").pack(pady=10)
    version_entry = ctk.CTkEntry(install_window)
    version_entry.pack(pady=5)
    
    def install_click():
        version = version_entry.get().strip()
        if not version:
            messagebox.showerror("Error", "Enter a version!")
            return
        
        def on_success(v):
            try:
                install_window.destroy()
                refresh_versions()
                messagebox.showinfo("Success", f"Version {v} installed!")
            except:
                refresh_versions()
                messagebox.showinfo("Success", f"Version {v} installed!")
        
        def on_error(e):
            try:
                messagebox.showerror("Error", f"Failed: {e}")
            except:
                pass
        
        minecraft_manager.install(minecraft_directory, version, on_success, on_error)
        messagebox.showinfo("Installing", "Installation started!")
    
    ctk.CTkButton(install_window, text="Install", command=install_click).pack(pady=10)

def toggle_theme():
    """Alterna entre dark e light mode e salva na config"""
    new_theme = "light" if theme_var.get() == "dark" else "dark"
    theme_var.set(new_theme)
    
    # Aplica o novo tema
    ctk.set_appearance_mode(new_theme)
    
    # Salva na configuração
    current_config["theme"] = new_theme
    config.save(current_config)
    
    # Atualiza texto do botão
    theme_button.configure(text=f"Switch to {'Dark' if new_theme == 'light' else 'Light'} Mode")

# ---------- Forge Functions ----------
def install_forge_for_current_version():
    """Instala Forge para a versão selecionada no menu"""
    if not minecraft_directory:
        messagebox.showerror("Error", "Select a folder first!")
        return
    
    version = selected_version.get()
    if version == "No versions":
        messagebox.showerror("Error", "Select a Minecraft version first!")
        return
    
    # Pergunta confirmação
    result = messagebox.askyesno(
        "Install Forge",
        f"This will install Forge for Minecraft {version}.\n\nContinue?"
    )
    if not result:
        return
    
    # Desabilita botão durante instalação
    install_forge_button.configure(state="disabled", text="Installing...")
    
    # CORREÇÃO: callback como DICIONÁRIO, não função
    forge_callback = {
        "setStatus": lambda status: print(f"Status: {status}"),
        "setProgress": lambda progress: print(f"Progress: {progress}%"),
        "setMax": lambda max_val: print(f"Max: {max_val}")
    }
    
    def install_thread():
        success, msg, forge_version = forge_manager.install_forge(
            minecraft_directory, 
            version,
            callback=forge_callback  # Agora passa o dicionário
        )
        
        # Volta pra thread principal pra atualizar UI
        window.after(0, lambda: install_finished(success, msg, forge_version))
    
    def install_finished(success, msg, forge_version):
        install_forge_button.configure(state="normal", text="Install Forge")
        if success:
            messagebox.showinfo("Success", msg)
            refresh_versions()
            refresh_forge_list()
        else:
            messagebox.showerror("Error", msg)
    
    import threading
    threading.Thread(target=install_thread).start()

def refresh_forge_list():
    """Atualiza a lista de Forge instalados na aba Mods"""
    if not minecraft_directory:
        return
    installed = minecraft_manager.get_versions(minecraft_directory)
    forge_versions = [v for v in installed if "forge" in v.lower()]
    if forge_versions:
        text = "\n".join([f"• {v}" for v in forge_versions])
    else:
        text = "No Forge versions installed"
    forge_list_label.configure(text=text)

# ========== HOME TAB ==========
ctk.CTkLabel(home_tab, text="Better Launcher", font=("Arial", 24, "bold")).pack(pady=15)

ctk.CTkLabel(home_tab, text="Username:").pack()
username_entry = ctk.CTkEntry(home_tab, placeholder_text="Enter your username")
username_entry.pack(pady=5)

ctk.CTkLabel(home_tab, text="Version:").pack()
version_menu = ctk.CTkOptionMenu(home_tab, variable=selected_version, values=versions)
version_menu.pack(pady=5)

ctk.CTkLabel(home_tab, text="RAM (GB):").pack()
ram_entry = ctk.CTkEntry(home_tab, placeholder_text="2")
ram_entry.pack(pady=5)
ram_entry.insert(0, str(current_ram))

ctk.CTkButton(home_tab, text="▶ PLAY", command=launch_game, fg_color="#2e7d32", height=40, font=("Arial", 14, "bold")).pack(pady=20)

# ========== VERSIONS TAB ==========
ctk.CTkLabel(versions_tab, text="Manage Versions", font=("Arial", 18, "bold")).pack(pady=20)
ctk.CTkButton(versions_tab, text="📥 Install New Version", command=open_install_window, height=35).pack(pady=10)

# ========== SETTINGS TAB ==========
ctk.CTkLabel(settings_tab, text="Settings", font=("Arial", 18, "bold")).pack(pady=20)

# Folder selection
ctk.CTkLabel(settings_tab, text="Minecraft Folder:").pack()
folder_label = ctk.CTkLabel(settings_tab, textvariable=folder_text, wraplength=400, fg_color=("gray75", "gray25"), corner_radius=6, padx=10, pady=5)
folder_label.pack(pady=5)
ctk.CTkButton(settings_tab, text="📁 Choose Folder", command=select_folder).pack(pady=10)

# Theme selection
ctk.CTkLabel(settings_tab, text="Appearance:").pack(pady=(20,5))
theme_button = ctk.CTkButton(
    settings_tab, 
    text=f"Switch to {'Dark' if current_theme == 'light' else 'Light'} Mode",
    command=toggle_theme,
    width=200
)
theme_button.pack(pady=5)

# ========== MODS TAB (com Forge) ==========
mods_tab = tabs.add("Mods")

# Frame do Forge
forge_frame = ctk.CTkFrame(mods_tab)
forge_frame.pack(pady=10, padx=10, fill="x")

ctk.CTkLabel(forge_frame, text="Forge Installer", font=("Arial", 16, "bold")).pack(pady=5)
ctk.CTkLabel(forge_frame, text="Install Forge to use mods", font=("Arial", 12)).pack()

# Botão de instalar Forge (referência global pra poder desabilitar)
install_forge_button = ctk.CTkButton(
    forge_frame, 
    text="⚙️ Install Forge for selected version", 
    command=install_forge_for_current_version
)
install_forge_button.pack(pady=10)

# Lista de Forge instalados
ctk.CTkLabel(forge_frame, text="Installed Forge versions:").pack()
forge_list_label = ctk.CTkLabel(forge_frame, text="No Forge installed", wraplength=400)
forge_list_label.pack(pady=5)

# Frame de Mods (básico por enquanto)
mods_frame = ctk.CTkFrame(mods_tab)
mods_frame.pack(pady=10, padx=10, fill="both", expand=True)

ctk.CTkLabel(mods_frame, text="Mods Manager", font=("Arial", 16, "bold")).pack(pady=5)
ctk.CTkLabel(mods_frame, text="Coming soon...", font=("Arial", 12)).pack(pady=20)

# Atualiza lista ao iniciar
refresh_forge_list()

# Shows actual theme
theme_status = ctk.CTkLabel(settings_tab, text=f"Current: {current_theme.title()} Mode", text_color=("gray", "white"))
theme_status.pack(pady=5)

# Start
refresh_versions()
window.mainloop()
