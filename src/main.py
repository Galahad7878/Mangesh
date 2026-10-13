import os
import subprocess
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.models import CrewMemberData, ParseEmailRequest, ParseEmailResponse, GenerateDocResponse
from src.services.storage_service import StorageService
from src.agents.parser_agent import ParserAgent
from src.agents.loi_agent import LOIAgent
from src.agents.anexo_ix_agent import AnexoIXAgent

load_dotenv()

app = FastAPI(
    title="Maritime Crew Change Document Agent API",
    description="Sistema local de automatización y generación documental para cambios de tripulación marítima",
    version="1.1.0"
)

# 1. SEGURIDAD Y RESTRICCIÓN EXCLUSIVA POR RED LOCAL (LAN)
@app.middleware("http")
async def enforce_lan_access(request: Request, call_next):
    client_host = request.client.host if request.client else ""
    # Permitir si es loopback local o pertenece al rango de red privada (10.x, 172.16-31.x, 192.168.x)
    if not StorageService.is_lan_ip(client_host):
        return JSONResponse(
            status_code=403,
            content={
                "error": "Acceso restringido",
                "detail": f"Acceso denegado desde la IP {client_host}. Este servidor solo está disponible para dispositivos en la red local (LAN)."
            }
        )
    return await call_next(request)

# Habilitar CORS para clientes de la red local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar agentes apuntando a la unidad compartida F:\
output_dir = StorageService.get_output_dir()
parser_agent = ParserAgent()
loi_agent = LOIAgent(output_dir=output_dir)
anexo_ix_agent = AnexoIXAgent(output_dir=output_dir)

# Montar frontend estático
static_dir = Path(__file__).resolve().parent.parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def read_root():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Maritime Crew Document Agent API activa. Visite /static/index.html"}

# 2. ENDPOINT DE ESTADO DE LA UNIDAD DE RED F:\ Y CONFIGURACIÓN LAN
@app.get("/api/storage/status")
def get_storage_status():
    """Devuelve el estado de conectividad y permisos de la unidad F:\ y la IP LAN del servidor."""
    health = StorageService.check_storage_health()
    health["lan_ip"] = StorageService.get_local_lan_ip()
    health["server_port"] = 4000
    health["lan_url"] = f"http://{health['lan_ip']}:4000"
    return health

@app.post("/api/parse", response_model=ParseEmailResponse)
def parse_email(req: ParseEmailRequest):
    """Invoca al ParserAgent para extraer campos estructurados del correo."""
    if not req.email_text or not req.email_text.strip():
        raise HTTPException(status_code=400, detail="El cuerpo del correo electrónico no puede estar vacío.")

    try:
        data, metodo = parser_agent.parse(req.email_text, custom_api_key=req.gemini_api_key)
        return ParseEmailResponse(
            success=True,
            data=data,
            metodo=metodo,
            error=None
        )
    except Exception as e:
        return ParseEmailResponse(
            success=False,
            data=None,
            metodo="error",
            error=f"Error durante el parseo: {str(e)}"
        )

@app.post("/api/generate/loi", response_model=GenerateDocResponse)
def generate_loi(crew: CrewMemberData):
    """Genera la LOI leyendo la plantilla desde F:\ y guardando en F:\Letters of Invitation LOIs\Documentos_Generados."""
    try:
        return loi_agent.generate(crew)
    except PermissionError as pe:
        raise HTTPException(status_code=503, detail=f"Error de permisos en red F:\\: {str(pe)}")
    except FileNotFoundError as fe:
        raise HTTPException(status_code=503, detail=f"Plantilla no encontrada en red F:\\: {str(fe)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando LOI: {str(e)}")

