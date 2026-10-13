from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class FlightSegment(BaseModel):
    aerolinea: str = Field(default="", description="Nombre de la aerolínea (ej. Iberia, Air Europa)")
    numero_vuelo: str = Field(default="", description="Código de vuelo (ej. IB3850, UX9112)")
    origen: str = Field(default="", description="Aeropuerto o ciudad de origen (ej. MAD / Madrid)")
    destino: str = Field(default="", description="Aeropuerto o ciudad de destino (ej. LPA / Las Palmas)")
    fecha_salida: str = Field(default="", description="Fecha de salida (ej. 25/08/2026)")
    hora_salida: str = Field(default="", description="Hora de salida (ej. 10:30)")
    fecha_llegada: str = Field(default="", description="Fecha de llegada (ej. 25/08/2026)")
    hora_llegada: str = Field(default="", description="Hora de llegada (ej. 13:15)")

class CrewMemberData(BaseModel):
    nombre: str = Field(default="", description="Nombre de pila")
    apellidos: str = Field(default="", description="Apellidos")
    nombre_completo: str = Field(default="", description="Nombre completo")
    rango_cargo: str = Field(default="", description="Cargo a bordo (ej. Chief Engineer, Captain, Able Seaman)")
    nacionalidad: str = Field(default="", description="Nacionalidad del tripulante")
    fecha_nacimiento: str = Field(default="", description="Fecha de nacimiento (ej. 14/05/1982)")
    lugar_nacimiento: str = Field(default="", description="Lugar/Ciudad de nacimiento")
    pasaporte: str = Field(default="", description="Número de pasaporte")
    fecha_expedicion_pasaporte: str = Field(default="", description="Fecha de expedición/emisión del pasaporte")
    validez_pasaporte: str = Field(default="", description="Fecha de caducidad del pasaporte")
    libreta_maritima: str = Field(default="", description="Número de libreta marítima (Seaman's Book)")
    fecha_expedicion_libreta: str = Field(default="", description="Fecha de expedición/emisión de libreta marítima")
    validez_libreta: str = Field(default="", description="Fecha de caducidad de libreta marítima")
    
    # Datos de la operativa y buque
    buque: str = Field(default="", description="Nombre del buque (ej. M/V ATLANTIC VOYAGER)")
    bandera: str = Field(default="", description="Bandera del buque (ej. Panamá, Malta, Liberia)")
    imo: str = Field(default="", description="Número IMO del buque")
    puerto_embarque: str = Field(default="", description="Puerto de embarque o desembarque (ej. Las Palmas)")
    fecha_embarque: str = Field(default="", description="Fecha estimada de embarque")
    fecha_desembarque: str = Field(default="", description="Fecha estimada de desembarque")
    tipo_operacion: str = Field(default="EMBARQUE", description="EMBARQUE / DESEMBARQUE / TRANSITO")
    agente_maritimo: str = Field(default="AGENCIA MARÍTIMA CANARIAS S.L.", description="Nombre de la agencia consignataria")
    contacto_agencia: str = Field(default="+34 928 000 000 / ops@agenciamaritima.com", description="Contacto de la consignataria")
    
    # Vuelos e itinerario
    vuelos: List[FlightSegment] = Field(default_factory=list, description="Lista de tramos de vuelo")
    itinerario_resumen: str = Field(default="", description="Resumen textual de los vuelos")
    
    # Metadatos del documento
    fecha_emision: str = Field(default="", description="Fecha actual de emisión del documento")

class ParseEmailRequest(BaseModel):
    email_text: str
    gemini_api_key: Optional[str] = None

class ParseEmailResponse(BaseModel):
    success: bool
    data: Optional[CrewMemberData] = None
    tripulantes_multiples: Optional[List[CrewMemberData]] = None
    error: Optional[str] = None
    metodo: str = "regex" # "gemini" o "regex"

class GenerateDocResponse(BaseModel):
    success: bool
    tipo: str # "LOI" o "ANEXO_IX"
    nombre_archivo: str
    ruta_archivo: str
    url_descarga: str
    mensaje: str
    error: Optional[str] = None
