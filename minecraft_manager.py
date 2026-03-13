import minecraft_launcher_lib
import uuid
import subprocess
import threading
import os
import json
import shutil
import re
from java_utils import get_runtime_for_version, get_java_executable_from_runtime

def setup_folder(directory):
    """Ensures the folder has everything it needs"""
    if not directory:
        return False
    folders = ["versions", "libraries", "assets", "natives", "runtime"]
    for folder in folders:
        os.makedirs(os.path.join(directory, folder), exist_ok=True)
    profiles_file = os.path.join(directory, "launcher_profiles.json")
    if not os.path.exists(profiles_file):
        with open(profiles_file, "w") as f:
            json.dump({
                "profiles": {},
                "selectedProfile": "(Default)",
                "clientToken": str(uuid.uuid4())
            }, f, indent=2)
    return True

def ensure_java_runtime(directory, version):
    """Garante que o runtime Java para a versão está baixado."""
    runtime_name = get_runtime_for_version(version)
    java_path = get_java_executable_from_runtime(directory, runtime_name)
    if java_path:
        return True
    # Se não encontrou, tenta baixar via minecraft_launcher_lib
    try:
        print(f"Baixando runtime {runtime_name} para versão {version}...")
        # A biblioteca baixa o runtime automaticamente durante a instalação da versão
        # Mas podemos forçar o download aqui se necessário
        # Por enquanto, apenas retornamos False e deixamos a instalação tentar baixar
        return False
    except:
        return False

def consolidate_forge_versions(minecraft_dir):
    """Corrige a estrutura de versões antigas do Forge."""
    versions_dir = os.path.join(minecraft_dir, "versions")
    if not os.path.exists(versions_dir):
        return 0
    all_folders = [f for f in os.listdir(versions_dir) if os.path.isdir(os.path.join(versions_dir, f))]
    forge_folders = [f for f in all_folders if "forge" in f.lower()]
    consolidated = 0
    used = set()
    for folder in forge_folders:
        if folder in used:
            continue
        folder_path = os.path.join(versions_dir, folder)
        files = os.listdir(folder_path)
        has_json = any(f.endswith('.json') for f in files)
        has_jar = any(f.endswith('.jar') for f in files)
        if has_json and has_jar:
            continue
        complement = None
        for other in forge_folders:
            if other == folder or other in used:
                continue
            numbers_folder = re.findall(r'\d+\.\d+(?:\.\d+)*', folder)
            numbers_other = re.findall(r'\d+\.\d+(?:\.\d+)*', other)
            if set(numbers_folder) & set(numbers_other):
                complement = other
                break
        if complement:
            complement_path = os.path.join(versions_dir, complement)
            comp_files = os.listdir(complement_path)
            comp_has_json = any(f.endswith('.json') for f in comp_files)
            comp_has_jar = any(f.endswith('.jar') for f in comp_files)
            if has_jar and not has_json and comp_has_json and not comp_has_jar:
                main_folder = folder
                json_folder = complement
            elif comp_has_jar and not comp_has_json and has_json and not has_jar:
                main_folder = complement
                json_folder = folder
            else:
                continue
            main_path = os.path.join(versions_dir, main_folder)
            json_path = os.path.join(versions_dir, json_folder)
            json_files = [f for f in os.listdir(json_path) if f.endswith('.json')]
            if json_files:
                src_json = os.path.join(json_path, json_files[0])
                dest_json = os.path.join(main_path, main_folder + ".json")
                shutil.copy2(src_json, dest_json)
                print(f"Consolidated: copied JSON from {json_folder} to {main_folder}")
                shutil.rmtree(json_path)
                print(f"Deleted redundant folder: {json_folder}")
                used.add(main_folder)
                used.add(json_folder)
                consolidated += 1
    return consolidated

def get_versions(directory):
    if not directory or not os.path.exists(directory):
        return ["No versions"]
    try:
        setup_folder(directory)
        consolidate_forge_versions(directory)
        versions = minecraft_launcher_lib.utils.get_installed_versions(directory)
        return [v["id"] for v in versions] or ["No versions"]
    except Exception as e:
        print(f"Error getting versions: {e}")
        return ["No versions"]

def launch(directory, username, ram, version):
    setup_folder(directory)
    consolidate_forge_versions(directory)
    
    # Garante que o runtime existe
    runtime_name = get_runtime_for_version(version)
    java_path = get_java_executable_from_runtime(directory, runtime_name)
    if not java_path:
        raise Exception(f"Runtime {runtime_name} not found. Please install the vanilla version first.")
    
    options = {
        "username": username,
        "uuid": str(uuid.uuid4()),
        "token": "",
        "jvmArguments": [f"-Xmx{ram}G", f"-Xms{ram}G"],
        "executablePath": java_path  # Força usar nosso Java
    }
    
    command = minecraft_launcher_lib.command.get_minecraft_command(
        version, directory, options
    )
    
    # Substitui o java pelo nosso (redundante, mas seguro)
    if len(command) > 0:
        command[0] = java_path
    
    # Captura stderr para debug
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
        text=True,
        encoding='utf-8'
    )
    
    def log_output():
        for line in process.stdout:
            print(f"[MINECRAFT OUT] {line.strip()}")
        for line in process.stderr:
            print(f"[MINECRAFT ERROR] {line.strip()}")
    
    threading.Thread(target=log_output, daemon=True).start()

