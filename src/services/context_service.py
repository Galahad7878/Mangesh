import re
from datetime import datetime, timedelta
from typing import Dict, Any
from src.models import CrewMemberData

MONTHS_EXPANDED = {
    'JAN': 1, 'JANUARY': 1, 'ENE': 1, 'ENERO': 1,
    'FEB': 2, 'FEBRUARY': 2, 'FEBRERO': 2,
    'MAR': 3, 'MARCH': 3, 'MARZO': 3,
    'APR': 4, 'APRIL': 4, 'ABR': 4, 'ABRIL': 4,
    'MAY': 5, 'MAYO': 5,
    'JUN': 6, 'JUNE': 6, 'JUNIO': 6,
    'JUL': 7, 'JULY': 7, 'JULIO': 7,
    'AUG': 8, 'AUGUST': 8, 'AGO': 8, 'AGOSTO': 8,
    'SEP': 9, 'SEPTEMBER': 9, 'SEPTIEMBRE': 9, 'SEPT': 9,
    'OCT': 10, 'OCTOBER': 10, 'OCTUBRE': 10,
    'NOV': 11, 'NOVEMBER': 11, 'NOVIEMBRE': 11,
    'DEC': 12, 'DECEMBER': 12, 'DICIEMBRE': 12, 'DIC': 12
}

def parse_any_date(date_str: str) -> datetime:
    if not date_str:
        return datetime.now()
    clean = str(date_str).strip().upper()
    # Limpiar sufijos ordinales ingleses: 25th -> 25, 1st -> 1, 2nd -> 2, 3rd -> 3
    clean = re.sub(r'(\d+)(?:ST|ND|RD|TH)\b', r'\1', clean)

    # 1. ISO format: YYYY-MM-DD o YYYY/MM/DD
    m_iso = re.match(r'^([0-9]{4})[\/\.\-]([0-9]{1,2})[\/\.\-]([0-9]{1,2})', clean)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        return datetime(y, m, d)

    # 2. Formato día-mes-año (ej. 25th October 2026, 25-OCT-2026, 25OCT2026)
    m_mon1 = re.search(r'([0-9]{1,2})\s*[-/\s]?\s*([A-Z]{3,12})\s*[-/\s]?\s*([0-9]{2,4})?', clean)
    if m_mon1 and m_mon1.group(2) in MONTHS_EXPANDED:
        d = int(m_mon1.group(1))
        m = MONTHS_EXPANDED[m_mon1.group(2)]
        raw_y = m_mon1.group(3)
        y = int(raw_y) if raw_y else datetime.now().year
        if y < 100: y += 2000
        return datetime(y, m, d)

    # 2b. Formato mes-día-año (ej. October 25, 2026)
    m_mon2 = re.search(r'([A-Z]{3,12})\s+([0-9]{1,2})(?:[,\s]+([0-9]{2,4}))?', clean)
    if m_mon2 and m_mon2.group(1) in MONTHS_EXPANDED:
        m = MONTHS_EXPANDED[m_mon2.group(1)]
        d = int(m_mon2.group(2))
        raw_y = m_mon2.group(3)
        y = int(raw_y) if raw_y else datetime.now().year
        if y < 100: y += 2000
        return datetime(y, m, d)

    # 3. Formato estándar europeo: DD/MM/YYYY o DD-MM-YYYY
    m_eu = re.search(r'([0-9]{1,2})[\/\.\-]([0-9]{1,2})(?:[\/\.\-]([0-9]{2,4}))?', clean)
    if m_eu:
        d = int(m_eu.group(1))
        m = int(m_eu.group(2))
        raw_y = m_eu.group(3)
        y = int(raw_y) if raw_y else datetime.now().year
        if y < 100: y += 2000
        return datetime(y, m, d)

    return datetime.now()

