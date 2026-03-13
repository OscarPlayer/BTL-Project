import os
import shutil
import json

# Nome do nosso resource pack (aparecerá no jogo)
PACK_NAME = "YourSkin"

def create_skin_resource_pack(minecraft_dir, skin_path, model="steve", pack_format=15):
    """
    Cria um resource pack com a skin do usuário dentro da pasta resourcepacks.
    
    Args:
        minecraft_dir: diretório do jogo (ex: C:/Users/.../Game)
        skin_path: caminho para a imagem .png escolhida
        model: "steve" ou "alex" (define qual textura substituir)
        pack_format: número da versão do pack (padrão 15 para 1.20.5+)
    
    Returns:
        (sucesso, mensagem)
    """
    # Caminho base do resource pack (dentro de resourcepacks)
    packs_dir = os.path.join(minecraft_dir, "resourcepacks")
    pack_dir = os.path.join(packs_dir, PACK_NAME)
    assets_dir = os.path.join(pack_dir, "assets", "minecraft", "textures", "entity")
    
    # Cria a estrutura de pastas
    os.makedirs(assets_dir, exist_ok=True)
    
    # Define o nome do arquivo de destino baseado no modelo
    if model.lower() == "alex":
        dest_file = os.path.join(assets_dir, "alex.png")
    else:
        dest_file = os.path.join(assets_dir, "steve.png")
    
    # Copia a imagem do usuário
    try:
        shutil.copy2(skin_path, dest_file)
    except Exception as e:
        return False, f"Error copying skin: {str(e)}"
    
    # Cria o arquivo pack.mcmeta (obrigatório)
    mcmeta = {
        "pack": {
            "pack_format": pack_format,
            "description": "Custom skin"
        }
    }
    mcmeta_path = os.path.join(pack_dir, "pack.mcmeta")
    with open(mcmeta_path, "w", encoding="utf-8") as f:
        json.dump(mcmeta, f, indent=2)
    
    # Tenta ativar o pack no options.txt
    enable_skin_pack(minecraft_dir)
    
    return True, f"Skin applied successfully! (model: {model})"

def enable_skin_pack(minecraft_dir):
    """
    Ativa o resource pack YourSkin no options.txt do Minecraft.
    """
    options_path = os.path.join(minecraft_dir, "options.txt")
    if not os.path.exists(options_path):
        # Se o arquivo não existe, o jogo ainda não foi iniciado
        return
    
    try:
        with open(options_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Procura pela linha resourcePacks:
        found = False
        for i, line in enumerate(lines):
            if line.startswith("resourcePacks:"):
                # Extrai a lista atual
                packs_str = line[len("resourcePacks:"):].strip()
                try:
                    packs = json.loads(packs_str)
                    if PACK_NAME not in packs:
                        packs.append(PACK_NAME)
                    lines[i] = f"resourcePacks:{json.dumps(packs)}\n"
                except:
                    # Se não conseguir interpretar, substitui por nova lista
                    lines[i] = f"resourcePacks:[\"{PACK_NAME}\"]\n"
                found = True
                break
        
        if not found:
            # Se não existir, adiciona no final
            lines.append(f"resourcePacks:[\"{PACK_NAME}\"]\n")
        
        with open(options_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        print(f"Error enabling skin pack: {e}")

def remove_skin_pack(minecraft_dir):
    """
    Remove a pasta do resource pack e desativa no options.txt.
    """
    pack_dir = os.path.join(minecraft_dir, "resourcepacks", PACK_NAME)
    if os.path.exists(pack_dir):
        shutil.rmtree(pack_dir)
    
    # Remove da lista no options.txt
    options_path = os.path.join(minecraft_dir, "options.txt")
    if os.path.exists(options_path):
        try:
            with open(options_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                if line.startswith("resourcePacks:"):
                    packs_str = line[len("resourcePacks:"):].strip()
                    try:
                        packs = json.loads(packs_str)
                        if PACK_NAME in packs:
                            packs.remove(PACK_NAME)
                        lines[i] = f"resourcePacks:{json.dumps(packs)}\n"
                    except:
                        lines[i] = f"resourcePacks:[]\n"
                    break
            
            with open(options_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            print(f"Error removing skin from options.txt: {e}")
    
    return True, "Skin removed. (Restart the game to see default skin)"