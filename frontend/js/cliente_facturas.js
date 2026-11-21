// cliente_facturas.js: estado de facturación de las pesadas del cliente (solo lectura)

const API_TICKETS = `${API_BASE}/tickets/`;
const API_PROVEEDORES = `${API_BASE}/suppliers/`;
const API_PRODUCTOS = `${API_BASE}/products/`;

// Guardia de rol (obtenerSesion, borrarToken, fetchConToken y cerrarSesion vienen de auth.js)
const sesion = obtenerSesion();
const accesoPermitido = sesion !== null && sesion.rol === "cliente";
if (!accesoPermitido) {
    borrarToken();
    location.replace("login.html");
}

const filtroEstado = document.getElementById("filtro-estado");
const filtroDesde = document.getElementById("filtro-desde");
const filtroHasta = document.getElementById("filtro-hasta");
const contador = document.getElementById("contador");
const tablaPesadas = document.getElementById("tabla-pesadas");

let tickets = [];        // el backend ya devuelve solo los del proveedor del cliente
let productosPorId = {};

function crearCelda(texto) {
    const td = document.createElement("td");
    td.textContent = texto;
    return td;
}

function crearCartel(facturado) {
    const cartel = document.createElement("span");
    cartel.className = facturado ? "cartel cartel-azul" : "cartel cartel-rojo";
    cartel.textContent = facturado ? "Facturado" : "No facturado";
    return cartel;
}

function mostrarFilaUnica(texto) {
    const fila = document.createElement("tr");
    const celda = crearCelda(texto);
    celda.colSpan = 6;
    celda.className = "centrado";
    fila.appendChild(celda);
    tablaPesadas.replaceChildren(fila);
}

function coincide(t) {
    if (filtroEstado.value === "si" && !t.facturado) return false;
    if (filtroEstado.value === "no" && t.facturado) return false;
    if (filtroDesde.value !== "" && t.fecha < filtroDesde.value) return false;
    if (filtroHasta.value !== "" && t.fecha > filtroHasta.value) return false;
    return true;
}

function renderizar() {
    if (filtroDesde.value !== "" && filtroHasta.value !== "" && filtroDesde.value > filtroHasta.value) {
        contador.textContent = "";
        mostrarFilaUnica("La fecha Desde es posterior a Hasta");
        return;
    }

    const visibles = tickets.filter(coincide);
    const netoCerrado = visibles
        .filter((t) => t.estado === "cerrado")
        .reduce((suma, t) => suma + t.peso_neto, 0);
    contador.textContent = `${visibles.length} ${visibles.length === 1 ? "pesada" : "pesadas"} · ` +
        `${netoCerrado.toLocaleString("es-AR")} kg netos (cerradas)`;

    if (visibles.length === 0) {
        mostrarFilaUnica(tickets.length === 0 ? "Todavía no hay pesadas registradas" : "Ninguna pesada coincide con los filtros");
        return;
    }

    tablaPesadas.replaceChildren(...visibles.map((t) => {
        const fila = document.createElement("tr");
        const facturacion = document.createElement("td");
        facturacion.appendChild(crearCartel(t.facturado));
        fila.append(
            crearCelda(t.id),
            crearCelda(t.fecha.split("-").reverse().join("/")),
            crearCelda(t.product_id === null ? "—" : (productosPorId[t.product_id] ?? t.product_id)),
            crearCelda(t.patente ?? "—"),
            crearCelda(t.peso_neto === null ? "—" : t.peso_neto.toLocaleString("es-AR")),
            facturacion,
        );
        return fila;
    }));
}

async function pedirJSON(url) {
    const respuesta = await fetchConToken(url);
    if (!respuesta.ok) throw new Error(`Error ${respuesta.status} en ${url}`);
    return respuesta.json();
}

async function cargarTodo() {
    try {
        const [listaTickets, proveedores, productos] = await Promise.all([
            pedirJSON(API_TICKETS), pedirJSON(API_PROVEEDORES), pedirJSON(API_PRODUCTOS),
        ]);
        tickets = listaTickets;
        productosPorId = Object.fromEntries(productos.map((p) => [p.id, p.name]));
        const mio = proveedores.find((p) => Number(p.id) === Number(sesion.supplier_id));
        document.getElementById("nombre-proveedor").textContent = mio ? mio.name : `Proveedor #${sesion.supplier_id}`;
        renderizar();
    } catch (error) {
        console.error("Error al cargar las pesadas:", error);
        mostrarFilaUnica("No se pudieron cargar las pesadas");
    }
}

for (const filtro of [filtroEstado, filtroDesde, filtroHasta]) {
    filtro.addEventListener("change", renderizar);
}
document.getElementById("btn-limpiar").addEventListener("click", () => {
    filtroEstado.value = "";
    filtroDesde.value = "";
    filtroHasta.value = "";
    renderizar();
});
document.getElementById("btn-logout").addEventListener("click", cerrarSesion);

if (accesoPermitido) cargarTodo();
