// facturas.js: facturas por proveedor y período (solo admin)

const API_TICKETS = `${API_BASE}/tickets/`;
const API_PROVEEDORES = `${API_BASE}/suppliers/`;
const API_PRODUCTOS = `${API_BASE}/products/`;
const API_FACTURAS = `${API_BASE}/facturas/`;
const METODOS_DE_PAGO = ["Transferencia", "Efectivo", "Cheque", "E-Cheq", "Cuenta Corriente"];

// Guardia de rol (obtenerSesion, borrarToken, fetchConToken y cerrarSesion vienen de auth.js)
const sesion = obtenerSesion();
const accesoPermitido = sesion !== null && sesion.rol === "admin";
if (!accesoPermitido) {
    borrarToken();
    location.replace("login.html");
}

// Elementos

const $ = (id) => document.getElementById(id);
const buscarProveedor = $("buscar-proveedor");
const fechaDesde = $("fecha-desde");
const fechaHasta = $("fecha-hasta");
const btnGenerar = $("btn-generar");
const mensaje = $("mensaje");
const tablaResumen = $("tabla-resumen");
const tablaDetalle = $("tabla-detalle");
const tablaFacturas = $("tabla-facturas");
const modalFactura = $("modal-generar-factura");
const facturaMetodo = $("factura-metodo");
const facturaEstado = $("factura-estado");
const modalPago = $("modal-pago");
const pagoMetodo = $("pago-metodo");
const modalConfirmar = $("modal-confirmar");

// Estado

let tickets = [];
let proveedores = [];        // [{ id, name }] ordenados por nombre
let productosPorId = {};
let facturas = [];           // ya vienen ordenadas de la más nueva a la más vieja
let proveedorElegido = null; // { id, name } o null (vista general)
let facturaEnAccion = null;  // la factura a pagar o anular

// Utilidades

function mostrarMensaje(texto, tipo) {
    mensaje.textContent = texto;
    mensaje.className = `aviso ${tipo === "ok" ? "aviso-ok" : "aviso-error"}`;
    mensaje.style.display = "block";
}

function textoDeError(detail) {
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((e) => e.msg.replace(/^Value error, /, "")).join(" | ");
    return "Error desconocido";
}

function mostrarError(elemento, texto) {
    elemento.textContent = texto;
    elemento.style.display = "block";
}

const formatoFecha = (fecha) => fecha.split("-").reverse().join("/");
const formatoKilos = (valor) => (valor === null ? "—" : `${valor.toLocaleString("es-AR")} kg`);
const formatoPesos = (valor) => valor.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const nombreProveedor = (id) => proveedores.find((p) => p.id === id)?.name ?? `Proveedor ${id}`;

function fechaDeHoy() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function crearCelda(texto) {
    const td = document.createElement("td");
    td.textContent = texto;
    return td;
}

function crearCartel(texto, color) {
    const cartel = document.createElement("span");
    cartel.className = `cartel ${color}`; // cartel-azul | cartel-rojo | cartel-verde | cartel-amarillo | cartel-neutro
    cartel.textContent = texto;
    return cartel;
}

function celdaCon(...hijos) {
    const td = document.createElement("td");
    td.append(...hijos);
    return td;
}

function crearBoton(texto, clase, alHacerClic) {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = `boton boton-chico ${clase}`;
    boton.textContent = texto;
    boton.addEventListener("click", alHacerClic);
    return boton;
}

function mostrarFilaUnica(tbody, texto, columnas) {
    const fila = document.createElement("tr");
    const celda = crearCelda(texto);
    celda.colSpan = columnas;
    celda.className = "centrado";
    fila.appendChild(celda);
    tbody.replaceChildren(fila);
}

function opcionesDeMetodo(select) {
    select.replaceChildren(...METODOS_DE_PAGO.map((m) => {
        const opcion = document.createElement("option");
        opcion.value = m;
        opcion.textContent = m;
        return opcion;
    }));
}

// Período y pesadas

const pendienteDeFacturar = (t) => t.estado === "cerrado" && !t.facturado;
const rangoCompleto = () => fechaDesde.value !== "" && fechaHasta.value !== "";
const rangoInvalido = () => rangoCompleto() && fechaDesde.value > fechaHasta.value;

function enRango(t) {
    if (fechaDesde.value !== "" && t.fecha < fechaDesde.value) return false;
    if (fechaHasta.value !== "" && t.fecha > fechaHasta.value) return false;
    return true;
}

// Pesadas que entrarían en una factura nueva del proveedor elegido
function pesadasAFacturar() {
    if (proveedorElegido === null || !rangoCompleto() || rangoInvalido()) return [];
    return tickets.filter((t) => t.supplier_id === proveedorElegido.id && enRango(t) && pendienteDeFacturar(t));
}

