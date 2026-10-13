import re
import requests
from typing import Optional

# Base de datos local en memoria de buques frecuentes
KNOWN_VESSELS = {
    "luca ievoli": "9250086",
    "m.t. luca ievoli": "9250086",
    "mt luca ievoli": "9250086",
    "atlantic voyager": "9481234",
    "oceanic carrier": "9654120",
    "mar de fondo": "9123456",
    "luca": "9250086",
    "alessandro dp": "9364502",
    "ievoli shine": "9186716",
    "ievoli sun": "9149457",
    "ievoli black": "9439242",
    "ievoli ambra": "9792577",
    "ievoli ivory": "9703318",
    "ievoli grey": "9283734"
}

class IMOService:
    """
    Servicio de consulta y resolución de número IMO por nombre de buque.
    Consulta una base local en memoria y, de no existir, realiza una búsqueda
    en línea mediante DuckDuckGo / motores marítimos.
    """

    @classmethod
    def lookup_imo(cls, vessel_name: str) -> Optional[str]:
        if not vessel_name or not vessel_name.strip():
            return None

        # Limpiar prefijos M.T., M/T, M/V, Vessel, etc.
        clean_name = re.sub(r'^(?:M\.T\.|MT|M\/T|M\.V\.|MV|M\/V|VESSEL|BUQUE|SS)\s+', '', vessel_name, flags=re.IGNORECASE).strip()
        key = clean_name.lower().strip()

        # 1. Búsqueda en base local / caché inmediata
        if key in KNOWN_VESSELS:
            print(f"[IMOService] IMO encontrado en base local para '{vessel_name}': {KNOWN_VESSELS[key]}")
            return KNOWN_VESSELS[key]

        # 2. Búsqueda en línea (DuckDuckGo Lite)
        try:
            query = f"{clean_name} vessel IMO number"
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            res = requests.get(url, headers=headers, timeout=3.5)
            if res.status_code == 200:
                text = res.text
                # Buscar patrón "IMO 9xxxxxx" o "IMO: 9xxxxxx" o "IMO number 9xxxxxx"
                m = re.search(r'\bIMO\s*(?:NO\.?|NUMBER|#)?\s*[:\s]*([0-9]{7})\b', text, re.IGNORECASE)
                if m:
                    imo_found = m.group(1)
                    KNOWN_VESSELS[key] = imo_found
                    print(f"[IMOService] IMO encontrado en línea para '{vessel_name}': {imo_found}")
                    return imo_found

                # Buscar cualquier número de 7 dígitos típico de IMO (ej. 9xxxxxx o 8xxxxxx)
                m2 = re.findall(r'\b(9[0-9]{6}|8[0-9]{6})\b', text)
                if m2:
                    imo_found = m2[0]
                    KNOWN_VESSELS[key] = imo_found
                    print(f"[IMOService] IMO encontrado por patrón en línea para '{vessel_name}': {imo_found}")
                    return imo_found
        except Exception as e:
            print(f"[IMOService] No se pudo consultar el IMO en línea ({e})")

        return None
