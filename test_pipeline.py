import sys
from pathlib import Path

# Añadir ruta raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.models import CrewMemberData, FlightSegment
from src.services.template_service import TemplateService
from src.agents.parser_agent import ParserAgent
from src.agents.loi_agent import LOIAgent
from src.agents.anexo_ix_agent import AnexoIXAgent

def test_full_pipeline():
    print("=== TEST 1: Inicializando plantillas ===")
    data_dir = TemplateService.get_data_dir()
    TemplateService.ensure_templates_exist()
    assert (data_dir / "plantilla_loi.docx").exists(), "Falta plantilla_loi.docx"
    assert (data_dir / "plantilla_anexo_ix.docx").exists(), "Falta plantilla_anexo_ix.docx"
    print("Plantillas verificadas exitosamente en:", data_dir)

    print("\n=== TEST 2: Parseo de correo con ParserAgent ===")
    sample_email = """
    Dear Agents,
    Please arrange crew change in Las Palmas for M/V ATLANTIC VOYAGER (Flag: Panama, IMO: 9481234).
    Joining Date: 25/08/2026

    Seafarer details:
    Full Name: IVAN PETROV
    Rank: CHIEF ENGINEER
    Nationality: UKRAINIAN
    DOB: 14/05/1982 in Odesa
    Passport: EP883921 (Exp: 20/10/2030)
    Seaman Book: SB-449102 (Exp: 15/12/2029)

    Flights:
    IB3850 MAD-LPA 25/08 11:30 14:15
    """

    parser = ParserAgent()
    crew_data, method = parser.parse(sample_email)
    print(f"Metodo utilizado: {method}")
    print(f"Nombre extraido: {crew_data.nombre_completo}")
    print(f"Rango: {crew_data.rango_cargo}")
    print(f"Buque: {crew_data.buque} (IMO: {crew_data.imo})")
    print(f"Pasaporte: {crew_data.pasaporte}")
    print(f"Vuelos: {[v.numero_vuelo for v in crew_data.vuelos]}")

    assert crew_data.nombre_completo == "IVAN PETROV"
    assert crew_data.pasaporte == "EP883921"
    assert crew_data.imo == "9481234"

    print("\n=== TEST 3: Generacion de Carta de Invitacion (LOI) ===")
    loi_agent = LOIAgent(data_dir=data_dir)
    res_loi = loi_agent.generate(crew_data)
    print("LOI generada:", res_loi.nombre_archivo)
    assert Path(res_loi.ruta_archivo).exists(), "El archivo LOI no se creo"

    print("\n=== TEST 4: Generacion de Anexo IX ===")
    anexo_agent = AnexoIXAgent(data_dir=data_dir)
    res_anexo = anexo_agent.generate(crew_data)
    print("Anexo IX generado:", res_anexo.nombre_archivo)
    assert Path(res_anexo.ruta_archivo).exists(), "El archivo Anexo IX no se creo"

    print("\n[OK] TODAS LAS PRUEBAS UNITARIAS Y DE GENERACION PASARON CON EXITO.")

if __name__ == "__main__":
    test_full_pipeline()
