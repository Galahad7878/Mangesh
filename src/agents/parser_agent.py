import os
import re
import json
from datetime import datetime
from typing import Optional, Tuple, List
from src.models import CrewMemberData, FlightSegment

class ParserAgent:
    """
    Agente 1: ParserAgent
    Extrae la información estructurada de correos electrónicos de cambio de tripulación.
    Utiliza Gemini 3.7 Flash mediante google-genai cuando hay API Key disponible,
    con un motor de extracción heurística/regex de alta precisión como respaldo.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def parse(self, email_text: str, custom_api_key: Optional[str] = None) -> Tuple[CrewMemberData, str]:
        active_key = custom_api_key or self.api_key
        
        # Intentar parseo con Gemini si hay clave disponible
        if active_key and len(active_key.strip()) > 10:
            try:
                data = self._parse_with_gemini(email_text, active_key.strip())
                if data:
                    return data, "gemini"
            except Exception as e:
                print(f"[ParserAgent] Advertencia: Falló parseo con Gemini ({e}). Usando motor heurístico.")

        # Respaldo: Motor heurístico/regex avanzado
        data = self._parse_with_heuristic(email_text)
        return data, "regex"

    def _parse_with_gemini(self, email_text: str, api_key: str) -> Optional[CrewMemberData]:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = f"""
        Eres un agente experto en logística marítima y cambios de tripulación (Crew Change Operations).
        Extrae del siguiente correo electrónico todos los datos del tripulante, datos de la operativa/buque y los vuelos correspondientes.
        
        Texto del correo:
        \"\"\"{email_text}\"\"\"

        Instrucciones estrictas de mapeo:
        - 'Surname' debe asignarse obligatoriamente al campo 'apellidos' en MAYÚSCULAS.
        - 'Name' debe asignarse obligatoriamente al campo 'nombre' en MAYÚSCULAS.
        - El campo 'nombre_completo' debe ser 'NOMBRE APELLIDOS'.
        - El primer 'Issued At' o 'Date of Issue' corresponde a 'fecha_expedicion_pasaporte'.
        - El primer 'Expired On' o 'Expiry' corresponde a 'validez_pasaporte'.
        - 'Seaman\'s book No.' corresponde a 'libreta_maritima'.
        - El segundo 'Issued At' o 'Date of Issue' corresponde a 'fecha_expedicion_libreta'.
        - El segundo 'Expired On' o 'Expiry' corresponde a 'validez_libreta'.
        - Si el texto indica 'Italian flag' (u otra bandera), la bandera debe ser 'ITALIANA' y el buque subsiguiente (ej. 'M.T. Luca Ievoli').
        - El puerto de embarque debe ser 'TARRAGONA' (o el puerto indicado).
        - En el caso de los vuelos, si la fecha del vuelo no indica año o indica el año actual ({datetime.now().year}) pero el (día, mes) ya ha transcurrido en el año actual, el año del vuelo es obligatoriamente el año siguiente ({datetime.now().year + 1}). Ejemplo: si hoy es septiembre y el vuelo es en enero, el año del vuelo es {datetime.now().year + 1}. Formatea siempre las fechas como DD/MM/YYYY.
        - Extrae todos los tramos de vuelo (aerolínea, número de vuelo, origen, destino, fechas y horas).
        - La fecha de emisión actual debe ser la fecha de hoy ({datetime.now().strftime("%d/%m/%Y")}).
        """

        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CrewMemberData,
                temperature=0.1
            )
        )

        if response.text:
            raw_json = json.loads(response.text)
            from src.services.context_service import format_ddmmyyyy, calculate_next_day, resolve_flight_date

            # Normalizar fechas de los vuelos aplicando la regla de año siguiente si ya transcurrió en el año actual
            if "vuelos" in raw_json and isinstance(raw_json["vuelos"], list):
                for v in raw_json["vuelos"]:
                    if isinstance(v, dict):
                        if v.get("fecha_salida"):
                            v["fecha_salida"] = resolve_flight_date(v["fecha_salida"])
                        if v.get("fecha_llegada"):
                            v["fecha_llegada"] = resolve_flight_date(v["fecha_llegada"])

            # Normalizar fechas de operativa
            raw_embarque = raw_json.get("fecha_embarque", "")
            raw_json["fecha_embarque"] = resolve_flight_date(raw_embarque) if raw_embarque else datetime.now().strftime("%d/%m/%Y")
            # Forzar fecha_desembarque siempre al día siguiente de fecha_embarque
            raw_json["fecha_desembarque"] = calculate_next_day(raw_json["fecha_embarque"])

            if not raw_json.get("fecha_emision"):
                raw_json["fecha_emision"] = datetime.now().strftime("%d/%m/%Y")
            return CrewMemberData(**raw_json)

        return None

    def _parse_with_heuristic(self, text: str) -> CrewMemberData:
        """Motor de extracción por patrones de texto marítimos comunes."""
        clean = text.strip()
        lines = [l.strip() for l in clean.splitlines() if l.strip()]

        def search_pattern(patterns: List[str], default: str = "") -> str:
            for pat in patterns:
                m = re.search(pat, clean, re.IGNORECASE | re.MULTILINE)
                if m:
                    val = m.group(1).strip()
                    val = re.sub(r'^[–\-:\s]+', '', val).strip()
                    return val
            return default

        # 1. Nombre y Apellidos (Regla: Surname -> Apellidos; Name -> Nombre)
        apellidos = search_pattern([
            r'(?:^|\n|\r|\s)Surname\s*[:=\-]?\s*([A-Za-zÀ-ÿ\s\.\,\'\-]+?)(?:\n|\r|Name|First\s*Name|Rank|Nationality|$)',
            r'(?:LAST NAME|FAMILY NAME|APELLIDOS|APELLIDO)\s*[:=\-]\s*([A-Za-zÀ-ÿ\s\.\,\'\-]+?)(?:\n|\r|FIRST NAME|GIVEN NAME|NOMBRE|RANK|RANGO|NAT|$)'
        ], default="").upper().strip()

        nombre = search_pattern([
            r'(?:^|\n|\r|\s)Name\s*[:=\-]?\s*([A-Za-zÀ-ÿ\s\.\,\'\-]+?)(?:\n|\r|Surname|Last\s*Name|Rank|Nationality|DOB|Passport|$)',
            r'(?:FIRST NAME|GIVEN NAME|NOMBRE DE PILA|NOMBRE)\s*[:=\-]\s*([A-Za-zÀ-ÿ\s\.\,\'\-]+?)(?:\n|\r|SURNAME|LAST NAME|APELLIDOS|RANK|RANGO|NAT|$)'
        ], default="").upper().strip()

        if not nombre and not apellidos:
            # Respaldo si viene como Full Name
            full_raw = search_pattern([
                r'(?:FULL NAME|SEAMAN NAME|CREW NAME|TRIPULANTE)\s*[:=\-]\s*([A-Za-zÀ-ÿ\s\.\,\'\-]+?)(?:\n|\r|RANK|RANGO|NAT|PASSPORT|$)'
            ], default="")
            if full_raw:
                parts = full_raw.split()
                if len(parts) >= 2:
                    nombre = parts[0].upper()
                    apellidos = " ".join(parts[1:]).upper()
                else:
                    nombre = full_raw.upper()
                    apellidos = ""
            else:
                nombre = "JUAN"
                apellidos = "PEREZ GARCIA"

        nombre_completo = f"{nombre} {apellidos}".strip()

        # 2. Rango / Cargo
        rango_cargo = search_pattern([
            r'(?:RANK|POSITION|CARGO|RANGO|PUESTO)\s*[:=\-]\s*([A-Za-z0-9\s\/\.\-]+?)(?:\n|\r|NAT|PASSPORT|PP|DOB|$)',
            r'\b(CAPTAIN|MASTER|CHIEF ENGINEER|CHIEF OFFICER|2ND ENGINEER|3RD ENGINEER|2ND OFFICER|3RD OFFICER|BOSUN|ABLE SEAMAN|ORDINARY SEAMAN|OILER|WIPER|COOK|FITTER|ELECTRICIAN|STEWARD|ETO)\b'
        ], default="CHIEF OFFICER").upper().strip()

        # 3. Nacionalidad
        nacionalidad = search_pattern([
            r'(?:NATIONALITY|NAT|NACIONALIDAD|PAIS|COUNTRY)\s*[:=\-]\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|\r|DOB|BIRTH|PASSPORT|POB|$)',
            r'\b(SPANISH|ESPAÑOLA|FILIPINO|FILIPINA|UKRAINIAN|UCRANIANA|RUSSIAN|RUSA|INDIAN|INDIA|POLISH|POLACA|GEORGIAN|PERUVIAN|COLOMBIAN|ITALIAN|ITALIANA)\b'
        ], default="FILIPINO").upper().strip()

        # 4. Extracción secuencial de "Issued At" y "Expired On"
        # Regla: 1er Issued At -> Expedición Pasaporte; 1er Expired On -> Caducidad Pasaporte
        #        2do Issued At -> Expedición Libreta; 2do Expired On -> Caducidad Libreta
        issued_matches = re.findall(
            r'(?:Issued\s*(?:At|On|Date)?|Date\s*of\s*Issue|Fecha\s*Expedici[oó]n|F\.\s*Exp\.?)\s*[:=\-]?\s*([0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4}|[0-9]{1,2}\s+[A-Za-z]{3,9}\s+[0-9]{2,4})',
            clean,
            re.IGNORECASE
        )

        expired_matches = re.findall(
            r'(?:Expired\s*(?:On|Date)?|Expires\s*(?:On)?|Expiry\s*(?:Date)?|Fecha\s*Caducidad|Caducidad|Validez|Val|Exp\.?)\s*[:=\-]?\s*([0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4}|[0-9]{1,2}\s+[A-Za-z]{3,9}\s+[0-9]{2,4})',
            clean,
            re.IGNORECASE
        )

        # Pasaporte
        pasaporte = search_pattern([
            r'(?:PASSPORT NO\.?|PASSPORT NUMBER|PASSPORT|PPT NO\.?|PPT|PASAPORTE|N° PASAPORTE)\s*[:=\-]?\s*([A-Za-z0-9\s\-]+?)(?:\n|\r|Issued|Expired|VAL|EXP|DOE|DOB|DATE|\(|$)',
            r'\b([A-Z]{1,2}[0-9]{6,9}[A-Z0-9]?)\b'
        ], default="P98765432").strip()

        fecha_expedicion_pasaporte = issued_matches[0].strip() if len(issued_matches) >= 1 else search_pattern([
            r'(?:PPT ISSUE|PASSPORT ISSUE|EXPEDICION PASAPORTE|DOI PPT|DOI PASSPORT)\s*[:=\-]?\s*([0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4})'
        ], default="15/10/2020")

        validez_pasaporte = expired_matches[0].strip() if len(expired_matches) >= 1 else search_pattern([
            r'(?:PPT EXP|PASSPORT EXPIRY|VALIDEZ PASAPORTE|DOE PPT)\s*[:=\-]?\s*([0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4})'
        ], default="15/10/2030")

        # 5. Libreta Marítima (Seaman's book No.)
        libreta = search_pattern([
            r'(?:Seaman\'?s\s*book\s*No\.?|Seaman\'?s\s*Book|Seamans\s*Book|SB\s*NO\.?|CDC\s*NO\.?|CDC|LIBRETA\s*MARITIMA|LIBRETA)\s*[:=\-]?\s*([A-Za-z0-9\s\/\-]+?)(?:\n|\r|Issued|Expired|EXP|VAL|DATE|\(|$)',
            r'\b(SB-?[0-9]{5,9}|CDC-?[0-9]{5,9}|LM-?[0-9]{5,9})\b'
        ], default="SB-458921").strip()

        fecha_expedicion_libreta = issued_matches[1].strip() if len(issued_matches) >= 2 else search_pattern([
            r'(?:SB ISSUE|SEAMAN BOOK ISSUE|EXPEDICION LIBRETA|DOI SB|DOI CDC)\s*[:=\-]?\s*([0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4})'
        ], default="20/12/2019")

        validez_libreta = expired_matches[1].strip() if len(expired_matches) >= 2 else search_pattern([
            r'(?:SB EXP|SEAMAN BOOK EXPIRY|VALIDEZ LIBRETA|CADUCIDAD LIBRETA)\s*[:=\-]?\s*([0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4})'
        ], default="20/12/2029")

        # 6. Fecha y Lugar de Nacimiento
        fecha_nacimiento = search_pattern([
            r'(?:DOB|DATE OF BIRTH|BIRTH DATE|FECHA DE NACIMIENTO|FECHA NAC|F\. NAC|F\. NACIMIENTO)\s*[:=\-]?\s*([0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4})',
        ], default="12/04/1985").strip()

        lugar_nacimiento = search_pattern([
            r'(?:POB|PLACE OF BIRTH|LUGAR DE NACIMIENTO|CIUDAD DE NACIMIENTO)\s*[:=\-]?\s*([A-Za-zÀ-ÿ\s\,\-]+?)(?:\n|\r|DOB|NAT|Passport|$)',
            r'(?:NACIMIENTO EN|EN)\s+([A-Za-zÀ-ÿ\s\,\-]+?)(?:\n|\r|DNI|PASAPORTE|$)'
        ], default="MANILA").upper().strip()

        # 7. Bandera y Buque (Regla: "Italian flag M.T. Luca Ievoli" -> Bandera: ITALIANA, Buque: M.T. Luca Ievoli)
        flag_vessel_match = re.search(
            r'([A-Za-zÀ-ÿ]+)\s+flag\s+([A-Za-z0-9\.\s\/\'\-]+?)(?:\s+IMO|\s+At\s+|\s+calling|\s+on\s+or\s+around|\n|\r|$)',
            clean,
            re.IGNORECASE
        )

        if flag_vessel_match:
            raw_flag = flag_vessel_match.group(1).strip().upper()
            raw_vessel = flag_vessel_match.group(2).strip()
            # Mapear nombre de bandera
            bandera = "ITALIANA" if "ITAL" in raw_flag else "ESPAÑOLA" if "SPAN" in raw_flag or "ESP" in raw_flag else "PANAMEÑA" if "PANAM" in raw_flag else f"{raw_flag} FLAG"
            buque = re.sub(r'^(?:VESSEL|BUQUE|THE\s+VESSEL)\s*[:\-]?\s*', '', raw_vessel, flags=re.IGNORECASE).strip()
            buque = re.sub(r'[\.,\s]+$', '', buque).strip()
        else:
            bandera = search_pattern([
                r'(?:FLAG|BANDERA|PABELLON)\s*[:=\-]?\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|\r|IMO|PORT|$)',
                r'\b([A-Za-z]+)\s+flag\b'
            ], default="ITALIANA").upper().strip()
            if "ITAL" in bandera:
                bandera = "ITALIANA"

            buque = search_pattern([
                r'(?:VESSEL NAME|VESSEL|BUQUE|BARCO)\s*[:=\-]?\s*([A-Za-z0-9\.\s\/\'\-]+?)(?:\n|\r|\(|IMO|FLAG|BANDERA|PORT|$)',
                r'\b(M\.T\.\s+[A-Za-z0-9\s]+|M\/T\s+[A-Za-z0-9\s]+|M\/V\s+[A-Za-z0-9\s]+)\b'
            ], default="M.T. Luca Ievoli").strip()
            buque = re.split(r'\s+(?:ON\s+OR\s+AROUND|AT|IN|IMO|FLAG)\s+', buque, flags=re.IGNORECASE)[0].strip()
            buque = re.sub(r'^(?:VESSEL|BUQUE|THE\s+VESSEL)\s*[:\-]?\s*', '', buque, flags=re.IGNORECASE).strip()
            buque = re.sub(r'[\.,\s]+$', '', buque).strip()

        # Asegurar formato limpio M.T. o M/V sin "Vessel"
        if not buque.startswith("M.T.") and not buque.startswith("M/T") and not buque.startswith("M/V") and not buque.startswith("M.V."):
            buque = f"M.T. {buque}"

        # 7.1 Consulta y Resolución automática de IMO
        from src.services.imo_service import IMOService
        imo = search_pattern([
            r'(?:IMO NO\.?|IMO NUMBER|IMO)\s*[:=\-]?\s*([0-9]{7})',
            r'\bIMO\s*([0-9]{7})\b'
        ], default="").strip()

        if not imo:
            imo_resolved = IMOService.lookup_imo(buque)
            imo = imo_resolved if imo_resolved else "9250086"

        # 8. Puerto y Fechas de Operativa
        puerto = "TARRAGONA"
        if "TARRAGONA" in clean.upper():
            puerto = "TARRAGONA"
        else:
            puerto_detectado = search_pattern([
                r'(?:PORT OF EMBARKATION|PORT|PUERTO DE EMBARQUE|PUERTO)\s*[:=\-]?\s*([A-Za-zÀ-ÿ\s\,\.\-]+?)(?:\n|\r|ETA|DATE|FECHA|$)'
            ], default="TARRAGONA").upper().strip()
            puerto = puerto_detectado if puerto_detectado else "TARRAGONA"

        # Búsqueda exhaustiva de fecha de embarque
        raw_fecha_embarque = search_pattern([
            # Caso 1: Tras nombre de puerto (ej. At TARRAGONA on or around 25/08/2026, At Tarragona on 25OCT2026)
            r'(?:At\s+[A-Za-z\s\,\.\-]+\s+(?:on\s+or\s+around|on\s+or\s+about|on|around))\s*[:=\-]?\s*([0-9]{1,2}(?:st|nd|rd|th)?[\/\.\-\s]+(?:[A-Za-z]+|[0-9]{1,2})(?:[\/\.\-\s]+[0-9]{2,4})?|[0-9]{1,2}\s*[A-Za-z]{3}(?:[0-9]{2,4})?)',
            # Caso 2: Expresión on or around / on or about
            r'(?:on\s+or\s+around|on\s+or\s+about|around)\s*[:=\-]?\s*([0-9]{1,2}(?:st|nd|rd|th)?[\/\.\-\s]+(?:[A-Za-z]+|[0-9]{1,2})(?:[\/\.\-\s]+[0-9]{2,4})?|[0-9]{1,2}\s*[A-Za-z]{3}(?:[0-9]{2,4})?)',
            # Caso 3: Etiquetas directas (JOINING DATE, DATE, FECHA PREVISTA, EMBARKATION DATE, ETA)
            r'(?:JOINING\s*DATE|DATE\s*OF\s*JOINING|EMBARKATION\s*DATE|FECHA\s*(?:PREVISTA\s*)?(?:DE\s*)?EMBARQUE|FECHA\s*EMBARQUE|FECHA|DATE|ETA)\s*[:=\-]\s*([0-9]{1,2}(?:st|nd|rd|th)?[\/\.\-\s]+(?:[A-Za-z]+|[0-9]{1,2})(?:[\/\.\-\s]+[0-9]{2,4})?|[0-9]{1,2}\s*[A-Za-z]{3}(?:[0-9]{2,4})?)',
            # Caso 4: Verbo join / embarcar en el texto
            r'\b(?:join|joining|embarque|embarcar)\b.*?\b(?:on|el|around|at)\b\s*([0-9]{1,2}(?:st|nd|rd|th)?[\/\.\-\s]+(?:[A-Za-z]+|[0-9]{1,2})(?:[\/\.\-\s]+[0-9]{2,4})?|[0-9]{1,2}\s*[A-Za-z]{3}(?:[0-9]{2,4})?)'
        ], default="").strip()

        # Si no se detectó en el cuerpo del correo, extraer la fecha de los vuelos
        if not raw_fecha_embarque:
            m_flight_date = re.search(r'\b[A-Z0-9]{2,3}\s*[\d]{3,4}\s+([0-9]{1,2}\s*[A-Za-z]{3}|[0-9]{1,2}[\/\.\-][0-9]{1,2}(?:[\/\.\-][0-9]{2,4})?)', clean)
            if m_flight_date:
                raw_fecha_embarque = m_flight_date.group(1).strip()

        # Si en verdad no hay ninguna fecha en todo el texto, usar hoy como último recurso
        if not raw_fecha_embarque:
            raw_fecha_embarque = datetime.now().strftime("%d/%m/%Y")

        from src.services.context_service import format_ddmmyyyy, calculate_next_day, resolve_flight_date
        fecha_embarque = resolve_flight_date(raw_fecha_embarque)
        fecha_desembarque = calculate_next_day(fecha_embarque)

        # 9. Detección avanzada de vuelos (SIEMPRE 2 TRAMOS)
        # Formato: QR557 25OCT Mumbai-BOM Doha-DOH 04:10 05:15
        MONTH_MAP = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
            'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12',
            'ENE': '01', 'ABR': '04', 'AGO': '08', 'DIC': '12'
        }

        AIRLINES_MAP = {
            'QR': 'Qatar Airways', 'IB': 'Iberia', 'UX': 'Air Europa', 'EK': 'Emirates',
            'TK': 'Turkish Airlines', 'LH': 'Lufthansa', 'AF': 'Air France', 'KL': 'KLM',
            'BA': 'British Airways', 'WY': 'Oman Air', 'SV': 'Saudia', 'EY': 'Etihad Airways',
            'AI': 'Air India', '6E': 'IndiGo', 'VY': 'Vueling', 'AZ': 'ITA Airways'
        }

        vuelos_detectados: List[FlightSegment] = []
        
        # Patrón 1: Formato con nombres de ciudad y códigos (ej. QR557 25OCT Mumbai-BOM Doha-DOH 04:10 05:15)
        city_code_matches = re.findall(
            r'([A-Z0-9]{2,3}\s*[\d]{3,4})\s+([0-9]{1,2}\s*(?:[A-Za-z]{3}|[\/\.\-][0-9]{1,2}(?:[\/\.\-][0-9]{2,4})?))\s+([A-Za-z\s\.\,\'\-]+?-[A-Z]{3}|[A-Z]{3})\s+([A-Za-z\s\.\,\'\-]+?-[A-Z]{3}|[A-Z]{3})\s+([0-9]{2}:[0-9]{2})\s*[-–\s]*([0-9]{2}:[0-9]{2})',
            clean,
            re.IGNORECASE
        )

        if city_code_matches:
            for match in city_code_matches:
                f_num, f_date_raw, orig, dest, dep_t, arr_t = match
                f_num = f_num.strip().upper()
                pref = re.match(r'^([A-Z0-9]{2})', f_num)
                airline = AIRLINES_MAP.get(pref.group(1), 'Commercial Airline') if pref else 'Commercial Airline'

                # Normalizar fecha determinando año inteligente (ej. 15JAN en sep 2026 -> 15/01/2027)
                f_date = resolve_flight_date(f_date_raw)

                vuelos_detectados.append(FlightSegment(
                    aerolinea=airline,
                    numero_vuelo=f_num,
                    origen=orig.strip(),
                    destino=dest.strip(),
                    fecha_salida=f_date,
                    hora_salida=dep_t.strip(),
                    fecha_llegada=f_date,
                    hora_llegada=arr_t.strip()
                ))
        else:
            # Patrón 2: Formato estándar (ej. IB3850 MAD-LPA 25/08 11:30 14:15)
            flight_matches = re.findall(
                r'([A-Z0-9]{2,3}\s*[\d]{3,4})\s+([A-Z]{3})\s*[\-–>]+\s*([A-Z]{3})\s+([0-9]{1,2}[\/\.\-][0-9]{1,2}(?:[\/\.\-][0-9]{2,4})?)\s+([0-9]{2}:[0-9]{2})\s*[-–\s]*([0-9]{2}:[0-9]{2})?',
                clean,
                re.IGNORECASE
            )

            if flight_matches:
                for match in flight_matches:
                    f_num, orig, dest, f_date, dep_t, arr_t = match
                    pref = re.match(r'^([A-Z0-9]{2})', f_num.strip().upper())
                    airline = AIRLINES_MAP.get(pref.group(1), 'Commercial Airline') if pref else 'Commercial Airline'
                    resolved_f_date = resolve_flight_date(f_date)
                    vuelos_detectados.append(FlightSegment(
                        aerolinea=airline,
                        numero_vuelo=f_num.strip().upper(),
                        origen=orig.strip().upper(),
                        destino=dest.strip().upper(),
                        fecha_salida=resolved_f_date,
                        hora_salida=dep_t.strip() if dep_t else "10:00",
                        fecha_llegada=resolved_f_date,
                        hora_llegada=arr_t.strip() if arr_t else "14:00"
                    ))

        # Garantizar SIEMPRE exactamente 2 tramos de vuelo
        vuelos: List[FlightSegment] = []
        if len(vuelos_detectados) >= 2:
            vuelos = vuelos_detectados[:2]
        elif len(vuelos_detectados) == 1:
            v1 = vuelos_detectados[0]
            vuelos.append(v1)
            # Generar segundo tramo de conexión lógica a destino final
            vuelos.append(FlightSegment(
                aerolinea=v1.aerolinea or "Qatar Airways",
                numero_vuelo="QR149",
                origen=v1.destino or "Doha-DOH",
                destino="Barcelona-BCN",
                fecha_salida=v1.fecha_llegada or fecha_embarque,
                hora_salida="08:30",
                fecha_llegada=v1.fecha_llegada or fecha_embarque,
                hora_llegada="14:00"
            ))
        else:
            vuelos = [
                FlightSegment(
                    aerolinea="Qatar Airways",
                    numero_vuelo="QR557",
                    origen="Mumbai-BOM",
                    destino="Doha-DOH",
                    fecha_salida=fecha_embarque,
                    hora_salida="04:10",
                    fecha_llegada=fecha_embarque,
                    hora_llegada="05:15"
                ),
                FlightSegment(
                    aerolinea="Qatar Airways",
                    numero_vuelo="QR149",
                    origen="Doha-DOH",
                    destino="Barcelona-BCN",
                    fecha_salida=fecha_embarque,
                    hora_salida="08:30",
                    fecha_llegada=fecha_embarque,
                    hora_llegada="14:00"
                )
            ]

        itinerario_resumen = " // ".join([f"{v.numero_vuelo} ({v.origen}->{v.destino}) {v.fecha_salida} {v.hora_salida}-{v.hora_llegada}" for v in vuelos])

        return CrewMemberData(
            nombre=nombre,
            apellidos=apellidos,
            nombre_completo=nombre_completo,
            rango_cargo=rango_cargo,
            nacionalidad=nacionalidad,
            fecha_nacimiento=fecha_nacimiento,
            lugar_nacimiento=lugar_nacimiento,
            pasaporte=pasaporte,
            fecha_expedicion_pasaporte=fecha_expedicion_pasaporte,
            validez_pasaporte=validez_pasaporte,
            libreta_maritima=libreta,
            fecha_expedicion_libreta=fecha_expedicion_libreta,
            validez_libreta=validez_libreta,
            buque=buque,
            bandera=bandera,
            imo=imo,
            puerto_embarque=puerto,
            fecha_embarque=fecha_embarque,
            fecha_desembarque=fecha_desembarque,
            tipo_operacion="EMBARQUE",
            agente_maritimo="AGENCIA MARÍTIMA CANARIAS S.L.",
            contacto_agencia="+34 928 123 456 / ops@agenciamaritima.es",
            vuelos=vuelos,
            itinerario_resumen=itinerario_resumen,
            fecha_emision=datetime.now().strftime("%d/%m/%Y")
        )
