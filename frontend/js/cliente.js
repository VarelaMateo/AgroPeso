// Usa de auth.js: API_BASE, obtenerSesion, borrarToken, cerrarSesion, fetchConToken
const API_TICKETS = `${API_BASE}/tickets/`;
const API_PROVEEDORES = `${API_BASE}/suppliers/`;
const API_PRODUCTOS = `${API_BASE}/products/`;
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
const statNetoFiltrado = document.getElementById("stat-neto-filtrado");
const statCerradasFiltradas = document.getElementById("stat-cerradas-filtradas");
const filtroProducto = document.getElementById("filtro-producto");
const filtroDesde = document.getElementById("filtro-desde");
const filtroHasta = document.getElementById("filtro-hasta");
const avisoExportar = document.getElementById("aviso-exportar");

function mesAnteriorISO() {
    const hoy = new Date();
    const anterior = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1);
    return fechaLocalISO(anterior).slice(0, 7);
}

let tickets = [];
let productosPorId = {};
let ticketsFiltrados = []; // lo que muestra "Todos los tickets": es exactamente lo que se descarga
let nombreDelProveedor = "";

const COLUMNAS_TODOS = 9;
const COLUMNAS_MES = 6;

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

// El producto es opcional: sin producto se muestra "—"; si no está en el mapa, su id
function nombreProducto(productId) {
    if (productId === null) return "—";
    return productosPorId[productId] ?? productId;
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
        nombreDelProveedor = mio.name;
    } catch (error) {
        console.error("Error al cargar el proveedor:", error);
        nombreProveedor.textContent = `Proveedor #${sesion.supplier_id}`;
    }
}

// Si falla, las tablas muestran el id del producto en lugar del nombre
async function cargarProductos() {
    try {
        const respuesta = await fetchConToken(API_PRODUCTOS);
        if (!respuesta.ok) throw new Error(`GET /products/ respondió ${respuesta.status}`);
        const productos = await respuesta.json();
        productosPorId = Object.fromEntries(productos.map((p) => [p.id, p.name]));
        actualizarSelectFiltro(filtroProducto, "Todos los productos", productosPorId);
    } catch (error) {
        console.error("Error al cargar los productos:", error);
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
        crearCelda(nombreProducto(t.product_id)),
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
        crearCelda(nombreProducto(t.product_id)),
        crearCelda(formatoPeso(t.peso_neto)),
        crearCeldaEstado(t.estado)
    );
    return fila;
}

function leerFiltros() {
    return {
        texto: buscador.value.trim().toLowerCase(),
        productId: filtroProducto.value,
        desde: filtroDesde.value,
        hasta: filtroHasta.value,
    };
}

// Total neto de los tickets cerrados que pasan el filtro actual
function actualizarNetoFiltrado() {
    const cerrados = ticketsFiltrados.filter((t) => t.estado === "cerrado");
    const total = cerrados.reduce((suma, t) => suma + t.peso_neto, 0);
    statNetoFiltrado.textContent = `${total.toLocaleString("es-AR")} kg`;
    statCerradasFiltradas.textContent = `${cerrados.length} ${cerrados.length === 1 ? "pesada cerrada" : "pesadas cerradas"}`;
}

function dibujarTablaTodos() {
    const f = leerFiltros();
    const invalido = rangoInvalido(f.desde, f.hasta);
    // El buscador también acepta la fecha escrita (2026-11-20 o 20/11/2026), como antes
    ticketsFiltrados = invalido ? [] : tickets.filter((t) =>
        coincideConFiltros(t, f, [t.fecha, formatoFecha(t.fecha)]));
    actualizarNetoFiltrado();

    if (tickets.length === 0) {
        mostrarFilaUnica(tablaTodos, "Todavía no hay pesadas registradas", COLUMNAS_TODOS);
    } else if (invalido) {
        mostrarFilaUnica(tablaTodos, "La fecha Desde es posterior a Hasta", COLUMNAS_TODOS);
    } else if (ticketsFiltrados.length === 0) {
        mostrarFilaUnica(tablaTodos, "Ningún ticket coincide con los filtros", COLUMNAS_TODOS);
    } else {
        tablaTodos.replaceChildren(...ticketsFiltrados.map(filaTicketCompleta));
    }
}

// Descarga exactamente las filas de "Todos los tickets" (el backend ya limita a su proveedor)
function descargarExcel() {
    if (ticketsFiltrados.length === 0) {
        mostrarAvisoInline(avisoExportar, "No hay tickets para exportar con los filtros seleccionados");
        return;
    }
    const f = leerFiltros();
    const partes = ["MisPesadas"];
    if (f.productId !== "") partes.push(productosPorId[f.productId]);

    const contenido = generarCSV(
        ticketsFiltrados,
        () => nombreDelProveedor || `Proveedor ${sesion.supplier_id}`,
        (t) => nombreProducto(t.product_id),
    );
    descargarCSV(nombreDeArchivo(partes, f.desde, f.hasta, fechaLocalISO()), contenido);
}

function dibujarTablaMes() {
    const prefijo = fechaLocalISO().slice(0, 7);
    const delMes = tickets.filter((t) => t.fecha.startsWith(prefijo));

    if (delMes.length === 0) {
        mostrarFilaUnica(tablaMes, "No hay pesadas este mes", COLUMNAS_MES);
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
        mostrarFilaUnica(tablaTodos, msg, COLUMNAS_TODOS);
        mostrarFilaUnica(tablaMes, msg, COLUMNAS_MES);
    }
}

// ---------- Inicio ----------

document.getElementById("btn-salir").addEventListener("click", cerrarSesion);
document.getElementById("btn-buscar").addEventListener("click", () => buscador.focus());
buscador.addEventListener("input", dibujarTablaTodos);
for (const filtro of [filtroProducto, filtroDesde, filtroHasta]) {
    filtro.addEventListener("change", dibujarTablaTodos);
}
document.getElementById("btn-limpiar-filtros").addEventListener("click", () => {
    buscador.value = "";
    filtroProducto.value = "";
    filtroDesde.value = "";
    filtroHasta.value = "";
    dibujarTablaTodos();
});
document.getElementById("btn-descargar").addEventListener("click", descargarExcel);

if (accesoPermitido) {
    actualizarReloj();
    setInterval(actualizarReloj, 1000);
    cargarNombreProveedor();
    cargarProductos().then(cargarTickets); // los nombres de producto tienen que estar antes de dibujar
}