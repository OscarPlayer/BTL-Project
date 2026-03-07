import minecraft_launcher_lib
import os
import platform
import requests
import zipfile
import shutil

# ========== NOVO: Mapeamento de nomes reais das pastas ==========
RUNTIME_FOLDER_MAP = {
    "java-runtime-alpha": ["jre-legacy", "java-runtime-alpha"],  # Java 8 está em jre-legacy
    "java-runtime-beta": ["java-runtime-beta"],                  # Java 11
    "java-runtime-gamma": ["java-runtime-gamma"],                # Java 16/17
    "java-runtime-delta": ["java-runtime-delta"],                # Java 17+
}

def get_runtime_for_version(minecraft_version):
    """
    Retorna o nome do runtime necessário para a versão do Minecraft.
    """
    if minecraft_version.startswith("1."):
        try:
            major, minor = map(int, minecraft_version.split(".")[:2])
        except:
            return "java-runtime-gamma"
        if minor <= 16:
            return "java-runtime-alpha"
        elif minor == 17:
            return "java-runtime-beta"
        elif minor <= 20:
            return "java-runtime-gamma"
        else:
            return "java-runtime-delta"
    return "java-runtime-gamma"

# ========== FUNÇÃO MODIFICADA ==========
def get_java_executable_from_runtime(minecraft_dir, runtime_name):
    """
    Procura por javaw.exe nas possíveis pastas do runtime.
    Primeiro tenta os nomes mapeados, depois faz busca recursiva como fallback.
    """
    runtime_base = os.path.join(minecraft_dir, "runtime")
    if not os.path.exists(runtime_base):
        print(f"DEBUG: Pasta runtime não existe: {runtime_base}")
        return None
    
    # Obtém a lista de possíveis nomes de pasta para este runtime
    possible_folders = RUNTIME_FOLDER_MAP.get(runtime_name, [runtime_name])
    
    # Tenta cada possível nome de pasta
    for folder_name in possible_folders:
        candidate_path = os.path.join(runtime_base, folder_name)
        print(f"DEBUG: Tentando caminho: {candidate_path}")
        if os.path.exists(candidate_path):
            # Procura recursivamente por javaw.exe dentro desta pasta
            for root, dirs, files in os.walk(candidate_path):
                if "javaw.exe" in files:
                    java_path = os.path.join(root, "javaw.exe")
                    print(f"DEBUG: Encontrado javaw.exe em: {java_path}")
                    return java_path
                if "java.exe" in files:
                    java_path = os.path.join(root, "java.exe")
                    print(f"DEBUG: Encontrado java.exe em: {java_path}")
                    return java_path
    
    # Se não encontrou, faz uma busca recursiva em toda a pasta runtime (fallback)
    print("DEBUG: Fazendo busca recursiva em toda a pasta runtime...")
    for root, dirs, files in os.walk(runtime_base):
        if "javaw.exe" in files:
            java_path = os.path.join(root, "javaw.exe")
            print(f"DEBUG: Encontrado javaw.exe em: {java_path}")
            return java_path
        if "java.exe" in files:
            java_path = os.path.join(root, "java.exe")
            print(f"DEBUG: Encontrado java.exe em: {java_path}")
            return java_path
    
    print(f"DEBUG: Nenhum java.exe ou javaw.exe encontrado em {runtime_base}")
    return None

def install_forge(minecraft_dir, minecraft_version, callback=None):
    """
    Instala o Forge usando a biblioteca minecraft_launcher_lib,
    forçando o uso do runtime correto.
    """
    try:
        # 1. Verifica se a versão vanilla existe
        versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_dir)
        vanilla_installed = any(v["id"] == minecraft_version for v in versions)
        if not vanilla_installed:
            return False, f"Vanilla {minecraft_version} is not installed. Install it first.", None
        
        # 2. Descobre qual runtime usar e pega o caminho do Java
        runtime_name = get_runtime_for_version(minecraft_version)
        java_path = get_java_executable_from_runtime(minecraft_dir, runtime_name)
        if not java_path:
            return False, f"Runtime {runtime_name} not found. Run the vanilla version first to download it.", None
        
        # 3. Encontra a versão do Forge
        forge_version = minecraft_launcher_lib.forge.find_forge_version(minecraft_version)
        if not forge_version:
            return False, f"No Forge version found for Minecraft {minecraft_version}", None
        
        # 4. Instala o Forge com monkey patch no subprocess.run
        import subprocess
        original_run = subprocess.run
        
        def patched_run(*args, **kwargs):
            # Se o comando começar com 'java' ou 'javaw', substitui pelo caminho completo
            if args and isinstance(args[0], list) and args[0] and args[0][0] in ('java', 'javaw', 'java.exe', 'javaw.exe'):
                new_cmd = [java_path] + args[0][1:]
                args = (new_cmd,) + args[1:]
            return original_run(*args, **kwargs)
        
        subprocess.run = patched_run
        
        try:
            # Instala o Forge
            minecraft_launcher_lib.forge.install_forge_version(
                forge_version,
                minecraft_dir,
                callback=callback
            )
        finally:
            # Restaura o subprocess.run original
            subprocess.run = original_run
        
        # 5. Verifica se a versão foi instalada
        installed = minecraft_launcher_lib.utils.get_installed_versions(minecraft_dir)
        # Procura por qualquer versão que contenha 'forge' e a versão do minecraft
        forge_installed = [v["id"] for v in installed if "forge" in v["id"].lower() and minecraft_version in v["id"]]
        
        if forge_installed:
            return True, f"Forge {forge_version} installed successfully!", forge_installed[0]
        else:
            # Se não achou, tenta busca mais genérica
            forge_installed = [v["id"] for v in installed if "forge" in v["id"].lower()]
            if forge_installed:
                return True, f"Forge {forge_version} installed (with name: {forge_installed[0]})!", forge_installed[0]
            else:
                return True, f"Forge {forge_version} installed, but version not found in list.", None
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Error installing Forge: {str(e)}", None
