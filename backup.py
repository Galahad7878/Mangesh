import os
import sys
import zipfile
from pathlib import Path
from datetime import datetime

# Asegurar compatibilidad de salida UTF-8 en consolas Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Carpetas y extensiones excluidas obligatoriamente
EXCLUDED_DIRS = {
    '.venv', 'venv', 'env', '.env',
    'node_modules', '__pycache__',
    '.git', '.pytest_cache', '.vscode', '.idea',
    '.system_generated'
}
EXCLUDED_EXTS = {'.pyc', '.pyo', '.pyd', '.log', '.tmp'}

def create_backup():
    project_dir = Path(__file__).resolve().parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_filename = f"backup_LOIs_{timestamp}.zip"
    
    # Destino fuera del proyecto: Carpeta en el Escritorio del usuario
    desktop_backup_dir = Path.home() / "Desktop" / "Backups_NaviAgent"
    desktop_backup_dir.mkdir(parents=True, exist_ok=True)
    zip_path = desktop_backup_dir / backup_filename
    
    print("=" * 65)
    print("      NAVIAGENT - COPIA DE SEGURIDAD AUTOMATICA")
    print("=" * 65)
    print(f"[*] Origen:   {project_dir}")
    print(f"[*] Destino:  {zip_path}")
    print(f"[*] Ignorado: {', '.join(sorted(EXCLUDED_DIRS))}")
    print("-" * 65)

    count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            # Excluir directorios pesados y temporales in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in EXCLUDED_EXTS:
                    continue
                
                # Evitar incluir copias de backups anteriores
                if file.startswith("backup_") and ext == ".zip":
                    continue
                
                full_path = Path(root) / file
                rel_path = full_path.relative_to(project_dir)
                
                zipf.write(full_path, arcname=str(rel_path))
                print(f"  + {rel_path}")
                count += 1

    size_kb = round(zip_path.stat().st_size / 1024, 1)
    print("=" * 65)
    print("OK: Copia de seguridad generada con exito!")
    print(f"Total archivos: {count}")
    print(f"Tamano ZIP:     {size_kb} KB")
    print(f"Ubicacion:      {zip_path}")
    print("=" * 65)
    return zip_path

if __name__ == "__main__":
    create_backup()
