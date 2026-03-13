import minecraft_launcher_lib
from java_utils import get_runtime_for_version, get_java_executable_from_runtime
import os
import platform
import requests
import zipfile
import shutil

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