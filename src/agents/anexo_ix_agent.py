import re
from pathlib import Path
from datetime import datetime
from docxtpl import DocxTemplate
from src.models import CrewMemberData, GenerateDocResponse
from src.services.storage_service import StorageService

class AnexoIXAgent:
    """
    Agente 3: AnexoIXAgent
    Toma los datos estructurados del tripulante, los mapea en 'plantilla_anexo_ix.docx'
    leída exclusivamente desde la unidad compartida F:/Letters of Invitation LOIs/
    preservando el formato y estructura oficial del Anexo IX (solicitud visado frontera)
    en Times New Roman 10pt regular (sin negrita),
    y guarda el archivo en F:/Letters of Invitation LOIs/Documentos_Generados/Anexo_IX_[Nombre]_[Fecha].docx.
    """

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or StorageService.get_output_dir()

    def generate(self, crew: CrewMemberData) -> GenerateDocResponse:
        # 1. Comprobar salud y conectividad de la unidad F:\
        health = StorageService.check_storage_health()
        if not health["ok"]:
            raise RuntimeError(health["mensaje"])

        template_path = StorageService.get_anexo_template_path()
        if not template_path.exists():
            raise FileNotFoundError(f"No se encontró la plantilla Anexo IX en la unidad de red: {template_path}")

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

            output_filename = f"Anexo_IX_{safe_name}_{safe_date}.docx"
            out_dir = self.output_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = out_dir / output_filename

            # Guardar documento temporal para pase de estilo tipográfico
            doc.save(str(output_path))

            # Garantizar tipografía Times New Roman tamaño 10 en todo el documento generado
            self._apply_times_new_roman_10(output_path)

            print(f"[AnexoIXAgent] Documento Anexo IX guardado en red F:\\ (Times New Roman 10pt): {output_path}")

            return GenerateDocResponse(
                success=True,
                tipo="ANEXO_IX",
                nombre_archivo=output_filename,
                ruta_archivo=str(output_path),
                url_descarga=f"/api/descargar/{output_filename}",
                mensaje=f"Anexo IX guardado correctamente en {output_path}"
            )
        except PermissionError:
            raise PermissionError(f"Sin permisos de escritura en la carpeta de destino en F:\\: {self.output_dir}")
        except Exception as e:
            raise RuntimeError(f"Error procesando la plantilla Anexo IX en la unidad F:\\: {str(e)}")

    def _apply_times_new_roman_10(self, file_path: Path):
        """Aplica Times New Roman tamaño 10 sin negrita a todos los párrafos y tablas del documento."""
        try:
            import docx
            from docx.shared import Pt
            from docx.oxml.ns import qn

            d = docx.Document(str(file_path))

            def style_paragraphs(paragraphs):
                for p in paragraphs:
                    for r in p.runs:
                        r.font.name = "Times New Roman"
                        r.font.size = Pt(10)
                        r.font.bold = False
                        rPr = r._r.get_or_add_rPr()
                        for b in rPr.findall(qn('w:b')):
                            rPr.remove(b)
                        rFonts = rPr.get_or_add_rFonts()
                        rFonts.set(qn('w:ascii'), 'Times New Roman')
                        rFonts.set(qn('w:hAnsi'), 'Times New Roman')
                        rFonts.set(qn('w:cs'), 'Times New Roman')

            style_paragraphs(d.paragraphs)
            for table in d.tables:
                for row in table.rows:
                    for cell in row.cells:
                        style_paragraphs(cell.paragraphs)

            d.save(str(file_path))
        except Exception as e:
            print(f"[AnexoIXAgent] Aviso al aplicar formato tipográfico: {e}")
            print(f"[AnexoIXAgent] Aviso al aplicar formato tipográfico: {e}")

