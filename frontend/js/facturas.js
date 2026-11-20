// facturas.js: estado de facturación por proveedor y facturación por lote (solo admin)

const API_TICKETS = `${API_BASE}/tickets/`;
const API_PROVEEDORES = `${API_BASE}/suppliers/`;
const API_PRODUCTOS = `${API_BASE}/products/`;
const API_FACTURAR = `${API_BASE}/tickets/facturar`;

// Guardia de rol (obtenerSesion, borrarToken, fetchConToken y cerrarSesion vienen de auth.js)
const sesion = obtenerSesion();
const accesoPermitido = sesion !== null && sesion.rol === "admin";
if (!accesoPermitido) {
    borrarToken();
    location.replace("login.html");
}

// Elementos y estado

const buscarProveedor = document.getElementById("buscar-proveedor");
const listaProveedores = document.getElementById("lista-proveedores");
const fechaDesde = document.getElementById("fecha-desde");
const fechaHasta = document.getElementById("fecha-hasta");
const btnFacturar = document.getElementById("btn-facturar");
const btnDesmarcar = document.getElementById("btn-desmarcar");
const mensaje = document.getElementById("mensaje");
const vistaResumen = document.getElementById("vista-resumen");
const vistaDetalle = document.getElementById("vista-detalle");
const tablaResumen = document.getElementById("tabla-resumen");
const tablaDetalle = document.getElementById("tabla-detalle");
const tituloDetalle = document.getElementById("titulo-detalle");
const resumenDetalle = document.getElementById("resumen-detalle");
const modalConfirmar = document.getElementById("modal-confirmar");
const confirmarTexto = document.getElementById("confirmar-texto");
const confirmarTitulo = document.getElementById("confirmar-titulo");
const confirmarError = document.getElementById("confirmar-error");
const confirmarAceptar = document.getElementById("confirmar-aceptar");

let tickets = [];
let proveedores = [];      // [{ id, name }] ordenados por nombre
let productosPorId = {};
let proveedorElegido = null; // { id, name } o null (vista de resumen)
let marcarComoFacturado = true; // qué hace el modal: facturar (true) o deshacer la facturación (false)

// Utilidades

function mostrarMensaje(texto, tipo) {
    mensaje.textContent = texto;
    mensaje.className = `aviso ${tipo === "ok" ? "aviso-ok" : "aviso-error"}`;
    mensaje.style.display = "block";
}

function textoDeError(detail) {
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((e) => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(" | ");
    return "Error desconocido";
}

function formatoFecha(fecha) {
    return fecha.split("-").reverse().join("/");
}

function formatoPeso(valor) {
    return valor === null ? "—" : `${valor.toLocaleString("es-AR")} kg`;
}

function crearCelda(texto) {
    const td = document.createElement("td");
    td.textContent = texto;
    return td;
}

function crearCartel(texto, color) {
    const cartel = document.createElement("span");
    cartel.className = `cartel ${color}`; // color: cartel-azul | cartel-rojo | cartel-neutro
    cartel.textContent = texto;
    return cartel;
}

function mostrarFilaUnica(tbody, texto, columnas) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = columnas;
    celda.className = "centrado";
    celda.textContent = texto;
    fila.appendChild(celda);
    tbody.replaceChildren(fila);
}

// Solo los cerrados se pueden facturar: un ticket abierto todavía no tiene peso neto
function pendienteDeFacturar(t) {
    return t.estado === "cerrado" && !t.facturado;
}

function rangoCompleto() {
    return fechaDesde.value !== "" && fechaHasta.value !== "";
}

function rangoInvalido() {
    return rangoCompleto() && fechaDesde.value > fechaHasta.value;
}

function enRango(t) {
    if (fechaDesde.value !== "" && t.fecha < fechaDesde.value) return false;
    if (fechaHasta.value !== "" && t.fecha > fechaHasta.value) return false;
    return true;
}

// Vista 1: resumen por proveedor

function cartelDeProveedor(propios) {
    if (propios.length === 0) return crearCartel("Sin pesadas", "cartel-neutro");
    // Solo abiertas: no hay nada para facturar todavía (no es "todo facturado")
    if (!propios.some((t) => t.estado === "cerrado")) return crearCartel("Sin pesadas cerradas", "cartel-neutro");
    const pendientes = propios.filter(pendienteDeFacturar).length;
    if (pendientes === 0) return crearCartel("Todo facturado", "cartel-azul");
    return crearCartel(`${pendientes} sin facturar`, "cartel-rojo");
}

