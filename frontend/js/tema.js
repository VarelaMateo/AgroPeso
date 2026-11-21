// tema.js: tema claro / oscuro, recordado en este navegador (lo usan admin.html y cliente.html).
// Se carga al principio del <body> para aplicar el tema antes de dibujar (sin parpadeo blanco).
// La clase oscura sale de <body data-clase-oscura="...">; por defecto, "tema-oscuro".
const CLAVE_TEMA = "agropeso_tema";
const CLASE_OSCURA = document.body.dataset.claseOscura || "tema-oscuro";

function leerTemaGuardado() {
    try { return localStorage.getItem(CLAVE_TEMA); } catch (_) { return null; }
}

document.body.classList.toggle(CLASE_OSCURA, leerTemaGuardado() === "oscuro");

document.addEventListener("DOMContentLoaded", () => {
    const boton = document.getElementById("btn-tema");
    const pintarBoton = () => {
        const oscuro = document.body.classList.contains(CLASE_OSCURA);
        boton.textContent = oscuro ? "☀️ Modo claro" : "🌙 Modo oscuro";
        boton.setAttribute("aria-pressed", String(oscuro));
    };
    pintarBoton();
    boton.addEventListener("click", () => {
        const oscuro = document.body.classList.toggle(CLASE_OSCURA);
        try { localStorage.setItem(CLAVE_TEMA, oscuro ? "oscuro" : "claro"); } catch (_) { /* sin recordar */ }
        pintarBoton();
    });
});
