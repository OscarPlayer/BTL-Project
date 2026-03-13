import customtkinter as ctk
from tkinter import messagebox, filedialog
import config
import minecraft_manager
import forge_manager
import fabric_manager
import skins_manager
import os
import sys
import threading
from datetime import datetime
from CTkToolTip import CTkToolTip

# ---------- Animated Button Class ----------
class AnimatedButton(ctk.CTkButton):
    """Botão com efeito de borda animada ao passar o mouse."""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.default_border_color = self.cget("border_color") or "transparent"
        self.default_border_width = self.cget("border_width") or 0
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.configure(border_width=2, border_color="white")

    def on_leave(self, event):
        self.configure(border_width=self.default_border_width, border_color=self.default_border_color)

# ---------- Config ----------
current_config = config.load()
minecraft_directory = current_config.get("minecraft_directory")
current_ram = current_config.get("ram", 4)
current_theme = current_config.get("theme", "dark")
last_username = current_config.get("last_username", "")
last_version = current_config.get("last_version", "")

ctk.set_appearance_mode(current_theme)

# ---------- Window ----------
window = ctk.CTk()
window.geometry("800x600")
window.minsize(520, 600)
window.title("Better Launcher")

# ---------- Ícone da Janela ----------
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

icon_path = os.path.join(base_path, "icon.ico")

try:
    if os.path.exists(icon_path):
        window.iconbitmap(icon_path)  # Define o ícone da janela
    else:
        print("Arquivo de ícone não encontrado.")
except Exception as e:
    print(f"Erro ao carregar ícone: {e}")

# ---------- Variables ----------
folder_text = ctk.StringVar(value=minecraft_directory or "No folder selected")
versions = minecraft_manager.get_versions(minecraft_directory)
selected_version = ctk.StringVar(value=versions[0] if versions else "No versions")
version_display_map = {}
theme_var = ctk.StringVar(value=current_theme)

# ---------- Tabs ----------
tabs = ctk.CTkTabview(window, width=500, height=570)
tabs.pack(pady=10, padx=10, fill="both", expand=True)
home_tab = tabs.add("🏠 Home")
settings_tab = tabs.add("⚙️ Settings")
versions_tab = tabs.add("📦 Versions")
mods_tab = tabs.add("🧩 Mods")
skins_tab = tabs.add("🎨 Skin")
console_tab = tabs.add("📋 Console")

# ---------- Globais para textboxes (serão definidas na UI) ----------
forge_list_textbox = None
fabric_list_textbox = None

# ========== FUNCTIONS ==========

