// NaviAgent - Interfaz de Automatización Documental Marítima

// Ejemplos de correos reales para pruebas rápidas
const SAMPLES = {
  1: `Please be informed that the following crew member will join the Italian flag M.T. Luca Ievoli at TARRAGONA on or around 25/08/2026:

Surname: PETROV
Name: IVAN
Rank: CHIEF ENGINEER
Nationality: UKRAINIAN
Date of Birth: 14/05/1982
Place of Birth: ODESA, UKRAINE
Passport: EP883921
Issued At: 15/10/2020
Expired On: 20/10/2030
Seaman's book No.: SB-449102
Issued At: 10/12/2019
Expired On: 15/12/2029

Flight details:
QR557 25OCT Mumbai-BOM Doha-DOH 04:10 05:15
QR149 25OCT Doha-DOH Barcelona-BCN 08:30 14:00

Please arrange Letter of Invitation (LOI) and Annex IX for immigration clearance.

Best regards,
Crew Operations Desk`,

  2: `ATTN: CREW DEPT / LAS PALMAS PORT AGENT

RE: JOINING MASTER - M/T OCEANIC CARRIER (IMO 9654120, FLAG: MALTA)
JOINING PORT: LAS PALMAS DE GRAN CANARIA
DATE: 28/08/2026

SEAFARER INFORMATION:
NAME: RODRIGO SANTOS
RANK: MASTER / CAPTAIN
NATIONALITY: FILIPINO
DOB: 03/11/1976
POB: CEBU CITY, PHILIPPINES
PASSPORT: P8745219C (DOI: 10/06/2021, VAL: 10/06/2031)
SEAMAN BOOK: CDC-551920 (DOI: 05/04/2020, VAL: 05/04/2030)

FLIGHT TICKETS & SCHEDULE:
1. QR935 MNL -> DOH 27/08/2026 09:00 - 13:40
2. QR149 DOH -> MAD 27/08/2026 15:50 - 21:30
3. IB3856 MAD -> LPA 28/08/2026 07:30 - 10:20

Kindly provide Letter of Guarantee / Invitation (LOI) and Annex IX for immigration clearance.

Thanks & Regards,
Operations Manager`,

  3: `Buenos días Agencia Marítima Canarias,

Les enviamos los datos del marinero que embarcará en Las Palmas:

Tripulante: CARLOS MENDEZ SOTO
Cargo: MARINERO DE PRIMERA (ABLE SEAMAN)
Nacionalidad: ESPAÑOLA
F. Nacimiento: 22/09/1990 en SANTA CRUZ DE TENERIFE
DNI/Pasaporte: 44891230X (Expedición: 18/07/2022, Caducidad: 18/07/2032)
Libreta Marítima: LM-77412 (Expedición: 10/05/2020, Caducidad: 10/05/2030)

Buque: M/V MAR DE FONDO (Bandera España, IMO 9123456)
Fecha prevista de embarque: 24/08/2026
Vuelo: UX9112 MAD-LPA 24/08 15:00 - 17:45

Por favor emitir Carta de Invitación (LOI) y formulario oficial Anexo IX.

Saludos cordiales,
Naviera del Atlántico`
};

let currentCrewData = null;

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

