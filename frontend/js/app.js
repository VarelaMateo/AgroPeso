const API_URL = "http://127.0.0.1:8000/tickets/";

const form = document.getElementById("form-pesaje");
const mensaje = document.getElementById("mensaje");
const boton = form.querySelector("button[type='submit']");

function mostrarMensaje(texto, tipo) {
    mensaje.textContent = texto;
    const color = tipo === "ok" ? "w3-pale-green w3-border-green" : "w3-pale-red w3-border-red";
    mensaje.className = `w3-panel w3-leftbar ${color}`;
    mensaje.style.display = "block";
}

// El "detail" de la API es un texto (errores 400/404) o una lista (errores 422)
function textoDeError (detail){
    if (typeof detail === "string") 
        return detail;
    if (Array.isArray(detail)) {
        return detail.map((e) => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(" | ");
    }
    return "Error Desconocido";
}

form.addEventListener("submit", async (event) => {
    event.preventDefault() //Evita que el navegador recargue la pagina
    
    const brutoTexto = document.getElementById("peso_bruto").value.trim();

    const datos = {
        chofer: form.chofer.value.trim(),
        patente: form.patente.value.trim() || null,
        peso_tara: Number(form.peso_tara.value),    
        peso_bruto: brutoTexto === "" ? null : Number(brutoTexto),
        supplier_id: Number(form.supplier_id.value),
    }

    boton.disabled = true;

    try {
        const respuesta = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos),
        });

        let cuerpo = null;
        try {
        cuerpo = await respuesta.json();
        } catch (_) {
        // la respuesta no era JSON (por ejemplo, un error 500)
        }

        if (respuesta.ok) {
            mostrarMensaje(
                `Pesada registrada. ID: ${cuerpo.id}`,
                "ok"
            );

            form.reset();
            cargarHistorial();
        } else if (cuerpo && cuerpo.detail) {
            mostrarMensaje(textoDeError(cuerpo.detail), "error");
        } else {
            mostrarMensaje(`Error ${respuesta.status}: no se pudo registrar la pesada`, "error");
        }
    } catch (error) {
        mostrarMensaje("No se pudo conectar con el servidor. ¿Está encendida la API?", "error");
    } finally {
        boton.disabled = false;
    }

});

const tablaHistorial = document.getElementById("tabla-historial");

function crearCelda(texto) {
    const td = document.createElement("td");
    td.textContent = texto;
    return td;
}

function crearCeldaEstado(estado) {
    const td = document.createElement("td");
    const etiqueta = document.createElement("span");

    etiqueta.className = estado === "abierto" ? "w3-tag w3-orange" : "w3-tag w3-green";
    etiqueta.textContent = estado;
    td.appendChild(etiqueta);

    return td;
}

async function cerrarTicket(id) {
    const entrada = prompt("Ingrese el peso bruto");

    if (entrada === null) return;

    const pesoBruto = Number(entrada);
    if(entrada.trim() === "" || !Number.isInteger(pesoBruto) || pesoBruto <= 0){
        alert("El peso bruto debe ser un numero entero mayor a 0");
        return;
    }

    try {
        const respuesta = await fetch(`${API_URL}${id}/cerrar`, {
            method: "PATCH",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({peso_bruto: pesoBruto})
        });

        if (!respuesta.ok) {
            const error = await respuesta.json().catch(() => ({}));
            const detalle = typeof error.detail === "string" ? error.detail: `Error ${respuesta.status}`;
            alert (`No se pudo cerrar el ticket: ${detalle}`);

            return;
        }

        await cargarHistorial();
    } catch (error) {
        console.error("Error al cerrar el ticket: ", error);
        alert("No se pudo conectar con el servidor.");
    }
}

function crearCeldaAcciones(ticket) {
    const celda = document.createElement("td");

    if (ticket.estado === "abierto") {
        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = "w3-tag w3-round w3-blue";   // mismo w3-tag que la etiqueta, bordes redondeados, azul
        boton.style.border = "none";                   // los <button> traen borde propio
        boton.style.cursor = "pointer";                // para que se note que es clickeable
        boton.style.font = "inherit";                  // mismo tamaño de letra que la etiqueta
        boton.textContent = "Cerrar";
        boton.addEventListener("click", () => cerrarTicket(ticket.id));
        celda.appendChild(boton);
    }

    return celda;
}

function formatoFecha(fecha) {
    return fecha.split("-").reverse().join("/") // 2026-11-07 -> 07/11/2026
}

function formatoPeso(valor) {
    return valor === null ? "-": valor.toLocaleString("es-AR");
}

function mostrarFilaUnica(text) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");

    celda.colSpan = 9;
    celda.className = "w3-center";
    celda.textContent = text;

    fila.appendChild(celda);
    tablaHistorial.replaceChildren(fila);
}

async function cargarHistorial(){
    try{
        const respuesta = await fetch(API_URL);
        if (!respuesta.ok){
            throw new Error(`Error ${respuesta.status}`);
        }
        const tickets = await respuesta.json()

        if (tickets.length === 0) {
            mostrarFilaUnica("Todavia no hay pesadas registradas");
            return;
        }

        const filas = tickets.map((t) => {
            const fila = document.createElement('tr');
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
                fila.appendChild(crearCeldaAcciones(t))
            );
            return fila;
        });

        tablaHistorial.replaceChildren
        (...filas);
    } catch (error) {
        console.error("Error al cargar el historial:", error);
        mostrarFilaUnica("No se pudo cargar el historial. ¿Está encendida la API?");
    }
}


const API_PROVEEDORES = "http://127.0.0.1:8000/suppliers/";
const selectProveedores = document.getElementById("supplier_id");

function crearOpcion(valor, texto, esPlaceholder = false) {
    const opcion = document.createElement("option");
    opcion.value = valor;
    opcion.textContent = texto;
    if (esPlaceholder) {
        opcion.disable = true;
        opcion.defaultSelected = true; //para que form.reset() vuelve a esta opcion 
    }
    return opcion;

}

let proveedoresPorId = {};

async function cargarProveedores() {
    try {
        const respuesta = await fetch(API_PROVEEDORES);
        if (!respuesta.ok){
            throw new Error (`Error ${respuesta.status}`);
        }
        const proveedores = await respuesta.json();
        proveedoresPorId = Object.fromEntries(proveedores.map((p) => [p.id, p.name]));
        const textoInicial = proveedores.length === 0 ? "No hay proveedores cargados" : "Elegi un proveedor";
        const opciones = [crearOpcion("", textoInicial, true)];
        for (const proveedor of proveedores){
            opciones.push(crearOpcion(proveedor.id, proveedor.name));
        }
        selectProveedores.replaceChildren(...opciones);
    } catch (error){
        console.error("Error al cargar los proveedores:", error);
        selectProveedores.replaceChildren(crearOpcion("", "No se pudieron cargar los proveedores", true))
    }
}


async function iniciar() {
    await cargarProveedores();
    await cargarHistorial();
}
iniciar();

