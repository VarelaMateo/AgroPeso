const API = "http://127.0.0.1:8000";
const API_TICKETS = `${API}/tickets/`;
const API_PROVEEDORES = `${API}/suppliers/`;
const API_PRODUCTOS = `${API}/products/`;
const PAGINA_LOGIN = "login.html";

// Guardia de rol. obtenerSesion, borrarToken y fetchConToken vienen de auth.js
const sesion = obtenerSesion();
const accesoPermitido = sesion !== null && sesion.rol === "admin";

if (!accesoPermitido) {
    borrarToken();
    location.replace(PAGINA_LOGIN);
}

// Elementos y estado

const form = document.getElementById("form-pesaje");
const mensaje = document.getElementById("mensaje");
const botonSubmit = form.querySelector("button[type='submit']");
const tablaHistorial = document.getElementById("tabla-historial");
const tituloTabla = document.getElementById("titulo-tabla");
const buscador = document.getElementById("buscador");
const selectProveedores = document.getElementById("supplier_id");
const selectProductos = document.getElementById("product_id");
const statTicketsMes = document.getElementById("stat-tickets-mes");
const listaTopProveedores = document.getElementById("lista-top-proveedores");

let todosLosTickets = [];
let proveedoresPorId = {};


// Utilidades 

function mostrarMensaje(texto, tipo) {
    mensaje.textContent = texto;
    const color = tipo === "ok" ? "w3-pale-green w3-border-green" : "w3-pale-red w3-border-red";
    mensaje.className = `w3-panel w3-leftbar ${color}`;
    mensaje.style.display = "block";
}

function textoDeError(detail){
    if (typeof detail === "string") return detail;
    if(Array.isArray(detail)) {
        return detail.map((e) => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(" | ");
    }
    return "Error desconocido";
}

// Fecha local en formato YYYY-MM-DD
function fechaDeHoy() {
    const d = new Date();
    const mes = String(d.getMonth() + 1).padStart(2, "0");
    const dia = String(d.getDate()).padStart(2, "0");

    return `${d.getFullYear()}-${mes}-${dia}`;
}

function formatoFecha(fecha){
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
    const etiqueta = document.createElement("span")
    etiqueta.className = estado === "abierto" ? "w3-tag w3-orange" : "w3-tag w3-green";
    etiqueta.textContent = estado;
    td.appendChild(etiqueta);

    return td;
}

function crearCeldaAcciones(ticket) {
    const celda = document.createElement("td");
    if (ticket.estado === "abierto") {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "w3-button w3-small w3-round-xxlarge w3-green";
        btn.textContent = "Cerrar";
        btn.addEventListener("click", () => cerrarTicket(ticket.id));
        celda.appendChild(btn);
    }

    return celda;
}

function mostrarFilaUnica(texto) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = 10;
    celda.className = "w3-center";
    celda.textContent = texto;
    fila.appendChild(celda);
    tablaHistorial.replaceChildren(fila);
}

// ---------- Modal (reemplaza prompt y alert) ----------

const modal = document.getElementById("modal");
const modalTitulo = document.getElementById("modal-titulo");
const modalTexto = document.getElementById("modal-texto");
const modalCampo = document.getElementById("modal-campo");
const modalInput = document.getElementById("modal-input");
const modalError = document.getElementById("modal-error");
const modalForm = document.getElementById("modal-form");
const modalCancelar = document.getElementById("modal-cancelar");
const modalAceptar = document.getElementById("modal-aceptar");

let resolverModal = null;
let validacionModal = null;

function cerrarModal(valor) {
    modal.style.display = "none";
    const resolver = resolverModal;
    resolverModal = null;
    validacionModal = null;
    if (resolver) resolver(valor);
}

function abrirModal({ titulo, texto = "", conCampo = false, tipo = "text", placeholder = "",
                      validar = null, textoAceptar = "Aceptar", conCancelar = true }) {
    modalTitulo.textContent = titulo;
    modalTexto.textContent = texto;
    modalCampo.style.display = conCampo ? "block" : "none";
    modalInput.type = tipo;
    modalInput.placeholder = placeholder;
    modalInput.value = "";
    modalError.style.display = "none";
    modalAceptar.textContent = textoAceptar;
    modalCancelar.style.display = conCancelar ? "inline-block" : "none";
    validacionModal = validar;
    modal.style.display = "block";
    setTimeout(() => (conCampo ? modalInput : modalAceptar).focus(), 50);

    return new Promise((resolver) => { resolverModal = resolver; });
}