function initApp() {
  // Manejo de Contador de caracteres
  const emailInput = document.getElementById("emailInput");
  const charCounter = document.getElementById("charCounter");
  
  emailInput.addEventListener("input", () => {
    charCounter.textContent = `${emailInput.value.length} caracteres`;
  });

  // Cargar botones de ejemplo
  document.querySelectorAll(".btn-sample").forEach(btn => {
    btn.addEventListener("click", () => {
      const sampleId = btn.getAttribute("data-sample");
      if (SAMPLES[sampleId]) {
        emailInput.value = SAMPLES[sampleId];
        charCounter.textContent = `${emailInput.value.length} caracteres`;
        showToast("Ejemplo cargado en el editor", "info");
      }
    });
  });

  // Botón Limpiar
  document.getElementById("btnClear").addEventListener("click", () => {
    emailInput.value = "";
    charCounter.textContent = "0 caracteres";
    showToast("Editor limpiado", "info");
  });

  // Botón Parsear con ParserAgent
  document.getElementById("btnParse").addEventListener("click", parseEmail);

  // Escuchador dinámico para calcular automáticamente el día siguiente al embarque y sincronizar badges
  const inputFechaEmbarque = document.getElementById("field_fecha_embarque");
  const inputFechaDesembarque = document.getElementById("field_fecha_desembarque");
  const inputBuque = document.getElementById("field_buque");

  if (inputFechaEmbarque && inputFechaDesembarque) {
    const updateNextDay = () => {
      const next = calculateNextDayJS(inputFechaEmbarque.value);
      if (next) {
        inputFechaDesembarque.value = next;
      }
      updateOperationalBadges();
    };
    inputFechaEmbarque.addEventListener("input", updateNextDay);
    inputFechaEmbarque.addEventListener("change", updateNextDay);
    inputFechaEmbarque.addEventListener("blur", updateNextDay);

    inputFechaDesembarque.addEventListener("input", updateOperationalBadges);
    inputFechaDesembarque.addEventListener("change", updateOperationalBadges);
  }

  if (inputBuque) {
    inputBuque.addEventListener("input", updateOperationalBadges);
    inputBuque.addEventListener("change", updateOperationalBadges);
  }

  // Manejo de Pestañas
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      switchTab(tabId);
    });
  });

  // Añadir tramo de vuelo (si existe en DOM)
  const btnAddFlight = document.getElementById("btnAddFlight");
  if (btnAddFlight) {
    btnAddFlight.addEventListener("click", () => addFlightRow());
  }

  // Botones de Generación de Documentos
  document.getElementById("btnGenLOI")?.addEventListener("click", () => generateDocument("loi"));
  document.getElementById("btnGenAnexo")?.addEventListener("click", () => generateDocument("anexo_ix"));
  document.getElementById("btnGenBoth")?.addEventListener("click", () => generateDocument("all"));

  // Refrescar documentos
  document.getElementById("btnRefreshDocs")?.addEventListener("click", loadRecentDocs);

  // Abrir carpeta en unidad de red F:\
  document.getElementById("btnOpenFolder")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/abrir-carpeta", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        showToast("Abriendo carpeta en la unidad compartida F:\\", "success");
      } else {
        showToast(data.error || "No se pudo abrir la carpeta en F:\\", "warning");
      }
    } catch (e) {
      showToast("Error contactando al servidor", "error");
    }
  });

  // Reintentar conexión de almacenamiento de red
  document.getElementById("btnRetryStorage")?.addEventListener("click", () => {
    showToast("Comprobando conexión con la unidad F:\\...", "info");
    checkStorageStatus();
  });

  // Modal API Key
  setupApiKeyModal();

  // Comprobar estado de la unidad de red F:\ y LAN
  checkStorageStatus();
  setInterval(checkStorageStatus, 15000);

  // Cargar lista inicial de documentos generados
  loadRecentDocs();
}

async function checkStorageStatus() {
  try {
    const res = await fetch("/api/storage/status");
    const data = await res.json();

    const badge = document.getElementById("storageStatusBadge");
    const dot = document.getElementById("storageDot");
    const label = document.getElementById("storageLabel");
    const banner = document.getElementById("storageAlertBanner");
    const alertMsg = document.getElementById("storageAlertMessage");
    const lanLabel = document.getElementById("lanIpLabel");

    if (lanLabel && data.lan_ip) {
      lanLabel.textContent = `LAN: ${data.lan_ip}:${data.server_port || 4000}`;
    }

    if (data.ok) {
      if (badge) {
        badge.className = "inline-flex items-center space-x-2 bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full text-xs font-medium border border-emerald-500/20";
        badge.title = `Conectado a ${data.network_root}`;
      }
      if (dot) {
        dot.className = "w-2 h-2 rounded-full bg-emerald-400 animate-pulse";
      }
      if (label) {
        label.textContent = "Unidad F:\\ Conectada";
      }
      if (banner) banner.classList.add("hidden");
    } else {
      if (badge) {
        badge.className = "inline-flex items-center space-x-2 bg-rose-500/20 text-rose-300 px-3 py-1 rounded-full text-xs font-medium border border-rose-500/40 animate-pulse";
        badge.title = data.mensaje;
      }
      if (dot) {
        dot.className = "w-2 h-2 rounded-full bg-rose-500";
      }
      if (label) {
        label.textContent = "Unidad F:\\ Desconectada";
      }
      if (banner) {
        banner.classList.remove("hidden");
        if (alertMsg) alertMsg.textContent = data.mensaje;
      }
    }
  } catch (err) {
    console.error("Error verificando estado de la unidad F:", err);
  }
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".tab-btn").forEach(el => {
    el.classList.remove("text-blue-400", "border-b-2", "border-blue-500", "font-semibold");
    el.classList.add("text-slate-400");
  });

  const activeContent = document.getElementById(tabId);
  if (activeContent) activeContent.classList.remove("hidden");

  const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
  if (activeBtn) {
    activeBtn.classList.remove("text-slate-400");
    activeBtn.classList.add("text-blue-400", "border-b-2", "border-blue-500", "font-semibold");
  }
}

