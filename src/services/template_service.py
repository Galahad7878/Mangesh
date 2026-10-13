import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex: str):
    """Aplica color de fondo a una celda de tabla."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Ajusta márgenes internos de una celda en dxa."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def set_cell_border(cell, **kwargs):
    """
    kwargs: top, bottom, left, right
    values: dict(sz=12, val='single', color='003366')
    """
    tcPr = cell._element.get_or_add_tcPr()
    tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}/>')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            b_xml = f'<w:{edge} {nsdecls("w")} w:val="{edge_data.get("val", "single")}" w:sz="{edge_data.get("sz", "4")}" w:space="0" w:color="{edge_data.get("color", "CCCCCC")}"/>'
            tcBorders.append(parse_xml(b_xml))
    tcPr.append(tcBorders)

class TemplateService:
    @staticmethod
    def get_data_dir() -> Path:
        base_dir = Path(__file__).resolve().parent.parent.parent
        data_dir = base_dir / "datos"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    @classmethod
    def ensure_templates_exist(cls):
        data_dir = cls.get_data_dir()
        loi_path = data_dir / "plantilla_loi.docx"
        anexo_docx = data_dir / "plantilla_anexo_ix.docx"
        anexo_doc = data_dir / "plantilla_anexo_ix.doc"

        # Si existe plantilla_anexo_ix.docx existente, usarla tal cual
        if anexo_docx.exists():
            print(f"[TemplateService] Usando plantilla existente Anexo IX: {anexo_docx}")
        elif anexo_doc.exists():
            # Convertir plantilla .doc existente del usuario a .docx mediante Word COM
            try:
                import win32com.client
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                doc = word.Documents.Open(str(anexo_doc.resolve()))
                doc.SaveAs2(str(anexo_docx.resolve()), 16)
                doc.Close()
                word.Quit()
                print(f"[TemplateService] Convertida plantilla existente de usuario {anexo_doc} a {anexo_docx}")
            except Exception as e:
                print(f"[TemplateService] Aviso: No se pudo convertir automáticamente con Word COM ({e}).")

        # Si plantilla_loi.docx ya existe, respetarla
        if loi_path.exists():
            print(f"[TemplateService] Usando plantilla existente LOI: {loi_path}")

    @classmethod
    def create_default_loi_template(cls, target_path: Path):
        doc = Document()
        
        # Margenes de pagina
        sections = doc.sections
        for s in sections:
            s.top_margin = Inches(0.8)
            s.bottom_margin = Inches(0.8)
            s.left_margin = Inches(0.8)
            s.right_margin = Inches(0.8)

        # Encabezado corporativo
        header = doc.add_paragraph()
        header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        h_run = header.add_run("MARITIME SHIPPING SERVICES & CREW LOGISTICS\nLAS PALMAS DE GRAN CANARIA - SPAIN")
        h_run.font.name = "Arial"
        h_run.font.size = Pt(8.5)
        h_run.font.color.rgb = RGBColor(100, 110, 125)

        # Titulo Principal
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_p.paragraph_format.space_before = Pt(12)
        title_p.paragraph_format.space_after = Pt(4)
        t_run = title_p.add_run("LETTER OF INVITATION / GUARANTEE")
        t_run.font.name = "Arial"
        t_run.font.size = Pt(16)
        t_run.font.bold = True
        t_run.font.color.rgb = RGBColor(10, 45, 90)

        sub_p = doc.add_paragraph()
        sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub_p.paragraph_format.space_after = Pt(14)
        s_run = sub_p.add_run("CARTA DE INVITACIÓN Y GARANTÍA PARA CAMBIO DE TRIPULACIÓN")
        s_run.font.name = "Arial"
        s_run.font.size = Pt(10)
        s_run.font.italic = True
        s_run.font.color.rgb = RGBColor(70, 80, 95)

        # Destinatario y Fecha
        meta_table = doc.add_table(rows=2, cols=2)
        meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        meta_table.autofit = False

        r0c0 = meta_table.cell(0, 0)
        r0c0.text = "TO: IMMIGRATION & BORDER POLICE AUTHORITIES\nA LA ATENCIÓN: AUTORIDADES POLICIALES Y FRONTERIZAS"
        r0c0.paragraphs[0].runs[0].font.size = Pt(8.5)
        r0c0.paragraphs[0].runs[0].font.bold = True

        r0c1 = meta_table.cell(0, 1)
        r0c1.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_f = r0c1.paragraphs[0].add_run("Fecha / Date: {{ fecha_emision }}")
        r_f.font.size = Pt(9)
        r_f.font.bold = True

        r1c0 = meta_table.cell(1, 0)
        r1c0.text = "PORT OF EMBARKATION / PUERTO: {{ puerto_embarque }}"
        r1c0.paragraphs[0].runs[0].font.size = Pt(9)
        r1c0.paragraphs[0].runs[0].font.bold = True
        r1c0.paragraphs[0].runs[0].font.color.rgb = RGBColor(10, 45, 90)

        r1c1 = meta_table.cell(1, 1)
        r1c1.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_op = r1c1.paragraphs[0].add_run("OPERACIÓN: {{ tipo_operacion }}")
        r_op.font.size = Pt(9)
        r_op.font.bold = True
        r_op.font.color.rgb = RGBColor(180, 40, 40)

        # Espaciado
        doc.add_paragraph().paragraph_format.space_after = Pt(6)

        # Declaracion principal
        p_decl = doc.add_paragraph()
        p_decl.paragraph_format.space_after = Pt(10)
        p_decl.paragraph_format.line_spacing = 1.15
        d_run = p_decl.add_run(
            "We hereby certify and confirm that the below-mentioned seafarer has been designated to join the vessel described below in the Port of Las Palmas (Spain) as a professional crew member under our agency assistance."
        )
        d_run.font.name = "Arial"
        d_run.font.size = Pt(9.5)

        # TABLA 1: DATOS DEL TRIPULANTE (CREW DETAILS)
        h_trip = doc.add_paragraph()
        h_trip.paragraph_format.space_before = Pt(8)
        h_trip.paragraph_format.space_after = Pt(4)
        ht_run = h_trip.add_run("1. CREW MEMBER PERSONAL DETAILS / DATOS DEL TRIPULANTE")
        ht_run.font.name = "Arial"
        ht_run.font.size = Pt(10.5)
        ht_run.font.bold = True
        ht_run.font.color.rgb = RGBColor(10, 45, 90)

        t_crew = doc.add_table(rows=6, cols=2)
        t_crew.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        crew_rows = [
            ("Full Name / Nombre Completo:", "{{ nombre_completo }}"),
            ("Rank & Position / Rango - Cargo:", "{{ rango_cargo }}"),
            ("Nationality / Nacionalidad:", "{{ nacionalidad }}"),
            ("Passport Number / Pasaporte:", "{{ pasaporte }} (Exp: {{ fecha_expedicion_pasaporte }} - Val: {{ validez_pasaporte }})"),
            ("Seaman's Book / Libreta Marítima:", "{{ libreta_maritima }} (Exp: {{ fecha_expedicion_libreta }} - Val: {{ validez_libreta }})"),
            ("Date & Place of Birth / Nacimiento:", "{{ fecha_nacimiento }} - {{ lugar_nacimiento }}")
        ]

        for i, (label, val) in enumerate(crew_rows):
            c_lbl = t_crew.cell(i, 0)
            c_lbl.width = Inches(2.6)
            c_val = t_crew.cell(i, 1)
            c_val.width = Inches(4.5)

            p0 = c_lbl.paragraphs[0]
            p0.paragraph_format.space_after = Pt(2)
            r0 = p0.add_run(label)
            r0.font.name = "Arial"
            r0.font.size = Pt(9)
            r0.font.bold = True
            r0.font.color.rgb = RGBColor(50, 60, 75)
            set_cell_background(c_lbl, "F0F4F8")

            p1 = c_val.paragraphs[0]
            p1.paragraph_format.space_after = Pt(2)
            r1 = p1.add_run(val)
            r1.font.name = "Arial"
            r1.font.size = Pt(9.5)
            r1.font.bold = True
            r1.font.color.rgb = RGBColor(15, 25, 40)
            
            set_cell_border(c_lbl, top={"sz": 4, "color": "D0D7DE"}, bottom={"sz": 4, "color": "D0D7DE"}, left={"sz": 4, "color": "D0D7DE"}, right={"sz": 4, "color": "D0D7DE"})
            set_cell_border(c_val, top={"sz": 4, "color": "D0D7DE"}, bottom={"sz": 4, "color": "D0D7DE"}, left={"sz": 4, "color": "D0D7DE"}, right={"sz": 4, "color": "D0D7DE"})

        # TABLA 2: DATOS DEL BUQUE (VESSEL DETAILS)
        h_vessel = doc.add_paragraph()
        h_vessel.paragraph_format.space_before = Pt(10)
        h_vessel.paragraph_format.space_after = Pt(4)
        hv_run = h_vessel.add_run("2. VESSEL INFORMATION / DATOS DEL BUQUE")
        hv_run.font.name = "Arial"
        hv_run.font.size = Pt(10.5)
        hv_run.font.bold = True
        hv_run.font.color.rgb = RGBColor(10, 45, 90)

        t_vessel = doc.add_table(rows=3, cols=2)
        t_vessel.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        vessel_rows = [
            ("Vessel Name / Nombre del Buque:", "{{ buque }}"),
            ("Flag / IMO Number / Bandera - IMO:", "{{ bandera }} / {{ imo }}"),
            ("Expected Boarding Date / Fecha Embarque:", "{{ fecha_embarque }} en {{ puerto_embarque }}")
        ]

        for i, (label, val) in enumerate(vessel_rows):
            c_lbl = t_vessel.cell(i, 0)
            c_lbl.width = Inches(2.6)
            c_val = t_vessel.cell(i, 1)
            c_val.width = Inches(4.5)

            p0 = c_lbl.paragraphs[0]
            p0.paragraph_format.space_after = Pt(2)
            r0 = p0.add_run(label)
            r0.font.name = "Arial"
            r0.font.size = Pt(9)
            r0.font.bold = True
            r0.font.color.rgb = RGBColor(50, 60, 75)
            set_cell_background(c_lbl, "F0F4F8")

            p1 = c_val.paragraphs[0]
            p1.paragraph_format.space_after = Pt(2)
            r1 = p1.add_run(val)
            r1.font.name = "Arial"
            r1.font.size = Pt(9.5)
            r1.font.bold = True
            r1.font.color.rgb = RGBColor(15, 25, 40)
            
            set_cell_border(c_lbl, top={"sz": 4, "color": "D0D7DE"}, bottom={"sz": 4, "color": "D0D7DE"}, left={"sz": 4, "color": "D0D7DE"}, right={"sz": 4, "color": "D0D7DE"})
            set_cell_border(c_val, top={"sz": 4, "color": "D0D7DE"}, bottom={"sz": 4, "color": "D0D7DE"}, left={"sz": 4, "color": "D0D7DE"}, right={"sz": 4, "color": "D0D7DE"})

        # TABLA 3: ITINERARIO DE VUELO (FLIGHT DETAILS)
        h_flight = doc.add_paragraph()
        h_flight.paragraph_format.space_before = Pt(10)
        h_flight.paragraph_format.space_after = Pt(4)
        hf_run = h_flight.add_run("3. FLIGHT ITINERARY / ITINERARIO DE VUELO")
        hf_run.font.name = "Arial"
        hf_run.font.size = Pt(10.5)
        hf_run.font.bold = True
        hf_run.font.color.rgb = RGBColor(10, 45, 90)

        p_itinerario = doc.add_paragraph()
        p_itinerario.paragraph_format.space_after = Pt(6)
        r_it = p_itinerario.add_run("Resumen: {{ itinerario_resumen }}")
        r_it.font.name = "Arial"
        r_it.font.size = Pt(9)
        r_it.font.italic = True

        t_flight = doc.add_table(rows=2, cols=4)
        t_flight.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        headers = ["Vuelo / Flight", "Ruta / Route", "Salida / Dep", "Llegada / Arr"]
        for j, h in enumerate(headers):
            cell = t_flight.cell(0, j)
            set_cell_background(cell, "0A2D5A")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(h)
            r.font.name = "Arial"
            r.font.size = Pt(8.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

        # Fila de bucle Jinja para docxtpl
        f_row = t_flight.rows[1]
        c0 = f_row.cells[0]
        c0.text = "{% for v in vuelos %}{{ v.numero_vuelo }} ({{ v.aerolinea }})"
        c1 = f_row.cells[1]
        c1.text = "{{ v.origen }} -> {{ v.destino }}"
        c2 = f_row.cells[2]
        c2.text = "{{ v.fecha_salida }} {{ v.hora_salida }}"
        c3 = f_row.cells[3]
        c3.text = "{{ v.fecha_llegada }} {{ v.hora_llegada }}{% endfor %}"

        for cell in f_row.cells:
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in cell.paragraphs[0].runs:
                r.font.size = Pt(8.5)
            set_cell_border(cell, top={"sz": 4, "color": "D0D7DE"}, bottom={"sz": 4, "color": "D0D7DE"}, left={"sz": 4, "color": "D0D7DE"}, right={"sz": 4, "color": "D0D7DE"})

        # Clausula de Garantia y Firma
        doc.add_paragraph().paragraph_format.space_before = Pt(8)
        p_guar = doc.add_paragraph()
        p_guar.paragraph_format.line_spacing = 1.15
        p_guar.paragraph_format.space_after = Pt(14)
        rg = p_guar.add_run(
            "GUARANTEE CLAUSE: We, {{ agente_maritimo }}, act as nominated shipping agents and solemnly declare that all living expenses, accommodation, medical costs (if any) and repatriation costs are fully guaranteed by our agency and the vessel's principals."
        )
        rg.font.name = "Arial"
        rg.font.size = Pt(8.5)
        rg.font.italic = True
        rg.font.color.rgb = RGBColor(60, 70, 80)

        # Firma
        p_sign = doc.add_paragraph()
        p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_sign.paragraph_format.space_before = Pt(12)
        rs1 = p_sign.add_run("_________________________________________\n")
        rs1.font.bold = True
        rs2 = p_sign.add_run("Por {{ agente_maritimo }}\nDEPARTMENT OF CREW OPERATIONS & LOGISTICS\nTel: {{ contacto_agencia }}")
        rs2.font.name = "Arial"
        rs2.font.size = Pt(8.5)
        rs2.font.bold = True
        rs2.font.color.rgb = RGBColor(10, 45, 90)

        doc.save(str(target_path))

    @classmethod
    def create_default_anexo_ix_template(cls, target_path: Path):
        doc = Document()
        
        # Margenes de pagina
        sections = doc.sections
        for s in sections:
            s.top_margin = Inches(0.7)
            s.bottom_margin = Inches(0.7)
            s.left_margin = Inches(0.7)
            s.right_margin = Inches(0.7)

        # Encabezado Oficial Anexo IX
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_p.paragraph_format.space_after = Pt(2)
        t_run = title_p.add_run("ANEXO IX / ANNEX IX")
        t_run.font.name = "Arial"
        t_run.font.size = Pt(14)
        t_run.font.bold = True
        t_run.font.color.rgb = RGBColor(0, 51, 102)

        sub_p = doc.add_paragraph()
        sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub_p.paragraph_format.space_after = Pt(12)
        s_run = sub_p.add_run("SOLICITUD DE EXPEDICIÓN DE VISADO EN FRONTERA A MARINEROS EN TRÁNSITO\n(Código de Fronteras Schengen - Reglamento UE)")
        s_run.font.name = "Arial"
        s_run.font.size = Pt(9.5)
        s_run.font.bold = True
        s_run.font.color.rgb = RGBColor(50, 50, 50)

        # Cuadro de Informacion Fronteriza
        t_main = doc.add_table(rows=12, cols=2)
        t_main.alignment = WD_TABLE_ALIGNMENT.CENTER

        rows_data = [
            ("Puesto Fronterizo / Border Post:", "{{ puerto_embarque }} - Puesto Fronterizo Marítimo"),
            ("Fecha de Solicitud / Application Date:", "{{ fecha_emision }}"),
            ("Apellidos / Surnames:", "{{ apellidos }}"),
            ("Nombre / First Name:", "{{ nombre }}"),
            ("Nacionalidad / Nationality:", "{{ nacionalidad }}"),
            ("Fecha y Lugar de Nacimiento:", "{{ fecha_nacimiento }} - {{ lugar_nacimiento }}"),
            ("Documento de Viaje / Pasaporte:", "{{ pasaporte }} (Expedición: {{ fecha_expedicion_pasaporte }} - Caducidad: {{ validez_pasaporte }})"),
            ("Libreta Marítima / Seaman's Book:", "{{ libreta_maritima }} (Expedición: {{ fecha_expedicion_libreta }} - Caducidad: {{ validez_libreta }})"),
            ("Rango o Función a Bordo / Rank:", "{{ rango_cargo }}"),
            ("Buque de Destino / Vessel:", "{{ buque }} (Bandera: {{ bandera }} - IMO: {{ imo }})"),
            ("Fecha Prevista de Tránsito / Embarque:", "{{ fecha_embarque }}"),
            ("Agencia Marítima Garante:", "{{ agente_maritimo }} (Contacto: {{ contacto_agencia }})")
        ]

        for i, (label, val) in enumerate(rows_data):
            c_lbl = t_main.cell(i, 0)
            c_lbl.width = Inches(2.8)
            c_val = t_main.cell(i, 1)
            c_val.width = Inches(4.3)

            p0 = c_lbl.paragraphs[0]
            p0.paragraph_format.space_after = Pt(2)
            r0 = p0.add_run(label)
            r0.font.name = "Arial"
            r0.font.size = Pt(8.5)
            r0.font.bold = True
            r0.font.color.rgb = RGBColor(40, 50, 65)
            set_cell_background(c_lbl, "EAEFF5")

            p1 = c_val.paragraphs[0]
            p1.paragraph_format.space_after = Pt(2)
            r1 = p1.add_run(val)
            r1.font.name = "Arial"
            r1.font.size = Pt(9)
            r1.font.bold = True
            r1.font.color.rgb = RGBColor(10, 20, 30)

            set_cell_border(c_lbl, top={"sz": 4, "color": "B0C0D0"}, bottom={"sz": 4, "color": "B0C0D0"}, left={"sz": 4, "color": "B0C0D0"}, right={"sz": 4, "color": "B0C0D0"})
            set_cell_border(c_val, top={"sz": 4, "color": "B0C0D0"}, bottom={"sz": 4, "color": "B0C0D0"}, left={"sz": 4, "color": "B0C0D0"}, right={"sz": 4, "color": "B0C0D0"})

        # Sección de Vuelos de Entrada
        doc.add_paragraph().paragraph_format.space_before = Pt(6)
        h_flights = doc.add_paragraph()
        h_flights.paragraph_format.space_after = Pt(3)
        hf_r = h_flights.add_run("DATOS DEL VIAJE DE ENTRADA / INBOUND FLIGHT DETAILS")
        hf_r.font.name = "Arial"
        hf_r.font.size = Pt(9.5)
        hf_r.font.bold = True
        hf_r.font.color.rgb = RGBColor(0, 51, 102)

        t_f = doc.add_table(rows=2, cols=4)
        t_f.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        heads = ["Compañía / Vuelo", "Itinerario", "Salida", "Llegada"]
        for j, h in enumerate(heads):
            cell = t_f.cell(0, j)
            set_cell_background(cell, "334466")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(h)
            r.font.name = "Arial"
            r.font.size = Pt(8)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

        f_row = t_f.rows[1]
        f_row.cells[0].text = "{% for v in vuelos %}{{ v.aerolinea }} {{ v.numero_vuelo }}"
        f_row.cells[1].text = "{{ v.origen }} - {{ v.destino }}"
        f_row.cells[2].text = "{{ v.fecha_salida }} {{ v.hora_salida }}"
        f_row.cells[3].text = "{{ v.fecha_llegada }} {{ v.hora_llegada }}{% endfor %}"

        for cell in f_row.cells:
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in cell.paragraphs[0].runs:
                r.font.size = Pt(8)
            set_cell_border(cell, top={"sz": 4, "color": "B0C0D0"}, bottom={"sz": 4, "color": "B0C0D0"}, left={"sz": 4, "color": "B0C0D0"}, right={"sz": 4, "color": "B0C0D0"})

        # Compromiso de la Agencia
        doc.add_paragraph().paragraph_format.space_before = Pt(6)
        p_comp = doc.add_paragraph()
        p_comp.paragraph_format.space_after = Pt(10)
        p_comp.paragraph_format.line_spacing = 1.1
        rc = p_comp.add_run(
            "COMPROMISO: La agencia marítima solicitante garantiza la veracidad de los datos, asume la custodia del marinero desde su llegada hasta su efectivo embarque a bordo del buque citado, y se responsabiliza de todos los gastos de estancia y eventual repatriación con arreglo a la normativa Schengen."
        )
        rc.font.name = "Arial"
        rc.font.size = Pt(8)
        rc.font.italic = True
        rc.font.color.rgb = RGBColor(70, 70, 70)

        # Doble cuadro de firmas
        t_sig = doc.add_table(rows=1, cols=2)
        t_sig.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        sig0 = t_sig.cell(0, 0)
        sig0.paragraphs[0].text = "Sello y Firma del Agente Garante:\n\n\n_________________________________\n{{ agente_maritimo }}"
        sig0.paragraphs[0].runs[0].font.size = Pt(8)
        sig0.paragraphs[0].runs[0].font.bold = True
        
        sig1 = t_sig.cell(0, 1)
        sig1.paragraphs[0].text = "Resolución del Puesto Fronterizo (Policía Nacional):\n\n[  ] AUTORIZADO   /   [  ] DENEGADO\nFirma / Número de Carné Profesional:"
        sig1.paragraphs[0].runs[0].font.size = Pt(8)
        sig1.paragraphs[0].runs[0].font.bold = True

        doc.save(str(target_path))