// Devuelve el texto ingresado, o null si se cancela
function pedirDato(opciones) {
    return abrirModal({ ...opciones, conCampo: true });
}

// Muestra un mensaje con un solo botón
function avisar(texto, titulo = "Aviso") {
    return abrirModal({ titulo, texto, conCancelar: false });
}

function validarEnteroPositivo(valor) {
    return /^\d+$/.test(valor) && Number(valor) > 0 ? null : "Ingresá un número entero mayor a 0";
}

modalForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const valor = modalInput.value.trim();
    if (validacionModal) {
        const error = validacionModal(valor);
        if (error) {
            modalError.textContent = error;
            modalError.style.display = "block";
            return;
        }
    }
    cerrarModal(valor);
});

modalCancelar.addEventListener("click", () => cerrarModal(null));
modal.addEventListener("click", (event) => {
    if (event.target === modal) cerrarModal(null); // clic en el fondo oscuro
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modal.style.display === "block") cerrarModal(null);
});


// Tabla (filtra en el navegador)

function renderizarTabla() {
    const consulta = buscador.value.trim().toLowerCase();
    let tickets;

    if (consulta === "") {
        tituloTabla.textContent = "Lista de tickets abiertos de hoy";
        const hoy = fechaDeHoy();
        tickets = todosLosTickets.filter((t) => t.estado === "abierto" && t.fecha === hoy);
    } else {
        // Con busqueda se miran todos los tickets, abiertos y cerrados
        tituloTabla.textContent = "Resultado de la busqueda";
        tickets = todosLosTickets.filter((t) => {
            const proveedor = (proveedoresPorId[t.supplier_id] ?? "").toLowerCase()
            const patente = (t.patente ?? "").toLowerCase();
            return proveedor.includes(consulta) || patente.includes(consulta);
        });
    }

    if (tickets.length === 0) {
        mostrarFilaUnica(consulta === ""
            ? "No hay tickets abiertos hoy" : "Ningun ticket coincide con la busqueda");
        return;
    }

    const filas = tickets.map((t) => {
        const fila = document.createElement("tr");
        fila.append(
            crearCelda(t.id),
            crearCelda(formatoFecha(t.fecha)),
            crearCelda(t.chofer),
            crearCelda(t.patente ?? "—"),
            crearCelda(proveedoresPorId[t.supplier_id] ?? t.supplier_id),
            crearCelda(formatoPeso(t.peso_tara)),
            crearCelda(formatoPeso(t.peso_bruto)),
            crearCelda(formatoPeso(t.peso_neto)),
            crearCeldaEstado(t.estado),
            crearCeldaAcciones(t)
        );
        return fila;
    });
    tablaHistorial.replaceChildren(...filas);
}

// Estadísticas del mes (se calculan con la misma lista que ya trae la API)
function renderizarEstadisticas() {
    const mes = fechaDeHoy().slice(0, 7); // "YYYY-MM"
    const delMes = todosLosTickets.filter((t) => t.fecha.slice(0, 7) === mes);

    statTicketsMes.textContent = `${delMes.length} ${delMes.length === 1 ? "ticket" : "tickets"}`;

    const conteo = {};
    for (const t of delMes) conteo[t.supplier_id] = (conteo[t.supplier_id] ?? 0) + 1;

    const top = Object.entries(conteo)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3);

    if (top.length === 0) {
        const vacio = document.createElement("p");
        vacio.className = "w3-text-grey w3-small";
        vacio.textContent = "Sin tickets este mes";
        listaTopProveedores.replaceChildren(vacio);
        return;
    }

    const filas = top.map(([supplierId, cantidad]) => {
        const fila = document.createElement("div");
        fila.className = "w3-row w3-margin-bottom";

        const nombre = document.createElement("span");
        nombre.className = "w3-col s9 w3-text-grey";
        nombre.textContent = proveedoresPorId[supplierId] ?? `Proveedor ${supplierId}`;

        const total = document.createElement("span");
        total.className = "w3-col s3 w3-right-align";
        total.textContent = cantidad;

        fila.append(nombre, total);
        return fila;
    });
    listaTopProveedores.replaceChildren(...filas);
}