async function parseEmail() {
  const emailText = document.getElementById("emailInput").value.trim();
  if (!emailText) {
    showToast("Por favor pega o carga el texto del e-mail primero.", "warning");
    return;
  }

  const btn = document.getElementById("btnParse");
  const btnText = document.getElementById("btnParseText");
  const spinner = document.getElementById("parseSpinner");
  const apiKey = localStorage.getItem("navi_gemini_api_key") || "";

  btn.disabled = true;
  btnText.textContent = "Procesando con ParserAgent...";
  spinner.classList.remove("hidden");

  try {
    const res = await fetch("/api/parse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email_text: emailText,
        gemini_api_key: apiKey || null
      })
    });

    const result = await res.json();

    if (result.success && result.data) {
      currentCrewData = result.data;
      populateForm(result.data);

      // Actualizar badges
      const statusBadge = document.getElementById("dataStatusBadge");
      statusBadge.textContent = "Datos Extraídos y Listos";
      statusBadge.className = "px-2.5 py-0.5 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";

      const parserBadge = document.getElementById("parserStatusBadge");
      const parserMethod = document.getElementById("parserMethodName");
      parserBadge.classList.remove("hidden");
      parserBadge.classList.add("flex");
      
      if (result.metodo === "gemini") {
        parserMethod.innerHTML = `<i class="fa-solid fa-sparkles text-amber-400 mr-1"></i> Gemini 3.7 Flash (Neuronal)`;
        parserMethod.className = "font-semibold text-purple-400";
      } else {
        parserMethod.innerHTML = `<i class="fa-solid fa-bolt text-blue-400 mr-1"></i> Motor Heurístico Marítimo`;
        parserMethod.className = "font-semibold text-blue-400";
      }

      showToast(`Información de ${result.data.nombre_completo || 'tripulante'} parseada con éxito`, "success");
    } else {
      showToast(result.error || "No se pudieron extraer datos del correo.", "error");
    }
  } catch (err) {
    showToast(`Error al comunicarse con el servidor: ${err.message}`, "error");
  } finally {
    btn.disabled = false;
    btnText.textContent = "Parsear Datos con ParserAgent";
    spinner.classList.add("hidden");
  }
}

