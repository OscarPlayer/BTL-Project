import minecraft_launcher_lib
import uuid
import subprocess
import threading
import os
import json
import shutil
import re

def setup_folder(directory):
    """
    Ensures the folder has everything it needs
    """
    if not directory:
        return False
    
    # Required folders
    folders = ["versions", "libraries", "assets", "natives"]
    for folder in folders:
        os.makedirs(os.path.join(directory, folder), exist_ok=True)
    
    # Configuration file if it doesn't exist
    profiles_file = os.path.join(directory, "launcher_profiles.json")
    if not os.path.exists(profiles_file):
        with open(profiles_file, "w") as f:
            json.dump({
                "profiles": {},
                "selectedProfile": "(Default)",
                "clientToken": str(uuid.uuid4())
            }, f, indent=2)
    
    return True

def get_display_name(version_id):
    """
    Converte IDs técnicos em nomes amigáveis para exibição.
    Ex: "1.8.9-forge1.8.9-11.15.1.2318-1.8.9" → "Forge - 1.8.9"
    """
    if "forge" in version_id.lower():
        import re
        match = re.search(r'(\d+\.\d+(?:\.\d+)?)', version_id)
        if match:
            vanilla_version = match.group(1)
            return f"Forge - {vanilla_version}"
        return "Forge (unknown version)"
    return version_id  # Versões vanilla permanecem iguais

def consolidate_forge_versions(minecraft_dir):
    """
    Corrige a estrutura de versões antigas do Forge que criam duas pastas.
    Após copiar o JSON para a pasta principal, deleta a pasta secundária.
    Retorna o número de versões consolidadas.
    """
    versions_dir = os.path.join(minecraft_dir, "versions")
    if not os.path.exists(versions_dir):
        return 0

    all_folders = [f for f in os.listdir(versions_dir) if os.path.isdir(os.path.join(versions_dir, f))]
    
    # Filtra pastas com "forge" no nome
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
        
        # Se já tem tudo, não precisa fazer nada
        if has_json and has_jar:
            continue
        
        # Procura um par (outra pasta com números de versão em comum)
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
            
            # Decide qual pasta tem o JAR (a principal)
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
            
            # Copia o JSON para a pasta principal
            json_files = [f for f in os.listdir(json_path) if f.endswith('.json')]
            if json_files:
                src_json = os.path.join(json_path, json_files[0])
                dest_json = os.path.join(main_path, main_folder + ".json")
                shutil.copy2(src_json, dest_json)
                print(f"Consolidated: copied JSON from {json_folder} to {main_folder}")
                
                # --- AGORA DELETA a pasta secundária ---
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
        # First ensures the folder exists
        setup_folder(directory)
        
        # Consolida versões antigas do Forge (ex: 1.8.9)
        consolidate_forge_versions(directory)
        
        versions = minecraft_launcher_lib.utils.get_installed_versions(directory)
        return [v["id"] for v in versions] or ["No versions"]
    except Exception as e:
        print(f"Error getting versions: {e}")
        return ["No versions"]

def launch(directory, username, ram, version):
    # Ensures folder exists before launching
    setup_folder(directory)
    
    # Consolida novamente por segurança (caso a versão seja Forge antiga)
    consolidate_forge_versions(directory)
    
    options = {
        "username": username,
        "uuid": str(uuid.uuid4()),
        "token": "",
        "jvmArguments": [f"-Xmx{ram}G", f"-Xms{ram}G"],
    }
    
    command = minecraft_launcher_lib.command.get_minecraft_command(
        version, directory, options
    )
    
    if command[0].lower().endswith("java.exe"):
        command[0] = command[0][:-8] + "javaw.exe"
    
    subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)

def install(directory, version, on_success, on_error):
    # Ensures folder exists before installing
    setup_folder(directory)
    
    def install_thread():
        try:
            # Try to install with better error handling
            minecraft_launcher_lib.install.install_minecraft_version(
                version, directory
            )
            on_success(version)
        except Exception as e:
            # If SSL error, try again (sometimes it's network)
            if "SSL" in str(e):
                try:
                    print("SSL error, trying again...")
                    minecraft_launcher_lib.install.install_minecraft_version(
                        version, directory
                    )
                    on_success(version)
                except Exception as e2:
                    on_error(str(e2))
            else:
                on_error(str(e))
    
    threading.Thread(target=install_thread).start()