function renderizarResumen() {
    const texto = buscarProveedor.value.trim().toLowerCase();
    const visibles = proveedores.filter((p) => p.name.toLowerCase().includes(texto));

    if (visibles.length === 0) {
        mostrarFilaUnica(tablaResumen, proveedores.length === 0
            ? "No hay proveedores cargados" : "Ningún proveedor coincide con la búsqueda", 3);
        return;
    }

    const filas = visibles.map((p) => {
        const propios = tickets.filter((t) => t.supplier_id === p.id);
        const abiertos = propios.filter((t) => t.estado === "abierto").length;

        const fila = document.createElement("tr");
        fila.className = "fila-proveedor";
        fila.title = `Ver las pesadas de ${p.name}`;
        fila.addEventListener("click", () => elegirProveedor(p));

        const nombre = document.createElement("td");
        const negrita = document.createElement("strong");
        negrita.textContent = p.name;
        nombre.appendChild(negrita);

        const cantidad = crearCelda(abiertos > 0
            ? `${propios.length} (${abiertos} ${abiertos === 1 ? "abierta" : "abiertas"})`
            : String(propios.length));

        const estado = document.createElement("td");
        estado.appendChild(cartelDeProveedor(propios));

        fila.append(nombre, cantidad, estado);
        return fila;
    });
    tablaResumen.replaceChildren(...filas);
}

// Vista 2: detalle de un proveedor

function cartelesDeTicket(t) {
    const celda = document.createElement("td");
    celda.appendChild(t.facturado ? crearCartel("Facturado", "cartel-azul") : crearCartel("No facturado", "cartel-rojo"));
    if (t.estado === "abierto") {
        celda.append(crearCartel("Abierto", "cartel-neutro"));
    }
    return celda;
}

function renderizarDetalle() {
    tituloDetalle.textContent = `Pesadas de ${proveedorElegido.name}`;

    if (rangoInvalido()) {
        resumenDetalle.textContent = "";
        mostrarFilaUnica(tablaDetalle, "La fecha Desde es posterior a Hasta", 6);
        return;
    }

    const propios = tickets.filter((t) => t.supplier_id === proveedorElegido.id && enRango(t));
    const pendientes = propios.filter(pendienteDeFacturar);
    const netoPendiente = pendientes.reduce((suma, t) => suma + t.peso_neto, 0);
    resumenDetalle.textContent =
        `${propios.length} ${propios.length === 1 ? "pesada" : "pesadas"} · ` +
        `${pendientes.length} cerradas sin facturar · neto pendiente: ${formatoPeso(netoPendiente)}`;

    if (propios.length === 0) {
        mostrarFilaUnica(tablaDetalle, rangoCompleto() || fechaDesde.value || fechaHasta.value
            ? "No hay pesadas en ese rango de fechas" : "Este proveedor no tiene pesadas", 6);
        return;
    }

    const filas = propios.map((t) => {
        const fila = document.createElement("tr");
        fila.append(
            crearCelda(t.id),
            crearCelda(formatoFecha(t.fecha)),
            crearCelda(t.patente ?? "—"),
            crearCelda(t.product_id === null ? "—" : (productosPorId[t.product_id] ?? t.product_id)),
            crearCelda(formatoPeso(t.peso_neto)),
            cartelesDeTicket(t),
        );
        return fila;
    });
    tablaDetalle.replaceChildren(...filas);
}

// Navegación entre vistas

function actualizarBotonFacturar() {
    const listo = proveedorElegido !== null && rangoCompleto() && !rangoInvalido();
    btnFacturar.disabled = !listo;
    btnDesmarcar.disabled = !listo;
    if (proveedorElegido === null) btnFacturar.title = "Elegí un proveedor";
    else if (!rangoCompleto()) btnFacturar.title = "Elegí las fechas Desde y Hasta";
    else if (rangoInvalido()) btnFacturar.title = "La fecha Desde es posterior a Hasta";
    else btnFacturar.title = `Facturar las pesadas cerradas de ${proveedorElegido.name} en ese rango`;
    btnDesmarcar.title = listo ? "Deshacer la facturación de ese rango (por si se marcó por error)" : btnFacturar.title;
}

function renderizar() {
    const enDetalle = proveedorElegido !== null;
    vistaResumen.style.display = enDetalle ? "none" : "block";
    vistaDetalle.style.display = enDetalle ? "block" : "none";
    if (enDetalle) renderizarDetalle();
    else renderizarResumen();
    actualizarBotonFacturar();
}

function elegirProveedor(proveedor) {
    proveedorElegido = proveedor;
    buscarProveedor.value = proveedor.name;
    renderizar();
}

// Si lo escrito coincide con un proveedor (sin importar mayúsculas), se elige; si no, filtra el resumen
function alEscribirProveedor() {
    const texto = buscarProveedor.value.trim().toLowerCase();
    proveedorElegido = proveedores.find((p) => p.name.toLowerCase() === texto) ?? null;
    renderizar();
}

// Carga de datos (la API es la fuente de verdad)

async function pedirJSON(url) {
    const respuesta = await fetchConToken(url);
    if (!respuesta.ok) throw new Error(`Error ${respuesta.status} en ${url}`);
    return respuesta.json();
}