function calculateNextDayJS(dateStr) {
  if (!dateStr) return "";
  const clean = dateStr.trim().toUpperCase();

  // 1. Formato ISO YYYY-MM-DD o YYYY/MM/DD
  const m_iso = clean.match(/^([0-9]{4})[\/\.\-]([0-9]{1,2})[\/\.\-]([0-9]{1,2})/);
  if (m_iso) {
    const y = parseInt(m_iso[1], 10);
    const m = parseInt(m_iso[2], 10) - 1;
    const d = parseInt(m_iso[3], 10);
    const dt = new Date(y, m, d + 1);
    const dd = String(dt.getDate()).padStart(2, "0");
    const mm = String(dt.getMonth() + 1).padStart(2, "0");
    return `${dd}/${mm}/${dt.getFullYear()}`;
  }

  // 2. Formato con mes en letras: 25OCT2026, 25-OCT-2026
  const months = { JAN: 0, FEB: 1, MAR: 2, APR: 3, MAY: 4, JUN: 5, JUL: 6, AUG: 7, SEP: 8, OCT: 9, NOV: 10, DEC: 11, ENE: 0, ABR: 3, AGO: 7, DIC: 11 };
  const m_mon = clean.match(/^([0-9]{1,2})\s*[-/\s]?\s*([A-Z]{3})\s*[-/\s]?\s*([0-9]{2,4})?/);
  if (m_mon) {
    const d = parseInt(m_mon[1], 10);
    const m = months[m_mon[2]] !== undefined ? months[m_mon[2]] : 7;
    let y = m_mon[3] ? parseInt(m_mon[3], 10) : new Date().getFullYear();
    if (y < 100) y += 2000;
    const dt = new Date(y, m, d + 1);
    const dd = String(dt.getDate()).padStart(2, "0");
    const mm = String(dt.getMonth() + 1).padStart(2, "0");
    return `${dd}/${mm}/${dt.getFullYear()}`;
  }

  // 3. Formato estándar europeo DD/MM/YYYY o DD-MM-YYYY
  const m_eu = clean.match(/^([0-9]{1,2})[\/\.\-]([0-9]{1,2})(?:[\/\.\-]([0-9]{2,4}))?/);
  if (m_eu) {
    const d = parseInt(m_eu[1], 10);
    const m = parseInt(m_eu[2], 10) - 1;
    let y = m_eu[3] ? parseInt(m_eu[3], 10) : new Date().getFullYear();
    if (y < 100) y += 2000;
    const dt = new Date(y, m, d + 1);
    const dd = String(dt.getDate()).padStart(2, "0");
    const mm = String(dt.getMonth() + 1).padStart(2, "0");
    return `${dd}/${mm}/${dt.getFullYear()}`;
  }

  return "";
}

function resolveFlightDateJS(dateStr) {
  if (!dateStr) return "";
  const clean = dateStr.trim().toUpperCase();

  const now = new Date();
  const currentYear = now.getFullYear();

  let d = null, m = null, rawY = null;

  // 1. Formato ISO YYYY-MM-DD
  const m_iso = clean.match(/^([0-9]{4})[\/\.\-]([0-9]{1,2})[\/\.\-]([0-9]{1,2})/);
  if (m_iso) {
    rawY = parseInt(m_iso[1], 10);
    m = parseInt(m_iso[2], 10) - 1;
    d = parseInt(m_iso[3], 10);
  }

  // 2. Mes en texto (ej. 15JAN, 25OCT2026, 15-JAN)
  const months = { JAN: 0, FEB: 1, MAR: 2, APR: 3, MAY: 4, JUN: 5, JUL: 6, AUG: 7, SEP: 8, OCT: 9, NOV: 10, DEC: 11, ENE: 0, ABR: 3, AGO: 7, DIC: 11 };
  if (d === null) {
    const m_mon = clean.match(/^([0-9]{1,2})\s*[-/\s]?\s*([A-Z]{3,12})\s*[-/\s]?\s*([0-9]{2,4})?/);
    if (m_mon) {
      const code = m_mon[2].substring(0, 3);
      if (months[code] !== undefined) {
        d = parseInt(m_mon[1], 10);
        m = months[code];
        rawY = m_mon[3] ? parseInt(m_mon[3], 10) : null;
      }
    }
  }

  // 3. Estándar DD/MM o DD/MM/YYYY
  if (d === null) {
    const m_eu = clean.match(/^([0-9]{1,2})[\/\.\-]([0-9]{1,2})(?:[\/\.\-]([0-9]{2,4}))?/);
    if (m_eu) {
      d = parseInt(m_eu[1], 10);
      m = parseInt(m_eu[2], 10) - 1;
      rawY = m_eu[3] ? parseInt(m_eu[3], 10) : null;
    }
  }

  if (d === null || m === null) return dateStr;

  if (rawY && rawY < 100) rawY += 2000;

  // Regla: si (día, mes) ya pasó en el año actual, se entiende que es el año siguiente
  const checkDate = new Date(currentYear, m, d);
  const today = new Date(currentYear, now.getMonth(), now.getDate());

  let year;
  if (rawY && rawY > currentYear) {
    year = rawY;
  } else {
    if (checkDate < today) {
      year = currentYear + 1;
    } else {
      year = currentYear;
    }
  }

  const dd = String(d).padStart(2, "0");
  const mm = String(m + 1).padStart(2, "0");
  return `${dd}/${mm}/${year}`;
}