async function cargarTickets() {
    try {
        const respuesta = await fetchConToken(API_TICKETS);
        if (!respuesta.ok) throw new Error(`Error ${respuesta.status}`);
        todosLosTickets = await  respuesta.json();
        renderizarEstadisticas();
        renderizarTabla();
    } catch(error) {
        console.error("Error al cargar los tickets: ", error);
        mostrarFilaUnica("No se pudo cargar la lista");
    }
}

buscador.addEventListener("input", renderizarTabla);

// Proveedores

function crearOpcion(valor, texto, esPlaceholder = false) {
    const opcion = document.createElement("option");
    opcion.value = valor;
    opcion.textContent = texto;
    if (esPlaceholder) {
        opcion.disabled = true;
        opcion.defaultSelected = true; //form.reset() vuelve a esta opcn
    }

    return opcion;
}

async function cargarProveedores() {
    try{
        const respuesta = await fetchConToken(API_PROVEEDORES);
        if (!respuesta.ok) throw new Error (`Error ${respuesta.status}`);
        const proveedores = await respuesta.json();

        proveedoresPorId = Object.fromEntries(proveedores.map((p) => [p.id, p.name]));
        const textoInicial = proveedores.length === 0 ? "No hay proveedores cargados" : "Elegí un proveedor";
        const opciones = [crearOpcion("", textoInicial, true)];
        for (const p of proveedores) opciones.push(crearOpcion(p.id, p.name));
        selectProveedores.replaceChildren(...opciones);
    } catch (error) {
        console.error("Error al cargar los proveedores: ", error);
        selectProveedores.replaceChildren(crearOpcion("", "No se pudieron cargar los proveedores", true));
    }
}

async function agregarProveedores() {
     const nombre = await pedirDato({
        titulo: "Agregar proveedor",
        texto: "Nombre del nuevo proveedor",
        placeholder: "Ej: Berg",
        textoAceptar: "Guardar",
        validar: (v) => {
            if (v === "") return "El nombre es obligatorio";
            if (v.length > 200) return "Máximo 200 caracteres";
            return null;
        },
    });
    if (nombre === null) return;

    try {
        const respuesta = await fetchConToken(API_PROVEEDORES, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: nombre }),
        });
        if (!respuesta.ok) {
            const error = await respuesta.json().catch(() => ({}));
            await avisar(`No se pudo crear el proveedor: ${error.detail ? textoDeError(error.detail) : respuesta.status}`, "Error");
            return;
        }
        await cargarProveedores();
        renderizarTabla();
        mostrarMensaje(`Proveedor "${nombre}" creado`, "ok");
    } catch (error) {
        console.error("Error al crear el proveedor:", error);
        await avisar("No se pudo conectar con el servidor.", "Error");
    }
}

// Productos

async function cargarProductos() {
    try {
        const respuesta = await fetchConToken(API_PRODUCTOS);
        if (!respuesta.ok) throw new Error(`Error ${respuesta.status}`);
        const productos = await respuesta.json();

        // El producto es opcional: la primera opción se puede elegir y envía null
        const sinProducto = crearOpcion("", productos.length === 0 ? "No hay productos cargados" : "Sin producto");
        sinProducto.defaultSelected = true; // form.reset() vuelve a esta opción
        const opciones = [sinProducto];
        for (const p of productos) opciones.push(crearOpcion(p.id, p.name));
        selectProductos.replaceChildren(...opciones);
    } catch (error) {
        console.error("Error al cargar los productos: ", error);
        selectProductos.replaceChildren(crearOpcion("", "No se pudieron cargar los productos", true));
    }
}

