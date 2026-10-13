import re
from pathlib import Path
from datetime import datetime
from docxtpl import DocxTemplate
from src.models import CrewMemberData, GenerateDocResponse
from src.services.storage_service import StorageService

class LOIAgent:
    """
    Agente 2: LOIAgent
    Toma los datos estructurados del tripulante, los inyecta en 'plantilla_loi.docx'
    leída exclusivamente desde la unidad compartida F:/Letters of Invitation LOIs/
    respetando rigurosamente el diseño, estilos, tipografías y tablas,
    y guarda el resultado en F:/Letters of Invitation LOIs/Documentos_Generados/LOI_[Nombre]_[Fecha].docx.
    """

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or StorageService.get_output_dir()

    def generate(self, crew: CrewMemberData) -> GenerateDocResponse:
        # 1. Comprobar salud y conectividad de la unidad F:\
        health = StorageService.check_storage_health()
        if not health["ok"]:
            raise RuntimeError(health["mensaje"])

        template_path = StorageService.get_loi_template_path()
        if not template_path.exists():
            raise FileNotFoundError(f"No se encontró la plantilla LOI en la unidad de red: {template_path}")

        try:
            # 2. Cargar plantilla docxtpl desde unidad F:\
            doc = DocxTemplate(str(template_path))

            from src.services.context_service import build_template_context

            # Preparar contexto para Jinja2
            context = build_template_context(crew)

            # Renderizar documento
            doc.render(context)

            # Generar nombre seguro de archivo
            safe_name = re.sub(r'[^A-Za-z0-9_]', '_', crew.nombre_completo or "TRIPULANTE").strip('_')
            safe_date = re.sub(r'[^0-9]', '', crew.fecha_embarque or datetime.now().strftime("%Y%m%d"))
            if not safe_date:
                safe_date = datetime.now().strftime("%Y%m%d")

            output_filename = f"LOI_{safe_name}_{safe_date}.docx"
            out_dir = self.output_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = out_dir / output_filename

            # 3. Guardar documento en unidad F:\
            doc.save(str(output_path))
            print(f"[LOIAgent] Documento LOI guardado en red F:\\: {output_path}")

            return GenerateDocResponse(
                success=True,
                tipo="LOI",
                nombre_archivo=output_filename,
                ruta_archivo=str(output_path),
                url_descarga=f"/api/descargar/{output_filename}",
                mensaje=f"Carta de Invitación (LOI) guardada correctamente en {output_path}"
            )
        except PermissionError:
            raise PermissionError(f"Sin permisos de escritura en la carpeta de destino en F:\\: {self.output_dir}")
        except Exception as e:
            raise RuntimeError(f"Error procesando la plantilla LOI en la unidad F:\\: {str(e)}")
