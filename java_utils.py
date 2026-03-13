import os

RUNTIME_FOLDER_MAP = {
    "java-runtime-alpha": ["jre-legacy", "java-runtime-alpha"],
    "java-runtime-beta": ["java-runtime-beta"],
    "java-runtime-gamma": ["java-runtime-gamma"],
    "java-runtime-delta": ["java-runtime-delta"],
}

def get_runtime_for_version(minecraft_version):
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

def get_java_executable_from_runtime(minecraft_dir, runtime_name):
    runtime_base = os.path.join(minecraft_dir, "runtime")
    if not os.path.exists(runtime_base):
        return None
    possible_folders = RUNTIME_FOLDER_MAP.get(runtime_name, [runtime_name])
    for folder_name in possible_folders:
        candidate_path = os.path.join(runtime_base, folder_name)
        if os.path.exists(candidate_path):
            for root, dirs, files in os.walk(candidate_path):
                if "javaw.exe" in files:
                    return os.path.join(root, "javaw.exe")
                if "java.exe" in files:
                    return os.path.join(root, "java.exe")
    # fallback
    for root, dirs, files in os.walk(runtime_base):
        if "javaw.exe" in files:
            return os.path.join(root, "javaw.exe")
        if "java.exe" in files:
            return os.path.join(root, "java.exe")
    return None