# ---------- Console ----------
def log_message(message, level="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {"success": "✅", "error": "❌", "forge": "⚙️", "fabric": "🔷"}.get(level, "ℹ️")
    formatted = f"[{timestamp}] {prefix} {message}\n"
    console_text.configure(state="normal")
    console_text.insert("end", formatted)
    console_text.see("end")
    console_text.configure(state="disabled")

def clear_console():
    console_text.configure(state="normal")
    console_text.delete("1.0", "end")
    console_text.configure(state="disabled")

# ---------- Folder ----------
def select_folder():
    global minecraft_directory
    folder = filedialog.askdirectory()
    if folder:
        minecraft_directory = folder
        folder_text.set(folder)
        current_config["minecraft_directory"] = folder
        config.save(current_config)
        minecraft_manager.setup_folder(folder)
        refresh_versions()
        messagebox.showinfo("Success", "Folder prepared! Now you can install versions.")

# ---------- Versions ----------
def refresh_versions():
    global versions, version_display_map
    versions = minecraft_manager.get_versions(minecraft_directory)
    version_display_map = {}
    display_list = []
    for v in versions:
        display = minecraft_manager.get_display_name(v)
        version_display_map[display] = v
        display_list.append(display)
    version_menu.configure(values=display_list)
    if display_list:
        if last_version and last_version in versions:
            for disp, vid in version_display_map.items():
                if vid == last_version:
                    selected_version.set(disp)
                    break
        else:
            selected_version.set(display_list[0])

def launch_game():
    if not minecraft_directory:
        messagebox.showerror("Error", "Select a folder first!")
        return
    username = username_entry.get().strip()
    ram = ram_entry.get().strip()
    display_name = selected_version.get()
    version = version_display_map.get(display_name, display_name)
    if version == "No versions" or display_name == "No versions":
        messagebox.showerror("Error", "No version installed!")
        return
    version_dir = os.path.join(minecraft_directory, "versions", version)
    if not os.path.exists(os.path.join(version_dir, f"{version}.json")):
        messagebox.showerror("Error", f"Version {version} is missing its JSON file.")
        return
    if not username or not ram.isdigit():
        messagebox.showerror("Error", "Username and RAM are required!")
        return
    current_config["last_username"] = username
    ram_int = int(ram)
    if ram_int < 1 or ram_int > 32:
        messagebox.showerror("Error", "RAM must be between 1 and 32!")
        return
    current_config["ram"] = ram_int
    current_config["last_version"] = version
    config.save(current_config)
    # Verifica se deve manter o launcher aberto (opção futura)
    window.destroy()
    minecraft_manager.launch(minecraft_directory, username, ram_int, version)

def update_versions_list():
    versions_listbox.delete("0.0", "end")
    for v in versions:
        versions_listbox.insert("end", v + "\n")

def install_version_from_entry():
    version = version_entry.get().strip()
    if not version:
        messagebox.showerror("Error", "Enter a version!")
        return
    
    log_message(f"Starting installation of Minecraft {version}", "info")
    install_version_button.configure(state="disabled", text="Installing...")
    version_status.set(f"Installing {version}...")
    
    def progress_callback(status, level="info"):
        log_message(f"Minecraft: {status}", level)
    
    def on_success(v):
        log_message(f"Version {v} installed successfully!", "success")
        install_version_button.configure(state="normal", text="📥 Install")
        version_status.set(f"✅ Version {v} installed!")
        version_entry.delete(0, "end")
        refresh_versions()
        update_versions_list()
        messagebox.showinfo("Success", f"Version {v} installed!")
    
    def on_error(e):
        log_message(f"Error installing {version}: {e}", "error")
        install_version_button.configure(state="normal", text="📥 Install")
        version_status.set(f"❌ Error: {e[:50]}...")
        messagebox.showerror("Error", f"Failed: {e}")
    
    minecraft_manager.install(
        minecraft_directory, 
        version, 
        on_success, 
        on_error, 
        progress_callback=progress_callback
    )

def delete_current_version():
    if not minecraft_directory:
        messagebox.showerror("Error", "Select a folder first!")
        return
    display_name = selected_version.get()
    version_id = version_display_map.get(display_name, display_name)
    if version_id == "No versions" or display_name == "No versions":
        messagebox.showerror("Error", "No version selected!")
        return
    if not messagebox.askyesno("Confirm Deletion", f"Delete {display_name}?"):
        return
    log_message(f"Deleting version {display_name}...", "info")
    delete_button.configure(state="disabled", text="Deleting...")
    def delete_thread():
        success, msg = minecraft_manager.delete_version(minecraft_directory, version_id)
        window.after(0, lambda: delete_finished(success, msg))
    def delete_finished(success, msg):
        delete_button.configure(state="normal", text="🗑️ Delete Selected")
        if success:
            log_message(f"Version {display_name} deleted.", "success")
            refresh_versions()
            update_versions_list()
            messagebox.showinfo("Success", msg)
        else:
            log_message(f"Failed to delete {display_name}: {msg}", "error")
            messagebox.showerror("Error", msg)
    threading.Thread(target=delete_thread).start()

# ---------- Theme ----------
def toggle_theme():
    new_theme = "light" if theme_var.get() == "dark" else "dark"
    theme_var.set(new_theme)
    ctk.set_appearance_mode(new_theme)
    current_config["theme"] = new_theme
    config.save(current_config)
    icon = "☀️" if new_theme == "light" else "🌙"
    theme_button.configure(text=f"{icon} Switch to {'Dark' if new_theme == 'light' else 'Light'} Mode")

# ---------- Forge ----------
def install_forge_for_current_version():
    if not minecraft_directory:
        messagebox.showerror("Error", "Select a folder first!")
        return
    version = selected_version.get()
    if version == "No versions":
        messagebox.showerror("Error", "Select a Minecraft version first!")
        return
    log_message(f"Starting Forge installation for Minecraft {version}", "forge")
    if not messagebox.askyesno("Install Forge", f"Install Forge for Minecraft {version}?"):
        log_message("Forge installation cancelled", "info")
        return
    install_forge_button.configure(state="disabled", text="Installing...")
    forge_callback = {
        "setStatus": lambda s: log_message(f"Forge: {s}", "forge"),
        "setProgress": lambda p: None,
        "setMax": lambda m: None
    }
    def install_thread():
        success, msg, fv = forge_manager.install_forge(minecraft_directory, version, callback=forge_callback)
        window.after(0, lambda: install_finished(success, msg, fv))
    def install_finished(success, msg, fv):
        install_forge_button.configure(state="normal", text="⚙️ Install Forge")
        if success:
            log_message(f"Forge installed: {msg}", "success")
            messagebox.showinfo("Success", msg)
            refresh_versions()
            refresh_forge_list()
        else:
            log_message(f"Forge installation failed: {msg}", "error")
            messagebox.showerror("Error", msg)
    threading.Thread(target=install_thread).start()

def refresh_forge_list():
    global forge_list_textbox
    if not minecraft_directory or forge_list_textbox is None:
        return
    installed = minecraft_manager.get_versions(minecraft_directory)
    forge_versions = [v for v in installed if "forge" in v.lower()]
    forge_list_textbox.configure(state="normal")
    forge_list_textbox.delete("0.0", "end")
    for v in forge_versions:
        forge_list_textbox.insert("end", f"• {v}\n")
    forge_list_textbox.configure(state="disabled")

# ---------- Fabric ----------
def install_fabric_for_current_version():
    if not minecraft_directory:
        messagebox.showerror("Error", "Select a folder first!")
        return
    version = selected_version.get()
    if version == "No versions":
        messagebox.showerror("Error", "Select a Minecraft version first!")
        return
    log_message(f"Starting Fabric installation for Minecraft {version}", "fabric")
    if not messagebox.askyesno("Install Fabric", f"Install Fabric for Minecraft {version}?"):
        log_message("Fabric installation cancelled", "info")
        return
    install_fabric_button.configure(state="disabled", text="Installing...")
    fabric_callback = {
        "setStatus": lambda s: log_message(f"Fabric: {s}", "fabric"),
        "setProgress": lambda p: None,
        "setMax": lambda m: None
    }
    def install_thread():
        success, msg, fv = fabric_manager.install_fabric(minecraft_directory, version, callback=fabric_callback)
        window.after(0, lambda: install_finished(success, msg, fv))
    def install_finished(success, msg, fv):
        install_fabric_button.configure(state="normal", text="🔷 Install Fabric")
        if success:
            log_message(f"Fabric installed: {msg}", "success")
            messagebox.showinfo("Success", msg)
            refresh_versions()
            refresh_fabric_list()
        else:
            log_message(f"Fabric installation failed: {msg}", "error")
            messagebox.showerror("Error", msg)
    threading.Thread(target=install_thread).start()

def refresh_fabric_list():
    global fabric_list_textbox
    if not minecraft_directory or fabric_list_textbox is None:
        return
    installed = minecraft_manager.get_versions(minecraft_directory)
    fabric_versions = [v for v in installed if "fabric" in v.lower()]
    fabric_list_textbox.configure(state="normal")
    fabric_list_textbox.delete("0.0", "end")
    for v in fabric_versions:
        fabric_list_textbox.insert("end", f"• {v}\n")
    fabric_list_textbox.configure(state="disabled")

# ---------- Mods Management ----------
def refresh_mods_list():
    """Atualiza a listbox de mods com os mods instalados."""
    if not minecraft_directory:
        return
    mods = minecraft_manager.get_mods(minecraft_directory)
    mods_listbox.delete("0.0", "end")
    for mod in mods:
        mods_listbox.insert("end", mod + "\n")

def add_mod_dialog():
    """Abre diálogo para selecionar um mod e o adiciona."""
    if not minecraft_directory:
        messagebox.showerror("Error", "Select a folder first!")
        return
    file_path = filedialog.askopenfilename(
        title="Select a mod file",
        filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
    )
    if not file_path:
        return
    log_message(f"Adding mod: {os.path.basename(file_path)}", "info")
    add_button.configure(state="disabled", text="Adding...")
    def add_thread():
        success, msg = minecraft_manager.add_mod(minecraft_directory, file_path)
        window.after(0, lambda: add_finished(success, msg))
    def add_finished(success, msg):
        add_button.configure(state="normal", text="➕ Add Mod")
        if success:
            log_message(msg, "success")
            refresh_mods_list()
            messagebox.showinfo("Success", msg)
        else:
            log_message(msg, "error")
            messagebox.showerror("Error", msg)
    threading.Thread(target=add_thread).start()

def remove_selected_mod():
    """Remove o mod selecionado na listbox."""
    if not minecraft_directory:
        messagebox.showerror("Error", "Select a folder first!")
        return
    try:
        selected = mods_listbox.get("sel.first", "sel.last").strip()
    except:
        messagebox.showerror("Error", "No mod selected!")
        return
    if not selected:
        messagebox.showerror("Error", "No mod selected!")
        return
    if not messagebox.askyesno("Confirm Removal", f"Remove mod {selected}?"):
        return
    log_message(f"Removing mod: {selected}", "info")
    remove_button.configure(state="disabled", text="Removing...")
    def remove_thread():
        success, msg = minecraft_manager.remove_mod(minecraft_directory, selected)
        window.after(0, lambda: remove_finished(success, msg))
    def remove_finished(success, msg):
        remove_button.configure(state="normal", text="➖ Remove Selected")
        if success:
            log_message(msg, "success")
            refresh_mods_list()
            messagebox.showinfo("Success", msg)
        else:
            log_message(msg, "error")
            messagebox.showerror("Error", msg)
    threading.Thread(target=remove_thread).start()

def refresh_mods_tab():
    """Atualiza todas as listas da aba Mods: Forge, Fabric e mods."""
    refresh_forge_list()
    refresh_fabric_list()
    refresh_mods_list()
    log_message("Mods tab refreshed", "info")

# ---------- Skin Management ----------
def select_skin():
    if not minecraft_directory:
        messagebox.showerror("Error", "Select a folder first!")
        return
    file_path = filedialog.askopenfilename(
        title="Select a skin image",
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
    )
    if not file_path:
        return
    display_name = selected_version.get()
    version_id = version_display_map.get(display_name, display_name)
    pack_format = minecraft_manager.get_resource_pack_format(minecraft_directory, version_id)
    if pack_format is None:
        pack_format = 15
        log_message(f"Could not detect pack_format, using fallback: {pack_format}", "info")
    model = "steve"
    result = messagebox.askyesno("Skin Model", "Is this an Alex model (slim arms)?\nYes = Alex, No = Steve")
    if result:
        model = "alex"
    success, msg = skins_manager.create_skin_resource_pack(minecraft_directory, file_path, model, pack_format)
    if success:
        log_message(msg, "success")
        messagebox.showinfo("Success", msg)
    else:
        log_message(msg, "error")
        messagebox.showerror("Error", msg)

def remove_skin():
    if not minecraft_directory:
        messagebox.showerror("Error", "Select a folder first!")
        return
    success, msg = skins_manager.remove_skin_pack(minecraft_directory)
    if success:
        log_message(msg, "info")
        messagebox.showinfo("Success", msg)
    else:
        messagebox.showerror("Error", msg)

# ========== UI ==========
# ========== HOME TAB ==========
# Frame principal que ocupa toda a aba
main_home_frame = ctk.CTkFrame(home_tab, fg_color="transparent")
main_home_frame.pack(fill="both", expand=True)

# ----- Frame superior (campos) -----
top_frame = ctk.CTkFrame(main_home_frame, fg_color="transparent")
top_frame.pack(side="top", fill="x", pady=20)

ctk.CTkLabel(top_frame, text="Better Launcher", font=("Arial", 24, "bold")).pack(pady=15)
ctk.CTkLabel(top_frame, text="Username:").pack()
username_entry = ctk.CTkEntry(top_frame, placeholder_text="Enter your username")
username_entry.pack(pady=5)
if last_username:
    username_entry.insert(0, last_username)
ctk.CTkLabel(top_frame, text="Version:").pack()
version_menu = ctk.CTkOptionMenu(top_frame, variable=selected_version, values=versions)
version_menu.pack(pady=5)
ctk.CTkLabel(top_frame, text="RAM (GB):").pack()
ram_entry = ctk.CTkEntry(top_frame, placeholder_text="2")
ram_entry.pack(pady=5)
ram_entry.insert(0, str(current_ram))

# ----- Frame central (imagem) -----
center_frame = ctk.CTkFrame(main_home_frame, fg_color="transparent")
center_frame.pack(side="top", fill="both", expand=True)

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  # quando empacotado com PyInstaller, os arquivos extras ficam aqui
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

image_path = os.path.join(base_path, "home_bg.png")  # nome da imagem (pode ser .png, .jpg, etc.)

try:
    from PIL import Image
    if os.path.exists(image_path):
        pil_image = Image.open(image_path)
        # Ajuste o tamanho conforme necessário
        ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(456, 50))
        image_label = ctk.CTkLabel(center_frame, image=ctk_image, text="")
        image_label.pack(expand=True)
    else:
        # Se a imagem não existir, apenas não mostra nada (ou pode mostrar um texto opcional)
        # ctk.CTkLabel(center_frame, text="[Imagem decorativa]", font=("Arial", 16)).pack(expand=True)
        pass  # não mostra nada
