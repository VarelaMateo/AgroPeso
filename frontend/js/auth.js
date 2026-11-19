// auth.js: manejo de sesión (JWT) compartido por todas las pantallas.
// En login.html además maneja el envío del formulario.

const API_BASE = "http://127.0.0.1:8000";
const TOKEN_KEY = "access_token";
const PAGINAS_POR_ROL = {
    admin: "admin.html",
    cliente: "cliente.html"
}

// Token en localStorage

function guardarToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

function obtenerToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function borrarToken(){
    localStorage.removeItem(TOKEN_KEY);
}

function cerrarSesion(){
    borrarToken();
    window.location.href = "login.html";
}

// Lectura del payload del JWT

function decodificarPayLoad(token) {
    try{
        const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        const relleno = "=".repeat((4 - (base64.length % 4)) % 4);
        const binario = atob(base64 + relleno);
        const bytes = Uint8Array.from(binario, (c) => c.charCodeAt(0));

        return JSON.parse(new TextDecoder().decode(bytes));
    } catch(_){
        return null;
    }
}

function paginaSegunRol(rol){
    return PAGINAS_POR_ROL[rol] ?? null;
}

// Devuelve el payload del token si existe y no venció; si no, null
function obtenerSesion() {
    const token = obtenerToken();
    if (!token) return null;
    const payload = decodificarPayLoad(token);
    if (!payload || payload.exp * 1000 < Date.now()) return null;
    return payload;
}

// --- Helper de peticiones autenticadas ---
// Agrega el header Authorization. Si no hay token o la API responde 401
// (token inválido o vencido), borra la sesión y vuelve al login.

async function fetchConToken(url, opciones = {}) {
    const token = obtenerToken();
    if (!token) {
        cerrarSesion();
        throw new Error("No hay sesion iniciada");
    }

    const respuesta = await fetch(url, {
        ...opciones,
        headers: {
            ...(opciones.headers || {}),
            Authorization: `Bearer ${token}`,
        },
    });

    if (respuesta.status === 401){
        cerrarSesion();
        throw new Error("Sesion vencida o invalida");
    }

    return respuesta;
}

// --- Pantalla de login (solo si existe el formulario) ---


const formLogin = document.getElementById("form-login");

if (formLogin) {
    const mensaje = document.getElementById("mensaje");
    const boton = formLogin.querySelector("button[type='submit']");

    function mostrarError(text){
        mensaje.textContent = text;
        mensaje.style.display = "block";
    }

    const tokenExistente = obtenerToken();
    if (tokenExistente){
        const destino = paginaSegunRol(obtenerSesion()?.rol);
        if (destino){
            window.location.href = destino;
        } else {
            borrarToken()
        }
    }
    
    formLogin.addEventListener("submit", async (event) => {
        event.preventDefault();
        mensaje.style.display = "none";
        boton.disabled = true;

        // OAuth2PasswordRequestForm espera un formulario, no JSON
        const cuerpo = new URLSearchParams({
            username: formLogin.username.value.trim(),
            password: formLogin.password.value,
        });

        try {
            const respuesta = await fetch(`${API_BASE}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: cuerpo,
            });

            if (respuesta.status === 401) {
                mostrarError("Usuario o contraseña incorrectos");
                return;
            }
            if (!respuesta.ok) {
                mostrarError(`Error ${respuesta.status}: no se pudo iniciar sesión`);
                return;
            }

            const datos = await respuesta.json();
            const rol = decodificarPayLoad(datos.access_token)?.rol;
            const destino = paginaSegunRol(rol);

            if (!destino) {
                mostrarError("El usuario tiene un rol desconocido");
                return;
            }

            guardarToken(datos.access_token);
            window.location.href = destino;
        } catch (error) {
            console.error("Error al iniciar sesión:", error);
            mostrarError("No se pudo conectar con el servidor. ¿Está encendida la API?");
        } finally {
            boton.disabled = false;
        }
    });
}