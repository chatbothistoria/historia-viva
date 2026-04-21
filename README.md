# 🏛️ Historia Viva · Infantil y Primaria

Chatbot educativo con personajes históricos. Los alumnos eligen una época y una etapa educativa
y conversan con un personaje de esa época. La app responde cualquier pregunta gracias a una
base de conocimiento local + inteligencia artificial (Claude) como respaldo.

---

## Características

- 16 épocas históricas: desde el Paleolítico hasta la Democracia actual
- 4 niveles educativos: Infantil (3-5), Básico (6-8), Intermedio (8-10), Avanzado (10-12)
- Motor híbrido: base de conocimiento local + IA para cualquier pregunta inesperada
- Responde preguntas anacrónicas: "¿Tienes coche?" → el personaje responde en personaje
- Cuestionario final autocorregible generado desde el historial del chat
- Lectura en voz alta (TTS del navegador)
- Exportar conversación como texto
- Alineación curricular con Castilla y León
- Sin datos de alumnos almacenados

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
└── README.md
```

---

## Despliegue paso a paso

### Paso 1 — Cuenta en GitHub
Ve a github.com, crea una cuenta gratuita o inicia sesión.

### Paso 2 — Crear el repositorio
1. Clic en "New repository".
2. Nombre: historia-viva (o el que quieras).
3. Márcalo como Public.
4. Clic en "Create repository".

### Paso 3 — Subir los archivos
Desde el navegador (sin instalar nada):
1. En la página del repositorio, clic en "uploading an existing file".
2. Arrastra todos los archivos y carpetas de este proyecto.
3. Clic en "Commit changes".

### Paso 4 — API key de Google Gemini (gratuita)
1. Ve a aistudio.google.com y crea una cuenta.
2. Menú lateral → "Get API Key" → "Create Key".
3. Ponle un nombre (ej. historia-viva) y cópiala.
   IMPORTANTE: guárdala bien, solo se muestra una vez.

### Paso 5 — Desplegar en Streamlit
1. Ve a share.streamlit.io (puedes entrar con tu cuenta de GitHub).
2. Clic en "New app".
3. Elige tu repositorio historia-viva y la rama main.
4. Main file path: app.py
5. Clic en "Advanced settings" → "Secrets" y pega exactamente esto:
   GEMINI_API_KEY = "sk-ant-api03-AQUI_VA_TU_CLAVE"
6. Clic en "Deploy!".

En unos minutos tendrás una URL pública tipo:
https://historia-viva.streamlit.app

---

## Prueba local (opcional)

pip install -r requirements.txt
mkdir .streamlit
echo 'GEMINI_API_KEY = "sk-ant-TUCLAVE"' > .streamlit/secrets.toml
streamlit run app.py

---

## Coste estimado

| Uso                        | Llamadas IA | Coste aprox. |
|----------------------------|-------------|--------------|
| 1 sesión (25 alumnos)      | ~75         | 0,00 EUR    |
| 1 mes escolar (20 sesiones)| ~1.500      | 0,00 EUR    |
| Curso completo (8 meses)   | ~12.000     | 0,00 EUR      |

Las preguntas habituales usan la base de conocimiento local (sin coste de IA).
Solo se llama a la IA cuando la pregunta es inesperada o no tiene buena coincidencia local.

---

## Preguntas frecuentes

Los datos de los alumnos no se guardan. La conversación vive solo en la sesión del navegador.

Para añadir una época nueva: crea data/nueva_epoca.js con la misma estructura
que los archivos existentes y añade su entrada en data/index.js.

Cualquier cambio en GitHub se despliega automáticamente en Streamlit en segundos.