except Exception as e:
    print(f"Erro ao carregar imagem: {e}")
    # Em caso de erro, também não mostra nada
    pass

# ----- Frame inferior (botão) -----
bottom_frame = ctk.CTkFrame(main_home_frame, fg_color="transparent")
bottom_frame.pack(side="bottom", fill="x", pady=20)

play_btn = AnimatedButton(bottom_frame, text="▶ PLAY", command=launch_game, fg_color="#2e7d32", height=40, font=("Arial", 14, "bold"))
play_btn.pack(pady=10)
CTkToolTip(play_btn, message="Start Minecraft with selected version and RAM", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)

# ========== VERSIONS TAB ==========
ctk.CTkLabel(versions_tab, text="Manage Versions", font=("Arial", 18, "bold")).pack(pady=20)
version_frame = ctk.CTkFrame(versions_tab)
version_frame.pack(pady=10, padx=20, fill="x")
version_entry = ctk.CTkEntry(version_frame, placeholder_text="Enter version (e.g., 1.8.9)")
version_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
install_version_button = AnimatedButton(version_frame, text="📥 Install", command=install_version_from_entry, width=100)
install_version_button.pack(side="right")
CTkToolTip(install_version_button, message="Download and install a Minecraft version", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
version_status = ctk.StringVar(value="")
status_label = ctk.CTkLabel(versions_tab, textvariable=version_status, text_color=("gray", "white"))
status_label.pack(pady=5)
ctk.CTkLabel(versions_tab, text="Installed Versions:", font=("Arial", 14)).pack(pady=(20,5))
versions_listbox = ctk.CTkTextbox(versions_tab, wrap="word")
versions_listbox.pack(pady=5, padx=20, fill="both", expand=True)
CTkToolTip(versions_listbox, message="List of installed versions. Click to select.", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
action_frame = ctk.CTkFrame(versions_tab)
action_frame.pack(pady=5)
refresh_btn = AnimatedButton(action_frame, text="🔄 Refresh", command=update_versions_list, width=120)
refresh_btn.pack(side="left", padx=5)
CTkToolTip(refresh_btn, message="Update the list of installed versions", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
delete_button = AnimatedButton(action_frame, text="🗑️ Delete Selected", command=delete_current_version, width=120, fg_color="#d32f2f", hover_color="#b71c1c")
delete_button.pack(side="left", padx=5)
CTkToolTip(delete_button, message="Delete the currently selected version (from Home tab)", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
update_versions_list()

# ========== SETTINGS TAB ==========
ctk.CTkLabel(settings_tab, text="Settings", font=("Arial", 18, "bold")).pack(pady=20)
ctk.CTkLabel(settings_tab, text="Minecraft Folder:").pack()
folder_label = ctk.CTkLabel(settings_tab, textvariable=folder_text, wraplength=400, fg_color=("gray75", "gray25"), corner_radius=6, padx=10, pady=5)
folder_label.pack(pady=5)
folder_btn = AnimatedButton(settings_tab, text="📁 Choose Folder", command=select_folder)
folder_btn.pack(pady=10)
CTkToolTip(folder_btn, message="Select the folder where Minecraft will be installed", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
ctk.CTkLabel(settings_tab, text="Appearance:").pack(pady=(20,5))
theme_icon = "☀️" if current_theme == "light" else "🌙"
theme_button = AnimatedButton(settings_tab, text=f"{theme_icon} Switch to {'Dark' if current_theme == 'light' else 'Light'} Mode", command=toggle_theme, width=200)
theme_button.pack(pady=5)
CTkToolTip(theme_button, message="Toggle between dark and light appearance", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
ctk.CTkLabel(settings_tab, text=f"Current: {current_theme.title()} Mode", text_color=("gray", "white")).pack(pady=5)

# ========== MODS TAB ==========
loaders_frame = ctk.CTkFrame(mods_tab)
loaders_frame.pack(pady=10, padx=10, fill="x")

# ----- Forge Frame (esquerda) -----
forge_frame = ctk.CTkFrame(loaders_frame)
forge_frame.pack(side="left", fill="both", expand=True, padx=(0,5))
ctk.CTkLabel(forge_frame, text="Forge Installer", font=("Arial", 16, "bold")).pack(pady=5)
ctk.CTkLabel(forge_frame, text="Install Forge to use mods", font=("Arial", 12)).pack()
install_forge_button = AnimatedButton(forge_frame, text="⚙️ Install Forge", command=install_forge_for_current_version)
install_forge_button.pack(pady=5)
CTkToolTip(install_forge_button, message="Install Forge for the version selected in Home tab", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
ctk.CTkLabel(forge_frame, text="Installed Forge versions:").pack()
forge_list_textbox = ctk.CTkTextbox(forge_frame, height=80, wrap="word", state="disabled")
forge_list_textbox.pack(fill="both", expand=True, pady=5)

# ----- Fabric Frame (direita) -----
fabric_frame = ctk.CTkFrame(loaders_frame)
fabric_frame.pack(side="right", fill="both", expand=True, padx=(5,0))
ctk.CTkLabel(fabric_frame, text="Fabric Installer", font=("Arial", 16, "bold")).pack(pady=5)
ctk.CTkLabel(fabric_frame, text="Install Fabric to use mods", font=("Arial", 12)).pack()
install_fabric_button = AnimatedButton(fabric_frame, text="🔷 Install Fabric", command=install_fabric_for_current_version)
install_fabric_button.pack(pady=5)
CTkToolTip(install_fabric_button, message="Install Fabric for the version selected in Home tab", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
ctk.CTkLabel(fabric_frame, text="Installed Fabric versions:").pack()
fabric_list_textbox = ctk.CTkTextbox(fabric_frame, height=80, wrap="word", state="disabled")
fabric_list_textbox.pack(fill="both", expand=True, pady=5)

# ----- Mods Manager -----
mods_manager_frame = ctk.CTkFrame(mods_tab)
mods_manager_frame.pack(pady=10, padx=10, fill="both", expand=True)
ctk.CTkLabel(mods_manager_frame, text="Mods Manager", font=("Arial", 16, "bold")).pack(pady=5)
mods_listbox = ctk.CTkTextbox(mods_manager_frame, wrap="word")
mods_listbox.pack(pady=5, padx=10, fill="both", expand=True)
CTkToolTip(mods_listbox, message="List of installed mods. Click to select.", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
mods_buttons_frame = ctk.CTkFrame(mods_manager_frame)
mods_buttons_frame.pack(pady=5)
add_button = AnimatedButton(mods_buttons_frame, text="➕ Add Mod", command=add_mod_dialog, width=120)
add_button.pack(side="left", padx=5)
CTkToolTip(add_button, message="Add a new mod (.jar file)", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
remove_button = AnimatedButton(mods_buttons_frame, text="➖ Remove Selected", command=remove_selected_mod, width=140, fg_color="#d32f2f", hover_color="#b71c1c")
remove_button.pack(side="left", padx=5)
CTkToolTip(remove_button, message="Remove the selected mod", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
refresh_mods_button = AnimatedButton(mods_buttons_frame, text="🔄 Refresh All", command=refresh_mods_tab, width=120)
refresh_mods_button.pack(side="left", padx=5)
CTkToolTip(refresh_mods_button, message="Refresh loader lists and mod list", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)
refresh_forge_list()
refresh_fabric_list()
refresh_mods_list()

# ========== SKINS TAB ==========
ctk.CTkLabel(skins_tab, text="Skin Manager", font=("Arial", 18, "bold")).pack(pady=20)

select_btn = AnimatedButton(skins_tab, text="📂 Select Skin", command=select_skin)
select_btn.pack(pady=10)
CTkToolTip(select_btn, message="Choose a PNG image to use as your skin", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)

remove_btn = AnimatedButton(skins_tab, text="🗑️ Remove Skin", command=remove_skin, fg_color="#d32f2f", hover_color="#b71c1c")
remove_btn.pack(pady=5)
CTkToolTip(remove_btn, message="Remove the custom skin and revert to default", follow=True, delay=0.5, bg_color="#ffffe0", text_color="#000000", corner_radius=4)

info_text = (
    "Note:\n"
    "- The skin will appear in game after selecting it in Options > Resource Packs\n"
    "- You may need to restart the game for changes to take effect\n"
    "- Steve model: 64x64, Alex model: 64x32 (slim arms)"
)
ctk.CTkLabel(skins_tab, text=info_text, justify="left", wraplength=400).pack(pady=20)

# ========== CONSOLE TAB ==========
ctk.CTkLabel(console_tab, text="Console Logs", font=("Arial", 18, "bold")).pack(pady=10)
console_frame = ctk.CTkFrame(console_tab)
console_frame.pack(pady=10, padx=10, fill="both", expand=True)
console_text = ctk.CTkTextbox(console_frame, wrap="word", state="disabled")
console_text.pack(side="left", fill="both", expand=True, padx=(0, 5))
scrollbar = ctk.CTkScrollbar(console_frame, command=console_text.yview)
scrollbar.pack(side="right", fill="y")
console_text.configure(yscrollcommand=scrollbar.set)
clear_button = AnimatedButton(console_tab, text="🗑️ Clear Console", command=clear_console, width=150)
clear_button.pack(pady=5)

# ========== START ==========
refresh_versions()
window.mainloop()
