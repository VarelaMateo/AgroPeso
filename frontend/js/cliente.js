// Usa de auth.js: API_BASE, obtenerSesion, borrarToken, cerrarSesion, fetchConToken
const API_TICKETS = `${API_BASE}/tickets/`;
const API_PROVEEDORES = `${API_BASE}/suppliers/`;
const PAGINA_LOGIN = "login.html";

// Guardia de rol (mismo patrón que admin.js)
const sesion = obtenerSesion();
const accesoPermitido = sesion !== null && sesion.rol === "cliente";

if (!accesoPermitido) {
    borrarToken();
    location.replace(PAGINA_LOGIN);
}

const buscador = document.getElementById("buscador");
const nombreProveedor = document.getElementById("nombre-proveedor");
const fechaHora = document.getElementById("fecha-hora");
const tablaTodos = document.getElementById("tabla-todos");
const tablaMes = document.getElementById("tabla-mes");

const statTotal = document.getElementById("stat-total");
const statVariacion = document.getElementById("stat-variacion");
const statAbiertas = document.getElementById("stat-abiertas");
const statNetoPromedio = document.getElementById("stat-neto-promedio");

function mesAnteriorISO() {
    const hoy = new Date();
    const anterior = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1);
    return fechaLocalISO(anterior).slice(0, 7);
}

let tickets = [];

// ---------- Utilidades ----------

function fechaLocalISO(d = new Date()) {
    const mes = String(d.getMonth() + 1).padStart(2, "0");
    const dia = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${mes}-${dia}`;
}

function formatoFecha(fecha) {
    return fecha.split("-").reverse().join("/");
}

function formatoPeso(valor) {
    return valor === null ? "—" : valor.toLocaleString("es-AR");
}

function crearCelda(texto) {
    const td = document.createElement("td");
    td.textContent = texto;
    return td;
}

function crearCeldaEstado(estado) {
    const td = document.createElement("td");
    const etiqueta = document.createElement("span");
    etiqueta.className = estado === "abierto" ? "w3-tag w3-round w3-orange" : "w3-tag w3-round estado-cerrado";
    etiqueta.textContent = estado;
    td.appendChild(etiqueta);
    return td;
}

function mostrarFilaUnica(tbody, texto, columnas) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = columnas;
    celda.className = "w3-center";
    celda.textContent = texto;
    fila.appendChild(celda);
    tbody.replaceChildren(fila);
}

function actualizarEstadisticas() {
    const delMes = tickets.filter((t) => t.fecha.startsWith(fechaLocalISO().slice(0, 7)));
    const delMesAnterior = tickets.filter((t) => t.fecha.startsWith(mesAnteriorISO()));

    statTotal.textContent = tickets.length.toLocaleString("es-AR");

    if (delMesAnterior.length === 0) {
        statVariacion.textContent = `${delMes.length} este mes`;
    } else {
        const variacion = Math.round(((delMes.length - delMesAnterior.length) / delMesAnterior.length) * 100);
        statVariacion.textContent = `${variacion >= 0 ? "+" : ""}${variacion}% vs. mes anterior`;
    }

    const abiertas = tickets.filter((t) => t.estado === "abierto").length;
    statAbiertas.textContent = abiertas.toLocaleString("es-AR");

    const netos = delMes.filter((t) => t.peso_neto !== null).map((t) => t.peso_neto);
    statNetoPromedio.textContent = netos.length === 0
        ? "—"
        : `${Math.round(netos.reduce((a, b) => a + b, 0) / netos.length).toLocaleString("es-AR")} kg`;
}

// ---------- Encabezado ----------

function actualizarReloj() {
    fechaHora.textContent = new Date().toLocaleString("es-AR", {
        dateStyle: "short",
        timeStyle: "medium",
    });
}

async function cargarNombreProveedor() {
    try {
        const respuesta = await fetchConToken(API_PROVEEDORES);
        if (!respuesta.ok) throw new Error(`GET /suppliers/ respondió ${respuesta.status}`);
        const proveedores = await respuesta.json();
        const mio = proveedores.find((p) => Number(p.id) === Number(sesion.supplier_id));
        if (!mio) throw new Error(`El proveedor ${sesion.supplier_id} no vino en la lista: ${JSON.stringify(proveedores)}`);
        nombreProveedor.textContent = mio.name;
    } catch (error) {
        console.error("Error al cargar el proveedor:", error);
        nombreProveedor.textContent = `Proveedor #${sesion.supplier_id}`;
    }
}

// ---------- Tablas ----------

function filaTicketCompleta(t) {
    const fila = document.createElement("tr");
    fila.append(
        crearCelda(t.id),
        crearCelda(formatoFecha(t.fecha)),
        crearCelda(t.chofer),
        crearCelda(t.patente ?? "—"),
        crearCelda(formatoPeso(t.peso_tara)),
        crearCelda(formatoPeso(t.peso_bruto)),
        crearCelda(formatoPeso(t.peso_neto)),
        crearCeldaEstado(t.estado)
    );
    return fila;
}

function filaTicketMes(t) {
    const fila = document.createElement("tr");
    fila.append(
        crearCelda(t.id),
        crearCelda(formatoFecha(t.fecha)),
        crearCelda(t.patente ?? "—"),
        crearCelda(formatoPeso(t.peso_neto)),
        crearCeldaEstado(t.estado)
    );
    return fila;
}

function coincideConBusqueda(t, texto) {
    if (texto === "") return true;
    const patente = (t.patente ?? "").toLowerCase();
    return patente.includes(texto) || t.fecha.includes(texto) || formatoFecha(t.fecha).includes(texto);
}

function dibujarTablaTodos() {
    const texto = buscador.value.trim().toLowerCase();
    const filtrados = tickets.filter((t) => coincideConBusqueda(t, texto));

    if (tickets.length === 0) {
        mostrarFilaUnica(tablaTodos, "Todavía no hay pesadas registradas", 8);
    } else if (filtrados.length === 0) {
        mostrarFilaUnica(tablaTodos, "Ningún ticket coincide con la búsqueda", 8);
    } else {
        tablaTodos.replaceChildren(...filtrados.map(filaTicketCompleta));
    }
}

function dibujarTablaMes() {
    const prefijo = fechaLocalISO().slice(0, 7);
    const delMes = tickets.filter((t) => t.fecha.startsWith(prefijo));

    if (delMes.length === 0) {
        mostrarFilaUnica(tablaMes, "No hay pesadas este mes", 5);
    } else {
        tablaMes.replaceChildren(...delMes.map(filaTicketMes));
    }
}

async function cargarTickets() {
    try {
        const respuesta = await fetchConToken(API_TICKETS);
        if (!respuesta.ok) throw new Error(`Error ${respuesta.status}`);
        tickets = await respuesta.json();   // el backend ya filtra por supplier_id
        actualizarEstadisticas();
        dibujarTablaTodos();
        dibujarTablaMes();
    } catch (error) {
        console.error("Error al cargar los tickets:", error);
        const msg = "No se pudo cargar el historial. ¿Está encendida la API?";
        mostrarFilaUnica(tablaTodos, msg, 8);
        mostrarFilaUnica(tablaMes, msg, 5);
    }
}

// ---------- Inicio ----------

document.getElementById("btn-salir").addEventListener("click", cerrarSesion);
document.getElementById("btn-buscar").addEventListener("click", () => buscador.focus());
buscador.addEventListener("input", dibujarTablaTodos);

if (accesoPermitido) {
    actualizarReloj();
    setInterval(actualizarReloj, 1000);
    cargarNombreProveedor();
    cargarTickets();
}