// Vista general: estado por proveedor

function cartelDeProveedor(propios) {
    if (propios.length === 0) return crearCartel("Sin pesadas", "cartel-neutro");
    if (!propios.some((t) => t.estado === "cerrado")) return crearCartel("Sin pesadas cerradas", "cartel-neutro");
    const pendientes = propios.filter(pendienteDeFacturar).length;
    return pendientes === 0 ? crearCartel("Todo facturado", "cartel-azul") : crearCartel(`${pendientes} sin facturar`, "cartel-rojo");
}

function renderizarResumen() {
    const texto = buscarProveedor.value.trim().toLowerCase();
    const visibles = proveedores.filter((p) => p.name.toLowerCase().includes(texto));
    if (visibles.length === 0) {
        mostrarFilaUnica(tablaResumen, proveedores.length === 0
            ? "No hay proveedores cargados" : "Ningún proveedor coincide con la búsqueda", 3);
        return;
    }
    tablaResumen.replaceChildren(...visibles.map((p) => {
        const propios = tickets.filter((t) => t.supplier_id === p.id);
        const abiertos = propios.filter((t) => t.estado === "abierto").length;
        const fila = document.createElement("tr");
        fila.className = "fila-proveedor";
        fila.title = `Ver las pesadas y facturas de ${p.name}`;
        fila.addEventListener("click", () => elegirProveedor(p));
        const nombre = document.createElement("strong");
        nombre.textContent = p.name;
        fila.append(
            celdaCon(nombre),
            crearCelda(abiertos > 0 ? `${propios.length} (${abiertos} ${abiertos === 1 ? "abierta" : "abiertas"})` : String(propios.length)),
            celdaCon(cartelDeProveedor(propios)),
        );
        return fila;
    }));
}

// Vista de un proveedor: sus pesadas

function renderizarDetalle() {
    $("titulo-detalle").textContent = `Pesadas de ${proveedorElegido.name}`;
    const resumen = $("resumen-detalle");
    if (rangoInvalido()) {
        resumen.textContent = "";
        mostrarFilaUnica(tablaDetalle, "La fecha Desde es posterior a Hasta", 7);
        return;
    }
    const propios = tickets.filter((t) => t.supplier_id === proveedorElegido.id && enRango(t));
    const pendientes = propios.filter(pendienteDeFacturar);
    const neto = pendientes.reduce((suma, t) => suma + t.peso_neto, 0);
    resumen.textContent = `${propios.length} ${propios.length === 1 ? "pesada" : "pesadas"} · ` +
        `${pendientes.length} cerradas sin facturar · neto pendiente: ${formatoKilos(neto)}`;
    if (propios.length === 0) {
        mostrarFilaUnica(tablaDetalle, fechaDesde.value || fechaHasta.value
            ? "No hay pesadas en ese rango de fechas" : "Este proveedor no tiene pesadas", 7);
        return;
    }
    const numeroPorFactura = Object.fromEntries(facturas.map((f) => [f.id, f.numero_factura]));
    tablaDetalle.replaceChildren(...propios.map((t) => {
        const estado = celdaCon(t.facturado ? crearCartel("Facturado", "cartel-azul") : crearCartel("No facturado", "cartel-rojo"));
        if (t.estado === "abierto") estado.append(crearCartel("Abierto", "cartel-neutro"));
        const fila = document.createElement("tr");
        fila.append(
            crearCelda(t.id),
            crearCelda(formatoFecha(t.fecha)),
            crearCelda(t.patente ?? "—"),
            crearCelda(t.product_id === null ? "—" : (productosPorId[t.product_id] ?? t.product_id)),
            crearCelda(formatoKilos(t.peso_neto)),
            estado,
            crearCelda(t.factura_id === null ? "—" : (numeroPorFactura[t.factura_id] ?? `#${t.factura_id}`)),
        );
        return fila;
    }));
}

// Facturas (todas o las del proveedor elegido)

