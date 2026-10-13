# 🚢 NaviAgent | Automatización Documental de Cambios de Tripulación Marítima

Aplicación web local orientada a agencias consignatarias, navieras y operadores de logística marítima para procesar correos electrónicos sin formato, extraer y verificar datos de tripulantes y generar automáticamente Cartas de Invitación (**LOI**) y Solicitudes de Visado en Frontera (**Anexo IX**) en formato Word (.docx), preservando el 100% de la maquetación y tipografía institucional.

---

## 🏛️ Arquitectura de Agentes

1. **`ParserAgent` (`src/agents/parser_agent.py`)**:
   - Extrae datos de tripulantes, buques, puertos y vuelos con escalas.
   - Compatible con **Gemini 3.7 Flash** (API Neuronal) y con un **motor heurístico/regex marítimo de alta precisión** integrado (funciona offline sin necesidad obligatoria de clave API).
2. **`LOIAgent` (`src/agents/loi_agent.py`)**:
   - Toma la plantilla oficial `/datos/plantilla_loi.docx` e inyecta los datos con `docxtpl` / `python-docx`.
   - Genera `/datos/LOI_[Nombre_Tripulante]_[Fecha].docx`.
3. **`AnexoIXAgent` (`src/agents/anexo_ix_agent.py`)**:
   - Toma la plantilla oficial `/datos/plantilla_anexo_ix.docx` (solicitud visado frontera código Schengen).
   - Genera `/datos/Anexo_IX_[Nombre_Tripulante]_[Fecha].docx`.

---

## 📂 Estructura del Proyecto

```text
maritime-crew-doc-agent/
│
├── datos/                          # Plantillas y documentos generados
│   ├── plantilla_loi.docx         # Plantilla oficial Letter of Invitation
│   ├── plantilla_anexo_ix.docx    # Plantilla oficial Anexo IX Tránsito Marítimo
│   └── LOI_*.docx, Anexo_IX_*.docx# Documentos emitidos
│
├── src/
│   ├── agents/
│   │   ├── parser_agent.py        # ParserAgent (Gemini + Heurístico)
│   │   ├── loi_agent.py           # LOIAgent (docxtpl)
│   │   └── anexo_ix_agent.py      # AnexoIXAgent (docxtpl)
│   ├── services/
│   │   └── template_service.py    # Servicio y generador de plantillas
│   ├── models.py                  # Modelos de datos Pydantic
│   └── main.py                    # Servidor FastAPI (puerto 4000)
│
├── static/                        # Frontend Web (Tailwind CSS + JS interactivo)
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── requirements.txt               # Dependencias Python
├── iniciar.bat                    # Script de inicio en Windows (cmd)
└── run.ps1                        # Script de inicio PowerShell
```

---

## 🚀 Puesta en Marcha

### Opción 1: Ejecutar script directo
Haz doble clic en **`iniciar.bat`** o ejecuta en PowerShell:
```powershell
.\run.ps1
```

### Opción 2: Línea de comandos manual
```bash
# 1. Crear entorno virtual
uv venv .venv

# 2. Instalar dependencias
uv pip install -r requirements.txt

# 3. Iniciar el servidor
.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 4000 --reload
```

Abre tu navegador en:
👉 **`http://localhost:4000`**

---

## ⚙️ Variables de Plantilla Soportadas en Word (.docx)

Las plantillas Word admiten sintaxis Jinja2 compatible con `docxtpl`:

- `{{ nombre_completo }}`: Nombre y apellidos en mayúsculas
- `{{ nombre }}`: Nombre de pila
- `{{ apellidos }}`: Apellidos
- `{{ rango_cargo }}`: Cargo a bordo (ej. Chief Engineer, Master)
- `{{ nacionalidad }}`: País/Nacionalidad
- `{{ pasaporte }}`: Número de pasaporte
- `{{ validez_pasaporte }}`: Caducidad del pasaporte
- `{{ libreta_maritima }}`: Seaman's Book / Libreta
- `{{ validez_libreta }}`: Caducidad de libreta
- `{{ fecha_nacimiento }}` / `{{ lugar_nacimiento }}`: Datos de nacimiento
- `{{ buque }}` / `{{ bandera }}` / `{{ imo }}`: Datos de la embarcación
- `{{ puerto_embarque }}` / `{{ fecha_embarque }}`: Datos del puerto y fecha
- `{{ agente_maritimo }}` / `{{ contacto_agencia }}`: Datos de consignataria
- `{{ itinerario_resumen }}`: Resumen textual de vuelos
- `{% for v in vuelos %}`: Bucle de tramos con `{{ v.numero_vuelo }}`, `{{ v.aerolinea }}`, `{{ v.origen }}`, `{{ v.destino }}`, `{{ v.fecha_salida }}`, `{{ v.hora_salida }}`.