@app.post("/api/generate/anexo_ix", response_model=GenerateDocResponse)
def generate_anexo_ix(crew: CrewMemberData):
    """Genera el Anexo IX leyendo la plantilla desde F:\ y guardando en F:\Letters of Invitation LOIs\Documentos_Generados."""
    try:
        return anexo_ix_agent.generate(crew)
    except PermissionError as pe:
        raise HTTPException(status_code=503, detail=f"Error de permisos en red F:\\: {str(pe)}")
    except FileNotFoundError as fe:
        raise HTTPException(status_code=503, detail=f"Plantilla no encontrada en red F:\\: {str(fe)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando Anexo IX: {str(e)}")

@app.post("/api/generate/all")
def generate_all(crew: CrewMemberData):
    """Genera simultáneamente la LOI y el Anexo IX en la unidad de red F:\."""
    try:
        # Pre-verificar la unidad de red para dar error inmediato y limpio si está desconectada
        health = StorageService.check_storage_health()
        if not health["ok"]:
            raise HTTPException(status_code=503, detail=health["mensaje"])

        res_loi = loi_agent.generate(crew)
        res_anexo = anexo_ix_agent.generate(crew)
        return {
            "success": True,
            "documentos": [
                res_loi.model_dump(),
                res_anexo.model_dump()
            ],
            "mensaje": f"Se han guardado con éxito la LOI y el Anexo IX en la unidad compartida F:\\Letters of Invitation LOIs\\Documentos_Generados para {crew.nombre_completo}"
        }
    except HTTPException:
        raise
    except PermissionError as pe:
        raise HTTPException(status_code=503, detail=f"Error de permisos en F:\\: {str(pe)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando documentación completa: {str(e)}")

@app.get("/api/descargar/{filename}")
def download_file(filename: str):
    """Descarga de un documento generado ubicado en la unidad de red F:\."""
    safe_filename = os.path.basename(filename)
    file_path = StorageService.get_output_dir() / safe_filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en la unidad compartida F:\\.")

    return FileResponse(
        path=str(file_path),
        filename=safe_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@app.get("/api/documentos")
def list_documents():
    """Lista todos los documentos generados guardados en F:\Letters of Invitation LOIs\Documentos_Generados."""
    health = StorageService.check_storage_health()
    if not health["ok"]:
        return {
            "archivos": [],
            "error": health["mensaje"]
        }

    files = []
    out_dir = StorageService.get_output_dir()
    if out_dir.exists():
        for f in out_dir.glob("*.docx"):
            if not f.name.startswith("plantilla_"):
                files.append({
                    "nombre": f.name,
                    "tamaño_kb": round(f.stat().st_size / 1024, 2),
                    "fecha_mod": f.stat().st_mtime,
                    "url_descarga": f"/api/descargar/{f.name}"
                })
        files.sort(key=lambda x: x["fecha_mod"], reverse=True)
    return {"archivos": files}

@app.post("/api/abrir-carpeta")
def open_folder():
    """Abre la carpeta de documentos generados en la unidad compartida F:\ en el explorador de Windows."""
    try:
        health = StorageService.check_storage_health()
        target_path = StorageService.get_output_dir() if health["ok"] else StorageService.get_network_root()
        target_path.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(f'explorer "{str(target_path)}"')
        return {"success": True, "mensaje": f"Abierta carpeta en la unidad compartida: {target_path}"}
    except Exception as e:
        return {"success": False, "error": f"No se pudo abrir la unidad compartida: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    lan_ip = StorageService.get_local_lan_ip()
    print("=" * 65)
    print("      NAVIAGENT - SERVIDOR WEB LOCAL (RED LAN)")
    print("=" * 65)
    print(f"[*] Acceso local (esta máquina):   http://localhost:4000")
    print(f"[*] Acceso red local (otros PCs): http://{lan_ip}:4000")
    print(f"[*] Plantillas de entrada:        F:\\Letters of Invitation LOIs\\")
    print(f"[*] Documentos generados:         F:\\Letters of Invitation LOIs\\Documentos_Generados\\")
    print("=" * 65)
    uvicorn.run("src.main:app", host="0.0.0.0", port=4000, reload=False)