function updateOperationalBadges() {
  const buque = document.getElementById("field_buque")?.value.trim() || "Sin asignar";
  const embarque = document.getElementById("field_fecha_embarque")?.value.trim() || "--/--/----";
  const desembarque = document.getElementById("field_fecha_desembarque")?.value.trim() || "--/--/----";

  const badgeVessel = document.getElementById("quick_vessel_badge");
  const badgeEmbarque = document.getElementById("quick_embarque_badge");
  const badgeDesembarque = document.getElementById("quick_desembarque_badge");

  if (badgeVessel) badgeVessel.textContent = buque;
  if (badgeEmbarque) badgeEmbarque.textContent = embarque;
  if (badgeDesembarque) badgeDesembarque.textContent = desembarque;
}

function populateForm(data) {
  document.getElementById("field_nombre").value = data.nombre || "";
  document.getElementById("field_apellidos").value = data.apellidos || "";
  document.getElementById("field_rango_cargo").value = data.rango_cargo || "";
  document.getElementById("field_nacionalidad").value = data.nacionalidad || "";
  document.getElementById("field_fecha_nacimiento").value = data.fecha_nacimiento || "";
  document.getElementById("field_lugar_nacimiento").value = data.lugar_nacimiento || "";
  document.getElementById("field_pasaporte").value = data.pasaporte || "";
  document.getElementById("field_fecha_expedicion_pasaporte").value = data.fecha_expedicion_pasaporte || "";
  document.getElementById("field_validez_pasaporte").value = data.validez_pasaporte || "";
  document.getElementById("field_libreta_maritima").value = data.libreta_maritima || "";
  document.getElementById("field_fecha_expedicion_libreta").value = data.fecha_expedicion_libreta || "";
  document.getElementById("field_validez_libreta").value = data.validez_libreta || "";

  document.getElementById("field_buque").value = data.buque || "";
  document.getElementById("field_bandera").value = data.bandera || "";
  document.getElementById("field_imo").value = data.imo || "";
  document.getElementById("field_puerto_embarque").value = data.puerto_embarque || "";

  const embarqueVal = data.fecha_embarque || "";
  const calculatedNext = calculateNextDayJS(embarqueVal);
  // Regla estricta: si fecha_desembarque está vacía o es igual a fecha_embarque, forzar el día siguiente calculado (+1 día)
  const desembarqueVal = (data.fecha_desembarque && data.fecha_desembarque.trim() !== embarqueVal.trim())
    ? data.fecha_desembarque
    : calculatedNext;

  document.getElementById("field_fecha_embarque").value = embarqueVal;
  document.getElementById("field_fecha_desembarque").value = desembarqueVal;

  document.getElementById("field_itinerario_resumen").value = data.itinerario_resumen || "";

  // Actualizar la barra superior visible en todas las pestañas
  updateOperationalBadges();

  // Renderizar vuelos
  renderFlightRows(data.vuelos || []);
}

