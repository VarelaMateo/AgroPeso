// exportar.js: filtros combinables y exportación a CSV (Excel), compartido por admin y cliente.

const COLUMNAS_CSV = [
    "N° Ticket", "Fecha y Hora", "Estado", "Proveedor", "Producto",
    "Patente", "Chofer", "Peso Tara (kg)", "Peso Bruto (kg)", "Peso Neto (kg)",
];

// ---------- Filtros ----------

// true si "desde" es posterior a "hasta" (las fechas vienen como "YYYY-MM-DD", se comparan como texto)
function rangoInvalido(desde, hasta) {
    return desde !== "" && hasta !== "" && desde > hasta;
}

// Todos los filtros se combinan con AND. Un filtro vacío ("") no filtra.
// textosExtra: otros textos donde buscar además de patente y chofer (ej: nombre del proveedor)
function coincideConFiltros(t, { texto = "", supplierId = "", productId = "", desde = "", hasta = "" }, textosExtra = []) {
    if (supplierId !== "" && String(t.supplier_id) !== supplierId) return false;
    if (productId !== "" && String(t.product_id) !== productId) return false;
    if (desde !== "" && t.fecha < desde) return false;
    if (hasta !== "" && t.fecha > hasta) return false;
    if (texto !== "") {
        const campos = [t.patente, t.chofer, ...textosExtra].map((c) => (c ?? "").toLowerCase());
        if (!campos.some((c) => c.includes(texto))) return false;
    }
    return true;
}

// ---------- CSV ----------

// Una celda de texto: siempre entre comillas, con las comillas internas duplicadas.
// Si empieza con = + @ (o tab/retorno) o con "-" seguido de algo, Excel la interpretaría como
// fórmula: se antepone un apóstrofo. Un "-" solo (campo vacío) se deja como está.
function celdaTexto(valor) {
    let texto = String(valor ?? "");
    if (/^(?:[=+@\t\r]|-.)/s.test(texto)) texto = "'" + texto;
    return `"${texto.replace(/"/g, '""')}"`;
}

// Números sin separador de miles para que Excel los tome como números; "-" si no hay valor
function celdaNumero(valor) {
    return valor === null || valor === undefined ? "-" : String(valor);
}

// nombreProveedor(t) y nombreProducto(t) devuelven el texto a mostrar para cada ticket
// (los tickets sin producto salen como "-", igual que los pesos vacíos)
function generarCSV(tickets, nombreProveedor, nombreProducto) {
    const filas = [COLUMNAS_CSV.map(celdaTexto).join(";")];

    for (const t of tickets) {
        filas.push([
            celdaNumero(t.id),
            celdaTexto(t.fecha.split("-").reverse().join("/")),
            celdaTexto(t.estado === "cerrado" ? "Cerrado" : "Abierto"),
            celdaTexto(nombreProveedor(t)),
            celdaTexto(t.product_id === null ? "-" : nombreProducto(t)),
            celdaTexto(t.patente ?? "-"),
            celdaTexto(t.chofer),
            celdaNumero(t.peso_tara),
            celdaNumero(t.peso_bruto),
            celdaNumero(t.peso_neto),
        ].join(";"));
    }

    // Fila vacía de separación y fila de totales
    const cerrados = tickets.filter((t) => t.estado === "cerrado");
    const suma = (lista, campo) => lista.reduce((total, t) => total + (t[campo] ?? 0), 0);
    filas.push("");
    filas.push([
        celdaTexto("TOTALES"),
        celdaTexto(""),
        celdaTexto(`${cerrados.length} cerradas de ${tickets.length}`),
        celdaTexto(""), celdaTexto(""), celdaTexto(""), celdaTexto(""),
        celdaNumero(suma(tickets, "peso_tara")),
        celdaNumero(suma(cerrados, "peso_bruto")),
        celdaNumero(suma(cerrados, "peso_neto")),
    ].join(";"));

    // BOM para que Excel lea el archivo como UTF-8 (tildes y ñ) y CRLF como fin de línea
    return "﻿" + filas.join("\r\n") + "\r\n";
}

// ---------- Archivo ----------

// Quita caracteres que Windows no acepta en nombres de archivo y cambia espacios por "_"
function textoParaArchivo(texto) {
    return String(texto).trim().replace(/[\\/:*?"<>|]/g, "").replace(/\s+/g, "_");
}

// Ej: ["AgroPeso", "Berg"] + 2026-11-01 / 2026-11-20 -> AgroPeso_Berg_2026-11-01_a_2026-11-20.csv
function nombreDeArchivo(partes, desde, hasta, hoy) {
    let fechas;
    if (desde && hasta) fechas = `${desde}_a_${hasta}`;
    else if (desde) fechas = `desde_${desde}`;
    else if (hasta) fechas = `hasta_${hasta}`;
    else fechas = hoy;
    return [...partes.map(textoParaArchivo), fechas].join("_") + ".csv";
}

function descargarCSV(nombreArchivo, contenido) {
    const blob = new Blob([contenido], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = nombreArchivo;
    document.body.appendChild(enlace);
    enlace.click();
    enlace.remove();
    URL.revokeObjectURL(url);
}

// Muestra un aviso breve al lado de los filtros (sin alert ni innerHTML)
function mostrarAvisoInline(elemento, texto) {
    elemento.textContent = texto;
    elemento.style.display = "inline";
    clearTimeout(elemento._temporizador);
    elemento._temporizador = setTimeout(() => { elemento.style.display = "none"; }, 4000);
}

// Opciones de un <select> de filtro: "Todos los ..." + una por elemento
function opcionesDeFiltro(textoTodos, pares) {
    const todos = document.createElement("option");
    todos.value = "";
    todos.textContent = textoTodos;
    const opciones = [todos];
    for (const [id, nombre] of pares) {
        const opcion = document.createElement("option");
        opcion.value = String(id);
        opcion.textContent = nombre;
        opciones.push(opcion);
    }
    return opciones;
}

// Reemplaza las opciones de un select conservando lo que estaba elegido (si sigue existiendo)
function actualizarSelectFiltro(select, textoTodos, porId) {
    const elegido = select.value;
    const pares = Object.entries(porId).sort((a, b) => a[1].localeCompare(b[1]));
    select.replaceChildren(...opcionesDeFiltro(textoTodos, pares));
    if (elegido in porId) select.value = elegido;
}