function renderizarFacturas() {
    const deUno = proveedorElegido !== null;
    $("titulo-facturas").textContent = deUno ? `Historial de facturas de ${proveedorElegido.name}` : "Últimas facturas emitidas";
    $("col-proveedor").style.display = deUno ? "none" : "";
    const lista = deUno ? facturas.filter((f) => f.supplier_id === proveedorElegido.id) : facturas;
    if (lista.length === 0) {
        mostrarFilaUnica(tablaFacturas, "Todavía no hay facturas", 9);
        return;
    }
    tablaFacturas.replaceChildren(...lista.map((f) => {
        const acciones = celdaCon();
        acciones.style.whiteSpace = "nowrap";
        if (!f.pagado) acciones.append(crearBoton("Registrar pago", "boton-principal", () => abrirPago(f)));
        acciones.append(crearBoton("Anular", "boton-rojo-contorno", () => abrirAnular(f)));

        const fila = document.createElement("tr");
        fila.append(crearCelda(f.numero_factura), crearCelda(formatoFecha(f.fecha_factura)));
        if (!deUno) fila.append(crearCelda(nombreProveedor(f.supplier_id)));
        fila.append(
            crearCelda(`${formatoFecha(f.fecha_desde)} al ${formatoFecha(f.fecha_hasta)}`),
            crearCelda(f.cantidad_tickets),
            crearCelda(formatoPesos(f.total)),
            celdaCon(f.pagado ? crearCartel("Pagada", "cartel-verde") : crearCartel("Pendiente", "cartel-amarillo")),
            crearCelda(f.metodo_pago ?? "—"),
            acciones,
        );
        return fila;
    }));
}

// Navegación

function actualizarBotonGenerar() {
    const cantidad = pesadasAFacturar().length;
    btnGenerar.disabled = cantidad === 0;
    if (proveedorElegido === null) btnGenerar.title = "Elegí un proveedor";
    else if (!rangoCompleto()) btnGenerar.title = "Elegí las fechas Desde y Hasta";
    else if (rangoInvalido()) btnGenerar.title = "La fecha Desde es posterior a Hasta";
    else if (cantidad === 0) btnGenerar.title = "No hay pesadas cerradas sin facturar en ese período";
    else btnGenerar.title = `Facturar ${cantidad} ${cantidad === 1 ? "pesada" : "pesadas"} de ${proveedorElegido.name}`;
}

function renderizar() {
    const deUno = proveedorElegido !== null;
    $("vista-resumen").style.display = deUno ? "none" : "block";
    $("vista-detalle").style.display = deUno ? "block" : "none";
    if (deUno) renderizarDetalle();
    else renderizarResumen();
    renderizarFacturas();
    actualizarBotonGenerar();
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
        let listaProveedores, listaProductos;
        [tickets, listaProveedores, listaProductos, facturas] = await Promise.all([
            pedirJSON(API_TICKETS), pedirJSON(API_PROVEEDORES), pedirJSON(API_PRODUCTOS), pedirJSON(API_FACTURAS),
        ]);
        proveedores = listaProveedores.map((p) => ({ id: p.id, name: p.name })).sort((a, b) => a.name.localeCompare(b.name));
        productosPorId = Object.fromEntries(listaProductos.map((p) => [p.id, p.name]));
        $("lista-proveedores").replaceChildren(...proveedores.map((p) => {
            const opcion = document.createElement("option");
            opcion.value = p.name;
            return opcion;
        }));
        if (proveedorElegido !== null) proveedorElegido = proveedores.find((p) => p.id === proveedorElegido.id) ?? null;
        renderizar();
    } catch (error) {
        console.error("Error al cargar los datos:", error);
        mostrarFilaUnica(tablaResumen, "No se pudieron cargar los datos", 3);
        mostrarFilaUnica(tablaFacturas, "No se pudieron cargar las facturas", 9);
    }
}

// Pedidos a la API con el error dentro del modal (400 / 404 / 409 / 422)

async function enviar(url, metodo, cuerpo, elementoError) {
    try {
        const respuesta = await fetchConToken(url, {
            method: metodo,
            headers: { "Content-Type": "application/json" },
            body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
        });
        if (respuesta.ok) return respuesta.status === 204 ? {} : await respuesta.json();
        const error = await respuesta.json().catch(() => ({}));
        mostrarError(elementoError, error.detail ? textoDeError(error.detail) : `Error ${respuesta.status}`);
    } catch (error) {
        console.error(`Error en ${metodo} ${url}:`, error);
        mostrarError(elementoError, "No se pudo conectar con el servidor.");
    }
    return null;
}

const cerrarModal = (modal) => { modal.style.display = "none"; };

// Generar factura

function abrirGenerar() {
    const lote = pesadasAFacturar();
    if (lote.length === 0) return;
    const neto = lote.reduce((suma, t) => suma + t.peso_neto, 0);
    $("factura-resumen").textContent =
        `${proveedorElegido.name} · del ${formatoFecha(fechaDesde.value)} al ${formatoFecha(fechaHasta.value)} · ` +
        `${lote.length} ${lote.length === 1 ? "pesada cerrada" : "pesadas cerradas"} · ${formatoKilos(neto)} netos`;
    $("form-factura").reset();
    $("factura-fecha").value = fechaDeHoy();
    actualizarMetodoFactura();
    $("factura-error").style.display = "none";
    modalFactura.style.display = "block";
    setTimeout(() => $("factura-numero").focus(), 50);
}

