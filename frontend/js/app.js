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

    const datos = {
        chofer: form.chofer.value.trim(),
        patente: form.patente.value.trim() || null,
        peso_tara: Number(form.peso_tara.value),
        peso_bruto: Number(form.peso_bruto.value),
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
                `Pesada registrada. ID: ${cuerpo.id} - Peso neto: ${cuerpo.peso_neto} kg`,
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
                crearCelda(t.supplier_id),
                crearCelda(formatoPeso(t.peso_tara)),
                crearCelda(formatoPeso(t.peso_bruto)),
                crearCelda(formatoPeso(t.peso_neto)),
                crearCeldaEstado(t.estado)
            );
            return fila;
        });

        tablaHistorial.replaceChildren(...filas);
    } catch (error) {
        console.error("Error al cargar el historial:", error);
        mostrarFilaUnica("No se pudo cargar el historial. ¿Está encendida la API?");
    }
}

cargarHistorial();