function renderFlightRows(flights) {
  const container = document.getElementById("flightsContainer");
  const countBadge = document.getElementById("flightCountBadge");
  container.innerHTML = "";

  // Asegurar siempre 2 tramos
  let flightList = Array.isArray(flights) && flights.length > 0 ? [...flights] : [];
  if (flightList.length === 1) {
    const f1 = flightList[0];
    flightList.push({
      aerolinea: f1.aerolinea || "Qatar Airways",
      numero_vuelo: "QR149",
      origen: f1.destino || "Doha-DOH",
      destino: "Barcelona-BCN",
      fecha_salida: f1.fecha_llegada || document.getElementById("field_fecha_embarque")?.value || "25/10/2026",
      hora_salida: "08:30",
      fecha_llegada: f1.fecha_llegada || document.getElementById("field_fecha_embarque")?.value || "25/10/2026",
      hora_llegada: "14:00"
    });
  } else if (flightList.length === 0) {
    flightList = [
      {
        aerolinea: "Qatar Airways",
        numero_vuelo: "QR557",
        origen: "Mumbai-BOM",
        destino: "Doha-DOH",
        fecha_salida: "25/10/2026",
        hora_salida: "04:10",
        fecha_llegada: "25/10/2026",
        hora_llegada: "05:15"
      },
      {
        aerolinea: "Qatar Airways",
        numero_vuelo: "QR149",
        origen: "Doha-DOH",
        destino: "Barcelona-BCN",
        fecha_salida: "25/10/2026",
        hora_salida: "08:30",
        fecha_llegada: "25/10/2026",
        hora_llegada: "14:00"
      }
    ];
  } else if (flightList.length > 2) {
    flightList = flightList.slice(0, 2);
  }

  countBadge.textContent = "2";

  const legLabels = [
    { title: "1.ᵉʳ Tramo: Origen ➔ Escala / Conexión", badge: "Tramo 1", color: "blue" },
    { title: "2.º Tramo: Escala / Conexión ➔ Destino Final (BCN / Tarragona)", badge: "Tramo 2", color: "indigo" }
  ];

  flightList.forEach((f, idx) => {
    const meta = legLabels[idx] || { title: `Tramo #${idx + 1}`, badge: `Tramo ${idx + 1}`, color: "slate" };
    const row = document.createElement("div");
    row.className = "flight-row bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 space-y-2.5 relative";
    row.innerHTML = `
      <div class="flex items-center justify-between pb-1.5 border-b border-slate-800/80">
        <span class="text-xs font-bold text-slate-200 flex items-center space-x-1.5">
          <i class="fa-solid fa-plane-departure text-${meta.color}-400 text-xs"></i>
          <span>${meta.title}</span>
        </span>
        <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-${meta.color}-950/80 text-${meta.color}-300 border border-${meta.color}-800/60 uppercase">
          ${meta.badge}
        </span>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        <div>
          <label class="text-[10px] font-medium text-slate-400">N.º Vuelo</label>
          <input type="text" class="form-input text-xs font-mono flight-num" value="${f.numero_vuelo || ''}" placeholder="QR557">
        </div>
        <div>
          <label class="text-[10px] font-medium text-slate-400">Aerolínea</label>
          <input type="text" class="form-input text-xs flight-airline" value="${f.aerolinea || ''}" placeholder="Qatar Airways">
        </div>
        <div>
          <label class="text-[10px] font-medium text-slate-400">Origen</label>
          <input type="text" class="form-input text-xs flight-orig" value="${f.origen || ''}" placeholder="Mumbai-BOM">
        </div>
        <div>
          <label class="text-[10px] font-medium text-slate-400">Destino</label>
          <input type="text" class="form-input text-xs flight-dest" value="${f.destino || ''}" placeholder="Doha-DOH">
        </div>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        <div>
          <label class="text-[10px] font-medium text-slate-400">Fecha Salida</label>
          <input type="text" class="form-input text-xs font-mono flight-depdate" value="${f.fecha_salida || ''}" placeholder="25/10/2026">
        </div>
        <div>
          <label class="text-[10px] font-medium text-slate-400">Hora Salida</label>
          <input type="text" class="form-input text-xs font-mono flight-deptime" value="${f.hora_salida || ''}" placeholder="04:10">
        </div>
        <div>
          <label class="text-[10px] font-medium text-slate-400">Fecha Llegada</label>
          <input type="text" class="form-input text-xs font-mono flight-arrdate" value="${f.fecha_llegada || ''}" placeholder="25/10/2026">
        </div>
        <div>
          <label class="text-[10px] font-medium text-slate-400">Hora Llegada</label>
          <input type="text" class="form-input text-xs font-mono flight-arrtime" value="${f.hora_llegada || ''}" placeholder="05:15">
        </div>
      </div>
    `;

    // Normalizar automáticamente fechas al perder el foco
    const depInput = row.querySelector(".flight-depdate");
    const arrInput = row.querySelector(".flight-arrdate");
    if (depInput) {
      depInput.addEventListener("blur", () => {
        if (depInput.value.trim()) {
          depInput.value = resolveFlightDateJS(depInput.value.trim());
          if (arrInput && !arrInput.value.trim()) {
            arrInput.value = depInput.value;
          }
        }
      });
    }
    if (arrInput) {
      arrInput.addEventListener("blur", () => {
        if (arrInput.value.trim()) {
          arrInput.value = resolveFlightDateJS(arrInput.value.trim());
        }
      });
    }

    container.appendChild(row);
  });
}