def install(directory, version, on_success, on_error, progress_callback=None):
    setup_folder(directory)
    
    # Garante que o runtime será baixado durante a instalação
    # A biblioteca já faz isso automaticamente, mas vamos forçar a verificação
    runtime_name = get_runtime_for_version(version)
    java_path = get_java_executable_from_runtime(directory, runtime_name)
    if not java_path:
        print(f"Runtime {runtime_name} não encontrado. Será baixado durante a instalação.")
    
    def install_thread():
        try:
            if progress_callback:
                callback_dict = {
                    "setStatus": lambda status: progress_callback(status, "info"),
                    "setProgress": lambda progress: None,
                    "setMax": lambda max_val: None
                }
                minecraft_launcher_lib.install.install_minecraft_version(
                    version, directory, callback=callback_dict
                )
            else:
                minecraft_launcher_lib.install.install_minecraft_version(
                    version, directory
                )
            on_success(version)
        except Exception as e:
            if "SSL" in str(e):
                try:
                    print("SSL error, trying again...")
                    if progress_callback:
                        callback_dict = {
                            "setStatus": lambda status: progress_callback(status, "info"),
                            "setProgress": lambda progress: None,
                            "setMax": lambda max_val: None
                        }
                        minecraft_launcher_lib.install.install_minecraft_version(
                            version, directory, callback=callback_dict
                        )
                    else:
                        minecraft_launcher_lib.install.install_minecraft_version(
                            version, directory
                        )
                    on_success(version)
                except Exception as e2:
                    on_error(str(e2))
            else:
                on_error(str(e))
    
    threading.Thread(target=install_thread).start()

def delete_version(directory, version_id):
    version_dir = os.path.join(directory, "versions", version_id)
    if not os.path.exists(version_dir):
        return False, f"Version {version_id} not found."
    try:
        shutil.rmtree(version_dir)
        return True, f"Version {version_id} deleted successfully."
    except Exception as e:
        return False, f"Error deleting version: {str(e)}"

def get_display_name(version_id):
    if "forge" in version_id.lower():
        import re
        match = re.search(r'(\d+\.\d+(?:\.\d+)?)', version_id)
        if match:
            vanilla_version = match.group(1)
            return f"Forge - {vanilla_version}"
        return "Forge (unknown version)"
    if "fabric" in version_id.lower():
        import re
        matches = re.findall(r'(\d+\.\d+(?:\.\d+)?)', version_id)
        if matches:
            vanilla_version = matches[-1]
            return f"Fabric - {vanilla_version}"
        return "Fabric (unknown version)"
    return version_id

def get_mods(directory):
    mods_dir = os.path.join(directory, "mods")
    if not os.path.exists(mods_dir):
        return []
    return [f for f in os.listdir(mods_dir) if f.endswith('.jar')]

def add_mod(directory, file_path):
    if not file_path.lower().endswith('.jar'):
        return False, "Only .jar files are allowed."
    mods_dir = os.path.join(directory, "mods")
    os.makedirs(mods_dir, exist_ok=True)
    dest_path = os.path.join(mods_dir, os.path.basename(file_path))
    if os.path.exists(dest_path):
        return False, f"Mod {os.path.basename(file_path)} already exists."
    try:
        shutil.copy2(file_path, dest_path)
        return True, f"Mod {os.path.basename(file_path)} added successfully."
    except Exception as e:
        return False, f"Error adding mod: {str(e)}"

def remove_mod(directory, mod_name):
    mod_path = os.path.join(directory, "mods", mod_name)
    if not os.path.exists(mod_path):
        return False, f"Mod {mod_name} not found."
    try:
        os.remove(mod_path)
        return True, f"Mod {mod_name} removed successfully."
    except Exception as e:
        return False, f"Error removing mod: {str(e)}"

def get_resource_pack_format(minecraft_dir, version_id):
    version_json_path = os.path.join(minecraft_dir, "versions", version_id, f"{version_id}.json")
    if not os.path.exists(version_json_path):
        return None
    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
        if "pack_version" in version_data:
            if isinstance(version_data["pack_version"], int):
                return version_data["pack_version"]
            elif isinstance(version_data["pack_version"], dict) and "resource" in version_data["pack_version"]:
                return version_data["pack_version"]["resource"]
        if version_id.startswith("1.8"):
            return 1
        elif version_id.startswith("1.7"):
            return 3
        elif version_id.startswith("1.6"):
            return 2
        elif version_id.startswith("1.5"):
            return 1
        return 15
    except Exception as e:
        print(f"Error reading version.json: {e}")
        if version_id.startswith("1.8"):
            return 1
        return 15