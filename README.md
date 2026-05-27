# 🏛️ Historia Viva · Infantil y Primaria

Chatbot educativo con personajes históricos. Los alumnos eligen una época y una etapa educativa
y conversan con un personaje de esa época. Las respuestas se adaptan al nivel del alumnado
gracias a un motor de inteligencia artificial (Groq · Llama 3.3 70B) que recibe el contexto
histórico completo de la época elegida.

---

## Características

- 16 épocas históricas: desde el Paleolítico hasta la Democracia actual.
- 4 niveles educativos: Infantil (3-5), Básico (6-8), Intermedio (8-10), Avanzado (10-12).
- Base de conocimiento local enriquecida que se inyecta como contexto en cada respuesta.
- Responde a preguntas anacrónicas: "¿Tienes coche?" → el personaje responde en personaje.
- Cuestionario final autocorregible generado desde el historial del chat.
- Lectura en voz alta (TTS del navegador) con velocidad adaptada al nivel.
- Exportar la conversación como texto.
- Panel docente con estadísticas de la sesión (preguntas por época, resultados de tests).
- Alineación curricular con Castilla y León.
- Sin datos de alumnos almacenados de forma persistente.

---

## Estructura del proyecto

```
historia-viva/
├── app.py                  ← App principal (Streamlit)
├── requirements.txt        ← Dependencias Python
├── .gitignore
├── .streamlit/
│   └── config.toml         ← Tema visual
├── data/
│   ├── index.js            ← Índice de épocas
│   ├── paleolitico.js
│   └── ... (16 archivos)
├── images/
│   ├── paleolitico.jpg
│   └── ... (16 imágenes, 800×300 px aprox.)
└── README.md
```

---

## Despliegue paso a paso

### Paso 1 — Cuenta en GitHub

Ve a github.com, crea una cuenta gratuita o inicia sesión.

### Paso 2 — Crear el repositorio

1. Clic en "New repository".
2. Nombre: `historia-viva` (o el que quieras).
3. Márcalo como Public.
4. Clic en "Create repository".

### Paso 3 — Subir los archivos

Desde el navegador (sin instalar nada):

1. En la página del repositorio, clic en "uploading an existing file".
2. Arrastra todos los archivos y carpetas de este proyecto.
3. Clic en "Commit changes".

### Paso 4 — API key de Groq (gratuita, sin tarjeta de crédito)

1. Ve a [console.groq.com](https://console.groq.com) y crea una cuenta (puedes
   usar tu cuenta de Google o GitHub).
2. En el menú lateral entra en "API Keys" → "Create API Key".
3. Ponle un nombre (por ejemplo `historia-viva`) y cópiala.
   **IMPORTANTE**: guárdala bien, solo se muestra una vez.
   La clave tiene este formato: `gsk_...`

### Paso 5 — Desplegar en Streamlit

1. Ve a [share.streamlit.io](https://share.streamlit.io) (puedes entrar con tu cuenta de GitHub).
2. Clic en "New app".
3. Elige tu repositorio `historia-viva` y la rama `main`.
4. Main file path: `app.py`
5. Clic en "Advanced settings" → "Secrets" y pega exactamente esto, sustituyendo
   los valores entre comillas por los tuyos:

   ```toml
   GROQ_API_KEY = "gsk_AQUI_VA_TU_CLAVE_DE_GROQ"
   TEACHER_PASSWORD = "elige_tu_contraseña_de_docente"
   ```

   La línea `TEACHER_PASSWORD` es opcional pero **muy recomendable**: protege el
   acceso al panel docente con una contraseña que solo tú conozcas. Si no la
   configuras, se usa una contraseña por defecto que no es segura para un aula.

6. Clic en "Deploy!".

En unos minutos tendrás una URL pública tipo:
`https://historia-viva.streamlit.app`

---

## Prueba local (opcional)

```bash
pip install -r requirements.txt
mkdir -p .streamlit
cat > .streamlit/secrets.toml <<'EOF'
GROQ_API_KEY = "gsk_TUCLAVE"
TEACHER_PASSWORD = "tu_contraseña"
EOF
streamlit run app.py
```

---

## Coste estimado

Groq ofrece **1.000 peticiones diarias gratuitas** con el modelo Llama 3.3 70B
y **no requiere tarjeta de crédito**. Hay además un límite de 30 peticiones por
minuto, suficiente para una clase activa.

| Uso                          | Llamadas IA aprox. | Coste     |
|------------------------------|--------------------|-----------|
| 1 sesión (25 alumnos)        | ~75                | 0,00 EUR  |
| 1 mes escolar (20 sesiones)  | ~1.500             | 0,00 EUR* |
| Curso completo (8 meses)     | ~12.000            | 0,00 EUR* |

*Mientras te mantengas dentro del límite diario de 1.000 llamadas. La app
muestra el contador en el panel docente y, por seguridad, deja de llamar a la
API a partir de 950 llamadas. El límite se reinicia a medianoche UTC (01-02h
hora de España).

Si necesitas más cuota, Groq tiene un plan de pago bajo demanda. Consulta tu
uso en: [console.groq.com/usage](https://console.groq.com/usage)

---

## Preguntas frecuentes

**¿Se guardan los datos de los alumnos?**
No de forma persistente. Las preguntas que hacen los alumnos y los resultados
de los cuestionarios se guardan en memoria (RAM) mientras el servidor de
Streamlit está activo, para que el panel docente pueda mostrar el agregado de
la clase. Se borran automáticamente cuando la app se duerme o se redespliega.
No se almacenan nombres, no se asocian a alumnos concretos, no se envían a
ningún servicio externo aparte de la propia llamada a Groq para generar la
respuesta.

**¿Cómo añado una época nueva?**
Crea `data/nueva_epoca.js` con la misma estructura que los archivos existentes
y añade su entrada en `data/index.js`. Añade también una imagen en
`images/nueva_epoca.jpg` (800×300 px aproximadamente) y un emoji/color para
esa época en la constante `ERA_META` de `app.py`.

**¿Cómo cambio la contraseña del panel docente?**
En Streamlit Cloud, "Manage app" → "Settings" → "Secrets" y edita la línea
`TEACHER_PASSWORD`. Streamlit redespliega solo en segundos.

**¿Cualquier cambio en GitHub se ve enseguida?**
Sí. Streamlit detecta los cambios en el repo y redespliega automáticamente en
unos segundos. No hace falta tocar nada en Streamlit.