async function cargarTodo() {
    try {
        const [listaTickets, listaProveedoresApi, listaProductos] = await Promise.all([
            pedirJSON(API_TICKETS), pedirJSON(API_PROVEEDORES), pedirJSON(API_PRODUCTOS),
        ]);
        tickets = listaTickets;
        proveedores = listaProveedoresApi
            .map((p) => ({ id: p.id, name: p.name }))
            .sort((a, b) => a.name.localeCompare(b.name));
        productosPorId = Object.fromEntries(listaProductos.map((p) => [p.id, p.name]));

        listaProveedores.replaceChildren(...proveedores.map((p) => {
            const opcion = document.createElement("option");
            opcion.value = p.name;
            return opcion;
        }));
        // Si había un proveedor elegido, se vuelve a tomar con los datos nuevos
        if (proveedorElegido !== null) {
            proveedorElegido = proveedores.find((p) => p.id === proveedorElegido.id) ?? null;
        }
        renderizar();
    } catch (error) {
        console.error("Error al cargar los datos:", error);
        mostrarFilaUnica(tablaResumen, "No se pudieron cargar los datos", 3);
    }
}

// Facturación por lote con confirmación

function abrirConfirmacion(marcar) {
    if (btnFacturar.disabled) return;
    marcarComoFacturado = marcar;
    const afectadas = tickets.filter((t) => t.supplier_id === proveedorElegido.id && enRango(t)
        && t.estado === "cerrado" && t.facturado !== marcar).length;
    const rango = `de ${proveedorElegido.name} del ${formatoFecha(fechaDesde.value)} al ${formatoFecha(fechaHasta.value)}`;
    confirmarTitulo.textContent = marcar ? "Marcar como facturado" : "Desmarcar facturación";
    confirmarTexto.textContent = marcar
        ? `Se van a marcar como facturadas las pesadas cerradas ${rango} (${afectadas} ${afectadas === 1 ? "pendiente" : "pendientes"}).`
        : `Se va a deshacer la facturación de las pesadas ${rango} (${afectadas} ${afectadas === 1 ? "facturada" : "facturadas"}). Vuelven a quedar como no facturadas.`;
    confirmarError.style.display = "none";
    modalConfirmar.style.display = "block";
    setTimeout(() => confirmarAceptar.focus(), 50);
}

function cerrarConfirmacion() {
    modalConfirmar.style.display = "none";
}

async function facturar() {
    confirmarAceptar.disabled = true;
    try {
        const respuesta = await fetchConToken(API_FACTURAR, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                supplier_id: proveedorElegido.id,
                fecha_desde: fechaDesde.value,
                fecha_hasta: fechaHasta.value,
                facturado: marcarComoFacturado,
            }),
        });
        const cuerpo = await respuesta.json().catch(() => ({}));
        if (!respuesta.ok) {
            confirmarError.textContent = cuerpo.detail ? textoDeError(cuerpo.detail) : `Error ${respuesta.status}`;
            confirmarError.style.display = "block";
            return;
        }
        cerrarConfirmacion();
        const n = cuerpo.actualizados;
        const uno = n === 1;
        mostrarMensaje(marcarComoFacturado
            ? (n === 0 ? "No había pesadas cerradas sin facturar en ese rango"
                : `${n} ${uno ? "pesada marcada como facturada" : "pesadas marcadas como facturadas"}`)
            : (n === 0 ? "No había pesadas facturadas en ese rango"
                : `${n} ${uno ? "pesada vuelve" : "pesadas vuelven"} a estar sin facturar`), "ok");
        await cargarTodo();
    } catch (error) {
        console.error("Error al facturar:", error);
        confirmarError.textContent = "No se pudo conectar con el servidor.";
        confirmarError.style.display = "block";
    } finally {
        confirmarAceptar.disabled = false;
    }
}

// Eventos y arranque

buscarProveedor.addEventListener("input", alEscribirProveedor);
fechaDesde.addEventListener("change", renderizar);
fechaHasta.addEventListener("change", renderizar);
btnFacturar.addEventListener("click", () => abrirConfirmacion(true));
btnDesmarcar.addEventListener("click", () => abrirConfirmacion(false));
confirmarAceptar.addEventListener("click", facturar);
document.getElementById("confirmar-cancelar").addEventListener("click", cerrarConfirmacion);
modalConfirmar.addEventListener("click", (event) => {
    if (event.target === modalConfirmar) cerrarConfirmacion(); // clic en el fondo oscuro
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modalConfirmar.style.display === "block") cerrarConfirmacion();
});
document.getElementById("btn-limpiar").addEventListener("click", () => {
    buscarProveedor.value = "";
    fechaDesde.value = "";
    fechaHasta.value = "";
    proveedorElegido = null;
    mensaje.style.display = "none";
    renderizar();
});
document.getElementById("btn-logout").addEventListener("click", cerrarSesion);

if (accesoPermitido) {
    document.getElementById("nombre-usuario").textContent = sesion.username;
    cargarTodo();
}