function collectFlightsFromUI() {
  const rows = document.querySelectorAll(".flight-row");
  const flights = [];
  rows.forEach(r => {
    const rawDep = (r.querySelector(".flight-depdate")?.value || "").trim();
    const rawArr = (r.querySelector(".flight-arrdate")?.value || "").trim();
    flights.push({
      numero_vuelo: (r.querySelector(".flight-num")?.value || "").trim().toUpperCase(),
      aerolinea: (r.querySelector(".flight-airline")?.value || "").trim(),
      origen: (r.querySelector(".flight-orig")?.value || "").trim(),
      destino: (r.querySelector(".flight-dest")?.value || "").trim(),
      fecha_salida: resolveFlightDateJS(rawDep) || rawDep,
      hora_salida: (r.querySelector(".flight-deptime")?.value || "").trim(),
      fecha_llegada: resolveFlightDateJS(rawArr) || resolveFlightDateJS(rawDep) || rawArr,
      hora_llegada: (r.querySelector(".flight-arrtime")?.value || "").trim()
    });
  });
  return flights.slice(0, 2);
}

function getFormData() {
  const getVal = (id) => (document.getElementById(id)?.value || "").trim();
  const nombre = getVal("field_nombre").toUpperCase();
  const apellidos = getVal("field_apellidos").toUpperCase();
  const nombreCompleto = `${nombre} ${apellidos}`.trim();

  return {
    nombre: nombre,
    apellidos: apellidos,
    nombre_completo: nombreCompleto,
    rango_cargo: getVal("field_rango_cargo"),
    nacionalidad: getVal("field_nacionalidad"),
    fecha_nacimiento: getVal("field_fecha_nacimiento"),
    lugar_nacimiento: getVal("field_lugar_nacimiento"),
    pasaporte: getVal("field_pasaporte"),
    fecha_expedicion_pasaporte: getVal("field_fecha_expedicion_pasaporte"),
    validez_pasaporte: getVal("field_validez_pasaporte"),
    libreta_maritima: getVal("field_libreta_maritima"),
    fecha_expedicion_libreta: getVal("field_fecha_expedicion_libreta"),
    validez_libreta: getVal("field_validez_libreta"),
    buque: getVal("field_buque"),
    bandera: getVal("field_bandera"),
    imo: getVal("field_imo"),
    puerto_embarque: getVal("field_puerto_embarque"),
    fecha_embarque: getVal("field_fecha_embarque"),
    fecha_desembarque: getVal("field_fecha_desembarque"),
    tipo_operacion: currentCrewData?.tipo_operacion || "EMBARQUE",
    agente_maritimo: currentCrewData?.agente_maritimo || "AGENCIA MARÍTIMA CANARIAS S.L.",
    contacto_agencia: currentCrewData?.contacto_agencia || "+34 928 123 456 / ops@agenciamaritima.es",
    vuelos: collectFlightsFromUI(),
    itinerario_resumen: getVal("field_itinerario_resumen"),
    fecha_emision: currentCrewData?.fecha_emision || new Date().toLocaleDateString('es-ES')
  };
}

async function generateDocument(type) {
  const data = getFormData();
  if (!data.nombre_completo && !data.pasaporte) {
    showToast("Por favor parsea o ingresa los datos del tripulante antes de generar.", "warning");
    return;
  }

  let endpoint = "/api/generate/loi";
  if (type === "anexo_ix") endpoint = "/api/generate/anexo_ix";
  if (type === "all") endpoint = "/api/generate/all";

  showToast("Generando documento oficial Word...", "info");

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    const result = await res.json();

    if (res.ok) {
      displayGenerationResults(result, type);
      loadRecentDocs();
      showToast("¡Documento(s) Word (.docx) generado(s) con éxito!", "success");
    } else {
      showToast(result.detail || "Error generando documento.", "error");
    }
  } catch (err) {
    showToast(`Error al procesar: ${err.message}`, "error");
  }
}

function displayGenerationResults(result, type) {
  const box = document.getElementById("generationResultBox");
  const list = document.getElementById("downloadLinksList");
  box.classList.remove("hidden");
  list.innerHTML = "";

  const docs = result.documentos || [result];

  docs.forEach(doc => {
    const item = document.createElement("div");
    item.className = "flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-slate-800 hover:border-blue-500/40 transition";
    item.innerHTML = `
      <div class="flex items-center space-x-3 truncate">
        <div class="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center font-bold text-xs">
          <i class="fa-solid fa-file-word text-sm"></i>
        </div>
        <div class="truncate">
          <p class="text-xs font-semibold text-white truncate">${doc.nombre_archivo}</p>
          <p class="text-[10px] text-emerald-400 font-mono"><i class="fa-solid fa-network-wired mr-1"></i> F:\\Letters of Invitation LOIs\\Documentos_Generados</p>
        </div>
      </div>
      <a href="${doc.url_descarga}" download class="ml-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium flex items-center space-x-1.5 shadow transition shrink-0">
        <i class="fa-solid fa-download"></i>
        <span>Descargar</span>
      </a>
    `;
    list.appendChild(item);
  });
}