// El método de pago solo se elige (y es obligatorio) si la factura está pagada
function actualizarMetodoFactura() {
    facturaMetodo.disabled = facturaEstado.value !== "pagada";
}

$("form-factura").addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorEl = $("factura-error");
    const pagado = facturaEstado.value === "pagada";
    const datos = {
        supplier_id: proveedorElegido.id,
        numero_factura: $("factura-numero").value.trim(),
        fecha_factura: $("factura-fecha").value,
        fecha_desde: fechaDesde.value,
        fecha_hasta: fechaHasta.value,
        total: Number($("factura-total").value),
        pagado,
        metodo_pago: pagado ? facturaMetodo.value : null,
    };
    if (datos.numero_factura === "") return mostrarError(errorEl, "El N° de factura es obligatorio");
    if (datos.fecha_factura === "") return mostrarError(errorEl, "La fecha de factura es obligatoria");
    if (!(datos.total > 0)) return mostrarError(errorEl, "El total tiene que ser mayor a 0");

    const guardar = $("factura-guardar");
    guardar.disabled = true;
    const creada = await enviar(API_FACTURAS, "POST", datos, errorEl);
    guardar.disabled = false;
    if (creada === null) return;
    cerrarModal(modalFactura);
    mostrarMensaje(`Factura ${creada.numero_factura} generada con ${creada.cantidad_tickets} ${creada.cantidad_tickets === 1 ? "pesada" : "pesadas"}`, "ok");
    await cargarTodo();
});

// Registrar pago

function abrirPago(factura) {
    facturaEnAccion = factura;
    $("pago-titulo").textContent = `Registrar pago de ${factura.numero_factura}`;
    $("pago-error").style.display = "none";
    pagoMetodo.value = METODOS_DE_PAGO[0];
    modalPago.style.display = "block";
}

$("pago-guardar").addEventListener("click", async () => {
    const actualizada = await enviar(`${API_FACTURAS}${facturaEnAccion.id}/pago`, "PATCH",
        { pagado: true, metodo_pago: pagoMetodo.value }, $("pago-error"));
    if (actualizada === null) return;
    cerrarModal(modalPago);
    mostrarMensaje(`Factura ${actualizada.numero_factura} pagada (${actualizada.metodo_pago})`, "ok");
    await cargarTodo();
});

// Anular factura

function abrirAnular(factura) {
    facturaEnAccion = factura;
    $("confirmar-texto").textContent =
        `Se va a anular la factura ${factura.numero_factura} de ${nombreProveedor(factura.supplier_id)}. ` +
        `Sus ${factura.cantidad_tickets} ${factura.cantidad_tickets === 1 ? "pesada vuelve" : "pesadas vuelven"} a quedar sin facturar.`;
    $("confirmar-error").style.display = "none";
    modalConfirmar.style.display = "block";
}

$("confirmar-aceptar").addEventListener("click", async () => {
    const anulada = await enviar(`${API_FACTURAS}${facturaEnAccion.id}`, "DELETE", undefined, $("confirmar-error"));
    if (anulada === null) return;
    cerrarModal(modalConfirmar);
    mostrarMensaje(`Factura ${facturaEnAccion.numero_factura} anulada`, "ok");
    await cargarTodo();
});

// Eventos y arranque

opcionesDeMetodo(facturaMetodo);
opcionesDeMetodo(pagoMetodo);
facturaEstado.addEventListener("change", actualizarMetodoFactura);
buscarProveedor.addEventListener("input", alEscribirProveedor);
fechaDesde.addEventListener("change", renderizar);
fechaHasta.addEventListener("change", renderizar);
btnGenerar.addEventListener("click", abrirGenerar);
$("factura-cancelar").addEventListener("click", () => cerrarModal(modalFactura));
$("pago-cancelar").addEventListener("click", () => cerrarModal(modalPago));
$("confirmar-cancelar").addEventListener("click", () => cerrarModal(modalConfirmar));
for (const modal of [modalFactura, modalPago, modalConfirmar]) {
    modal.addEventListener("click", (event) => { if (event.target === modal) cerrarModal(modal); }); // fondo oscuro
}
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") [modalFactura, modalPago, modalConfirmar].forEach(cerrarModal);
});
$("btn-limpiar").addEventListener("click", () => {
    buscarProveedor.value = "";
    fechaDesde.value = "";
    fechaHasta.value = "";
    proveedorElegido = null;
    mensaje.style.display = "none";
    renderizar();
});
$("btn-logout").addEventListener("click", cerrarSesion);

if (accesoPermitido) {
    $("nombre-usuario").textContent = sesion.username;
    cargarTodo();
}
