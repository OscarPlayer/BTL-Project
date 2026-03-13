import minecraft_launcher_lib
import os
import subprocess
from java_utils import get_runtime_for_version, get_java_executable_from_runtime

def install_fabric(minecraft_dir, minecraft_version, loader_version=None, callback=None):
    """
    Instala o Fabric usando a biblioteca.
    Se loader_version for None, usa a versão mais recente compatível.
    """
    try:
        # Verifica vanilla
        versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_dir)
        if not any(v["id"] == minecraft_version for v in versions):
            return False, f"Vanilla {minecraft_version} is not installed. Install it first.", None

        # Se não especificou versão, usa None (a biblioteca escolhe a mais recente)
        # Se especificou, usa a versão escolhida (a biblioteca valida se é compatível)
        
        # Obtém Java
        runtime_name = get_runtime_for_version(minecraft_version)
        java_path = get_java_executable_from_runtime(minecraft_dir, runtime_name)
        if not java_path:
            return False, f"Runtime {runtime_name} not found. Run the vanilla version first.", None

        # Monkey patch no subprocess.run
        original_run = subprocess.run
        def patched_run(*args, **kwargs):
            if args and isinstance(args[0], list) and args[0] and args[0][0] in ('java', 'javaw', 'java.exe', 'javaw.exe'):
                new_cmd = [java_path] + args[0][1:]
                args = (new_cmd,) + args[1:]
            return original_run(*args, **kwargs)

        subprocess.run = patched_run
        try:
            # Instala o Fabric - se loader_version for None, usa a mais recente
            minecraft_launcher_lib.fabric.install_fabric(
                minecraft_version,
                minecraft_dir,
                loader_version=loader_version,  # Pode ser None
                callback=callback
            )
        finally:
            subprocess.run = original_run

        # Descobre a versão instalada
        installed = minecraft_launcher_lib.utils.get_installed_versions(minecraft_dir)
        fabric_installed = [
            v["id"] for v in installed 
            if "fabric" in v["id"].lower() and minecraft_version in v["id"]
        ]
        if fabric_installed:
            return True, f"Fabric {loader_version or 'latest'} installed successfully!", fabric_installed[0]
        else:
            return True, f"Fabric {loader_version or 'latest'} installed, but version not found.", None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Error installing Fabric: {str(e)}", None