def resolve_flight_date(date_str: str, now: datetime = None) -> str:
    """
    Determina de forma inteligente el año de un vuelo:
    Si la fecha (día, mes) ya ha pasado en el año actual,
    entonces se entiende que el vuelo será el año siguiente.
    """
    if not date_str:
        return ""
    if now is None:
        now = datetime.now()

    clean = str(date_str).strip().upper()
    clean = re.sub(r'(\d+)(?:ST|ND|RD|TH)\b', r'\1', clean)

    d, m, raw_y = None, None, None

    # 1. Formato ISO: YYYY-MM-DD o YYYY/MM/DD
    m_iso = re.match(r'^([0-9]{4})[\/\.\-]([0-9]{1,2})[\/\.\-]([0-9]{1,2})', clean)
    if m_iso:
        raw_y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))

    # 2. Formato día-mes con texto (ej. 15JAN, 25OCT2026, 15-JAN, 15 JAN)
    if d is None:
        m_mon1 = re.search(r'([0-9]{1,2})\s*[-/\s]?\s*([A-Z]{3,12})\s*[-/\s]?\s*([0-9]{2,4})?', clean)
        if m_mon1 and m_mon1.group(2) in MONTHS_EXPANDED:
            d = int(m_mon1.group(1))
            m = MONTHS_EXPANDED[m_mon1.group(2)]
            raw_y = int(m_mon1.group(3)) if m_mon1.group(3) else None

    # 2b. Formato mes-día con texto (ej. January 15)
    if d is None:
        m_mon2 = re.search(r'([A-Z]{3,12})\s+([0-9]{1,2})(?:[,\s]+([0-9]{2,4}))?', clean)
        if m_mon2 and m_mon2.group(1) in MONTHS_EXPANDED:
            m = MONTHS_EXPANDED[m_mon2.group(1)]
            d = int(m_mon2.group(2))
            raw_y = int(m_mon2.group(3)) if m_mon2.group(3) else None

    # 3. Formato estándar numérico: DD/MM o DD/MM/YYYY
    if d is None:
        m_eu = re.search(r'([0-9]{1,2})[\/\.\-]([0-9]{1,2})(?:[\/\.\-]([0-9]{2,4}))?', clean)
        if m_eu:
            d = int(m_eu.group(1))
            m = int(m_eu.group(2))
            raw_y = int(m_eu.group(3)) if m_eu.group(3) else None

    if d is None or m is None:
        return format_ddmmyyyy(date_str)

    if raw_y and raw_y < 100:
        raw_y += 2000

    # REGLA: Si la fecha (día, mes) ya ha pasado en el año actual, será el año siguiente
    try:
        current_year_date = datetime(now.year, m, d).date()
    except ValueError:
        current_year_date = datetime(now.year, m, 28).date()

    if raw_y and raw_y > now.year:
        year = raw_y
    else:
        if current_year_date < now.date():
            year = now.year + 1
        else:
            year = now.year

    try:
        final_dt = datetime(year, m, d)
        return final_dt.strftime("%d/%m/%Y")
    except ValueError:
        return f"{d:02d}/{m:02d}/{year}"

def format_ddmmyyyy(date_str: str) -> str:
    try:
        dt = parse_any_date(date_str)
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return datetime.now().strftime("%d/%m/%Y")