async function agregarProducto() {
    const nombre = await pedirDato({
        titulo: "Agregar producto",
        texto: "Nombre del nuevo producto",
        placeholder: "Ej: Soja",
        textoAceptar: "Guardar",
        validar: (v) => {
            if (v === "") return "El nombre es obligatorio";
            if (v.length > 200) return "Máximo 200 caracteres";
            return null;
        },
    });
    if (nombre === null) return;

    try {
        const respuesta = await fetchConToken(API_PRODUCTOS, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: nombre }),
        });
        if (!respuesta.ok) {
            const error = await respuesta.json().catch(() => ({}));
            await avisar(`No se pudo crear el producto: ${error.detail ? textoDeError(error.detail) : respuesta.status}`, "Error");
            return;
        }
        await cargarProductos();
        mostrarMensaje(`Producto "${nombre}" creado`, "ok");
    } catch (error) {
        console.error("Error al crear el producto:", error);
        await avisar("No se pudo conectar con el servidor.", "Error");
    }
}

// Cerrar ticket

async function cerrarTicket(id) {
     const entrada = await pedirDato({
        titulo: `Cerrar ticket ${id}`,
        texto: "Ingresá el peso bruto (kg)",
        tipo: "number",
        placeholder: "Ej: 48260",
        textoAceptar: "Cerrar ticket",
        validar: validarEnteroPositivo,
    });
    if (entrada === null) return;

    try {
        const respuesta = await fetchConToken(`${API_TICKETS}${id}/cerrar`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ peso_bruto: Number(entrada) }),
        });
        if (!respuesta.ok) {
            const error = await respuesta.json().catch(() => ({}));
            await avisar(`No se pudo cerrar el ticket: ${error.detail ? textoDeError(error.detail) : respuesta.status}`, "Error");
            return;
        }
        await cargarTickets();
    } catch (error) {
        console.error("Error al cerrar el ticket:", error);
        await avisar("No se pudo conectar con el servidor.", "Error");
    }
}
// Botón central: pide el ID del ticket y reutiliza cerrarTicket
async function cerrarTicketPorId() {
    const entrada = await pedirDato({
        titulo: "Cerrar ticket",
        texto: "ID del ticket a cerrar",
        tipo: "number",
        placeholder: "Ej: 12",
        textoAceptar: "Continuar",
        validar: validarEnteroPositivo,
    });
    if (entrada === null) return;
    cerrarTicket(Number(entrada));
}

// ---------- Formulario Nuevo ticket ----------

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const brutoTexto = form.peso_bruto.value.trim();
    const datos = {
        chofer: form.chofer.value.trim(),
        patente: form.patente.value.trim() || null,
        peso_tara: Number(form.peso_tara.value),
        peso_bruto: brutoTexto === "" ? null : Number(brutoTexto),
        supplier_id: Number(form.supplier_id.value),
        product_id: form.product_id.value === "" ? null : Number(form.product_id.value),
    };

    botonSubmit.disabled = true;
    try {
        const respuesta = await fetchConToken(API_TICKETS, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos),
        });

        let cuerpo = null;
        try { cuerpo = await respuesta.json(); } catch (_) { /* no era JSON */ }

        if (respuesta.ok) {
            mostrarMensaje(`Pesada registrada. ID: ${cuerpo.id}`, "ok");
            form.reset();
            await cargarTickets();
        } else if (cuerpo && cuerpo.detail) {
            mostrarMensaje(textoDeError(cuerpo.detail), "error");
        } else {
            mostrarMensaje(`Error ${respuesta.status}: no se pudo registrar la pesada`, "error");
        }
    } catch (error) {
        if (error.message !== "Sesion vencida o invalida") {
            mostrarMensaje("No se pudo conectar con el servidor. ¿Está encendida la API?", "error");
        }
    } finally {
        botonSubmit.disabled = false;
    }
});

// ---------- Botones y arranque ----------

document.getElementById("btn-logout").addEventListener("click", cerrarSesion);
document.getElementById("btn-cerrar").addEventListener("click", cerrarTicketPorId);
document.getElementById("btn-proveedor").addEventListener("click", agregarProveedores);
document.getElementById("btn-producto").addEventListener("click", agregarProducto);

async function iniciar() {
    document.getElementById("nombre-usuario").textContent = sesion.username;
    await Promise.all([cargarProveedores(), cargarProductos()]);
    await cargarTickets();
}


if (accesoPermitido) iniciar();