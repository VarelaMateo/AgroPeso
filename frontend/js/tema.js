// tema.js: tema claro / oscuro del panel admin, recordado en este navegador.
// Se carga al principio del <body> para aplicar el tema antes de dibujar (sin parpadeo blanco).
const CLAVE_TEMA = "agropeso_tema";

function leerTemaGuardado() {
    try { return localStorage.getItem(CLAVE_TEMA); } catch (_) { return null; }
}

document.body.classList.toggle("tema-oscuro", leerTemaGuardado() === "oscuro");

document.addEventListener("DOMContentLoaded", () => {
    const boton = document.getElementById("btn-tema");
    const pintarBoton = () => {
        const oscuro = document.body.classList.contains("tema-oscuro");
        boton.textContent = oscuro ? "☀️ Modo claro" : "🌙 Modo oscuro";
        boton.setAttribute("aria-pressed", String(oscuro));
    };
    pintarBoton();
    boton.addEventListener("click", () => {
        const oscuro = document.body.classList.toggle("tema-oscuro");
        try { localStorage.setItem(CLAVE_TEMA, oscuro ? "oscuro" : "claro"); } catch (_) { /* sin recordar */ }
        pintarBoton();
    });
});
