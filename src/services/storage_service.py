import os
import ipaddress
import socket
from pathlib import Path
from typing import Dict, Any

# Rutas maestras en la unidad compartida de red F:\
NETWORK_ROOT = Path("F:/Letters of Invitation LOIs")
TEMPLATES_DIR = NETWORK_ROOT
OUTPUT_DIR = NETWORK_ROOT / "Documentos_Generados"

LOI_TEMPLATE_NAME = "plantilla_loi.docx"
ANEXO_TEMPLATE_NAME = "plantilla_anexo_ix.docx"

class StorageService:
    """
    Servicio de gestión de almacenamiento en red local (Unidad F:\)
    Controla la lectura de plantillas, la ruta de salida de documentos generados
    y la verificación de conectividad y permisos de red en Windows.
    """

    @classmethod
    def get_network_root(cls) -> Path:
        return NETWORK_ROOT

    @classmethod
    def get_templates_dir(cls) -> Path:
        return TEMPLATES_DIR

    @classmethod
    def get_output_dir(cls) -> Path:
        return OUTPUT_DIR

    @classmethod
    def get_loi_template_path(cls) -> Path:
        return TEMPLATES_DIR / LOI_TEMPLATE_NAME

    @classmethod
    def get_anexo_template_path(cls) -> Path:
        return TEMPLATES_DIR / ANEXO_TEMPLATE_NAME

    @classmethod
    def check_storage_health(cls) -> Dict[str, Any]:
        """
        Verifica el estado de conexión de la unidad de red F:\, 
        la presencia obligatoria de las plantillas y los permisos de escritura.
        """
        root_path = cls.get_network_root()
        loi_path = cls.get_loi_template_path()
        anexo_path = cls.get_anexo_template_path()
        out_dir = cls.get_output_dir()

        # 1. Comprobar existencia del disco y carpeta raíz compartida
        try:
            if not root_path.exists():
                return {
                    "ok": False,
                    "error_code": "NETWORK_DRIVE_DISCONNECTED",
                    "mensaje": f"No se puede acceder a la unidad compartida en '{root_path}'. Verifique que la unidad de red F:\\ esté conectada a '\\\\192.168.4.5\\ficheros'."
                }
        except Exception as e:
            return {
                "ok": False,
                "error_code": "NETWORK_DRIVE_ERROR",
                "mensaje": f"Error accediendo a la unidad F:\\: {str(e)}"
            }

        # 2. Comprobar existencia de las dos plantillas obligatorias
        missing_templates = []
        if not loi_path.exists():
            missing_templates.append(f"LOI ({LOI_TEMPLATE_NAME})")
        if not anexo_path.exists():
            missing_templates.append(f"Anexo IX ({ANEXO_TEMPLATE_NAME})")

        if missing_templates:
            return {
                "ok": False,
                "error_code": "TEMPLATES_NOT_FOUND",
                "mensaje": f"Faltan plantillas en la unidad compartida F:\\: {', '.join(missing_templates)}. Deben estar en '{root_path}'."
            }

        # 3. Comprobar permisos de creación/escritura en el directorio de salida
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            test_file = out_dir / ".storage_health.tmp"
            test_file.write_text("health_check_ok", encoding="utf-8")
            if test_file.exists():
                test_file.unlink()
        except PermissionError:
            return {
                "ok": False,
                "error_code": "PERMISSION_DENIED",
                "mensaje": f"Permiso denegado: No se tienen permisos de escritura en '{out_dir}'. Compruebe los permisos del usuario en la red."
            }
        except Exception as e:
            return {
                "ok": False,
                "error_code": "WRITE_ERROR",
                "mensaje": f"No se pudo escribir en el directorio de salida '{out_dir}': {str(e)}"
            }

        return {
            "ok": True,
            "status": "connected",
            "network_root": str(root_path),
            "output_dir": str(out_dir),
            "loi_template": str(loi_path),
            "anexo_template": str(anexo_path),
            "mensaje": "Unidad de red F:\\ conectada y lista con permisos de lectura y escritura."
        }

    @staticmethod
    def get_local_lan_ip() -> str:
        """Detecta la IP local de la máquina en la red local de la oficina (ej. 192.168.4.30)."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    @staticmethod
    def is_lan_ip(client_ip: str) -> bool:
        """Comprueba si una dirección IP pertenece a una red privada / local (LAN)."""
        if not client_ip:
            return False
        clean_ip = client_ip.strip()
        if clean_ip in ("127.0.0.1", "localhost", "::1", "testclient"):
            return True
        try:
            ip_obj = ipaddress.ip_address(clean_ip)
            return ip_obj.is_private or ip_obj.is_loopback
        except ValueError:
            return False