def calculate_next_day(date_str: str) -> str:
    try:
        dt = parse_any_date(date_str)
        return (dt + timedelta(days=1)).strftime("%d/%m/%Y")
    except Exception:
        return (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

def build_template_context(crew: CrewMemberData) -> Dict[str, Any]:
    """
    Construye un diccionario de contexto robusto y enriquecido para Jinja2 / docxtpl,
    con soporte completo para dos tramos de vuelos y cálculo de fecha de desembarque.
    """
    fecha_embarque = resolve_flight_date(crew.fecha_embarque) if crew.fecha_embarque else datetime.now().strftime("%d/%m/%Y")
    
    fecha_desembarque_raw = crew.fecha_desembarque.strip() if crew.fecha_desembarque else ""
    # REGLA ESTRICTA: si fecha_desembarque está vacía o es igual a fecha_embarque,
    # debe ser obligatoriamente el día siguiente a fecha_embarque (+1 día)
    if not fecha_desembarque_raw or fecha_desembarque_raw == fecha_embarque or fecha_desembarque_raw == crew.fecha_embarque.strip():
        fecha_desembarque = calculate_next_day(fecha_embarque)
    else:
        fecha_desembarque = resolve_flight_date(fecha_desembarque_raw)

    # Desglose de los dos tramos de vuelo
    v1 = crew.vuelos[0] if len(crew.vuelos) > 0 else None
    v2 = crew.vuelos[1] if len(crew.vuelos) > 1 else None

    # Tramo 1
    v1_num = v1.numero_vuelo.strip() if v1 else ""
    v1_air = v1.aerolinea.strip() if v1 else ""
    v1_orig = v1.origen.strip() if v1 else ""
    v1_dest = v1.destino.strip() if v1 else ""
    v1_f_sal = resolve_flight_date(v1.fecha_salida) if (v1 and v1.fecha_salida) else ""
    v1_h_sal = v1.hora_salida.strip() if v1 else ""
    v1_f_lleg = resolve_flight_date(v1.fecha_llegada) if (v1 and v1.fecha_llegada) else (v1_f_sal or "")
    v1_h_lleg = v1.hora_llegada.strip() if v1 else ""
    vuelo_1 = f"{v1_num} {v1_f_sal} {v1_orig} - {v1_dest} ({v1_h_sal} - {v1_h_lleg})".strip() if v1 else ""

    # Tramo 2
    v2_num = v2.numero_vuelo.strip() if v2 else ""
    v2_air = v2.aerolinea.strip() if v2 else ""
    v2_orig = v2.origen.strip() if v2 else ""
    v2_dest = v2.destino.strip() if v2 else ""
    v2_f_sal = resolve_flight_date(v2.fecha_salida) if (v2 and v2.fecha_salida) else ""
    v2_h_sal = v2.hora_salida.strip() if v2 else ""
    v2_f_lleg = resolve_flight_date(v2.fecha_llegada) if (v2 and v2.fecha_llegada) else (v2_f_sal or "")
    v2_h_lleg = v2.hora_llegada.strip() if v2 else ""
    vuelo_2 = f"{v2_num} {v2_f_sal} {v2_orig} - {v2_dest} ({v2_h_sal} - {v2_h_lleg})".strip() if v2 else ""

    vuelos_detalle = f"{vuelo_1}\n{vuelo_2}".strip() if (vuelo_1 and vuelo_2) else (vuelo_1 or vuelo_2)

    return {
        # 1. Datos Personales
        "nombre": crew.nombre.strip(),
        "apellidos": crew.apellidos.strip(),
        "nombre_completo": crew.nombre_completo.strip() or f"{crew.nombre} {crew.apellidos}".strip(),
        "rango_cargo": crew.rango_cargo.strip(),
        "nacionalidad": crew.nacionalidad.strip(),
        "fecha_nacimiento": crew.fecha_nacimiento.strip(),
        "lugar_nacimiento": crew.lugar_nacimiento.strip(),

        # 2. Documentos
        "pasaporte": crew.pasaporte.strip(),
        "fecha_expedicion_pasaporte": crew.fecha_expedicion_pasaporte.strip(),
        "validez_pasaporte": crew.validez_pasaporte.strip(),
        "libreta_maritima": crew.libreta_maritima.strip(),
        "fecha_expedicion_libreta": crew.fecha_expedicion_libreta.strip(),
        "validez_libreta": crew.validez_libreta.strip(),

        # 3. Buque y Operativa
        "buque": crew.buque.strip(),
        "bandera": crew.bandera.strip(),
        "imo": crew.imo.strip(),
        "puerto_embarque": crew.puerto_embarque.strip(),
        "fecha_embarque": crew.fecha_embarque.strip(),
        "fecha_desembarque": fecha_desembarque,
        "fecha_salida_buque": fecha_desembarque,
        "tipo_operacion": crew.tipo_operacion.strip() if crew.tipo_operacion else "EMBARQUE",
        "agente_maritimo": crew.agente_maritimo.strip() if crew.agente_maritimo else "AGENCIA MARÍTIMA CANARIAS S.L.",
        "contacto_agencia": crew.contacto_agencia.strip() if crew.contacto_agencia else "+34 928 123 456 / ops@agenciamaritima.es",

        # 4. Tramo 1 (Campos específicos y amigables)
        "v1_numero_vuelo": v1_num,
        "v1_aerolinea": v1_air,
        "v1_origen": v1_orig,
        "v1_destino": v1_dest,
        "v1_fecha_salida": v1_f_sal,
        "v1_hora_salida": v1_h_sal,
        "v1_fecha_llegada": v1_f_lleg,
        "v1_hora_llegada": v1_h_lleg,
        "vuelo_1": vuelo_1,
        "tramo1_vuelo": v1_num,
        "tramo1_aerolinea": v1_air,
        "tramo1_origen": v1_orig,
        "tramo1_destino": v1_dest,
        "tramo1_fecha": v1_f_sal,
        "tramo1_salida": v1_h_sal,
        "tramo1_llegada": v1_h_lleg,

        # 5. Tramo 2 (Campos específicos y amigables)
        "v2_numero_vuelo": v2_num,
        "v2_aerolinea": v2_air,
        "v2_origen": v2_orig,
        "v2_destino": v2_dest,
        "v2_fecha_salida": v2_f_sal,
        "v2_hora_salida": v2_h_sal,
        "v2_fecha_llegada": v2_f_lleg,
        "v2_hora_llegada": v2_h_lleg,
        "vuelo_2": vuelo_2,
        "tramo2_vuelo": v2_num,
        "tramo2_aerolinea": v2_air,
        "tramo2_origen": v2_orig,
        "tramo2_destino": v2_dest,
        "tramo2_fecha": v2_f_sal,
        "tramo2_salida": v2_h_sal,
        "tramo2_llegada": v2_h_lleg,

        # 6. Resúmenes de Vuelos
        "vuelos_detalle": vuelos_detalle,
        "itinerario_resumen": crew.itinerario_resumen.strip() or vuelos_detalle,
        "itinerario_completo": vuelos_detalle,

        # 7. Compatibilidad directa para la plantilla LOI existente
        # {{ numero_vuelo }} {{ fecha_salida }} {{ origen }} {{ destino }} {{ hora_salida }} {{ hora_llegada }}
        "numero_vuelo": f"{v1_num} // {v2_num}" if (v1_num and v2_num) else (v1_num or v2_num),
        "aerolinea": f"{v1_air} // {v2_air}" if (v1_air and v2_air) else (v1_air or v2_air),
        "origen": f"{v1_orig} (via {v1_dest})" if (v1_orig and v1_dest != v2_dest) else v1_orig,
        "destino": v2_dest or v1_dest,
        "fecha_salida": v1_f_sal,
        "hora_salida": v1_h_sal,
        "fecha_llegada": v2_f_lleg or v1_f_lleg,
        "hora_llegada": v2_h_lleg or v1_h_lleg,

        # 8. Lista de vuelos iterable para {% for v in vuelos %}
        "vuelos": [v.model_dump() for v in crew.vuelos],

        # 9. Fecha de emisión
        "fecha_emision": crew.fecha_emision.strip() if crew.fecha_emision else datetime.now().strftime("%d/%m/%Y")
    }