async function loadRecentDocs() {
  const container = document.getElementById("recentDocsList");
  try {
    const res = await fetch("/api/documentos");
    const data = await res.json();

    if (data.archivos && data.archivos.length > 0) {
      container.innerHTML = "";
      data.archivos.forEach(file => {
        const row = document.createElement("div");
        row.className = "flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition";
        row.innerHTML = `
          <div class="flex items-center space-x-2 truncate">
            <i class="fa-regular fa-file-word text-blue-400 text-sm"></i>
            <span class="text-xs text-slate-300 font-medium truncate" title="${file.nombre}">${file.nombre}</span>
          </div>
          <div class="flex items-center space-x-2 shrink-0">
            <span class="text-[10px] text-slate-500 font-mono">${file.tamaño_kb} KB</span>
            <a href="${file.url_descarga}" download class="text-blue-400 hover:text-blue-300 text-xs p-1" title="Descargar archivo">
              <i class="fa-solid fa-cloud-arrow-down"></i>
            </a>
          </div>
        `;
        container.appendChild(row);
      });
    } else {
      container.innerHTML = `<p class="text-slate-500 italic py-2 text-center text-xs">No hay documentos generados aún.</p>`;
    }
  } catch (e) {
    console.error("Error cargando documentos recientes:", e);
  }
}

function setupApiKeyModal() {
  const modal = document.getElementById("settingsModal");
  const btnOpen = document.getElementById("btnToggleSettings");
  const btnClose = document.getElementById("btnCloseSettings");
  const btnSave = document.getElementById("btnSaveApiKey");
  const inputKey = document.getElementById("inputApiKey");
  const statusLabel = document.getElementById("apiKeyStatusLabel");

  const savedKey = localStorage.getItem("navi_gemini_api_key");
  if (savedKey) {
    inputKey.value = savedKey;
    statusLabel.textContent = "Gemini Configurado";
  }

  btnOpen.addEventListener("click", () => {
    modal.classList.remove("hidden");
    setTimeout(() => modal.classList.remove("opacity-0"), 10);
  });

  const closeModal = () => {
    modal.classList.add("opacity-0");
    setTimeout(() => modal.classList.add("hidden"), 200);
  };

  btnClose.addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  btnSave.addEventListener("click", () => {
    const val = inputKey.value.trim();
    if (val) {
      localStorage.setItem("navi_gemini_api_key", val);
      statusLabel.textContent = "Gemini Configurado";
      showToast("API Key de Gemini guardada localmente", "success");
    } else {
      localStorage.removeItem("navi_gemini_api_key");
      statusLabel.textContent = "Configurar Gemini";
      showToast("Configuración restaurada al modo heurístico local", "info");
    }
    closeModal();
  });
}

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = "toast flex items-center space-x-2 px-4 py-2.5 rounded-xl shadow-2xl text-xs font-medium text-white transition pointer-events-auto";

  if (type === "success") {
    toast.classList.add("bg-emerald-600", "border", "border-emerald-500");
    toast.innerHTML = `<i class="fa-solid fa-circle-check text-white"></i> <span>${message}</span>`;
  } else if (type === "error") {
    toast.classList.add("bg-rose-600", "border", "border-rose-500");
    toast.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-white"></i> <span>${message}</span>`;
  } else if (type === "warning") {
    toast.classList.add("bg-amber-600", "border", "border-amber-500");
    toast.innerHTML = `<i class="fa-solid fa-circle-exclamation text-white"></i> <span>${message}</span>`;
  } else {
    toast.classList.add("bg-blue-600", "border", "border-blue-500");
    toast.innerHTML = `<i class="fa-solid fa-circle-info text-white"></i> <span>${message}</span>`;
  }

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-x-4");
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
