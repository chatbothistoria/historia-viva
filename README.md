# App offline de consulta normativa con Ollama

Esta app está preparada para consultar **solo** los **38 PDFs aprobados** incluidos en `static/pdfs`, sin usar Internet para responder.

## Qué hace

- indexa únicamente los PDFs aprobados;
- verifica cada PDF por **SHA-256** para evitar que entren otros documentos;
- usa **búsqueda semántica** con embeddings locales de Ollama;
- responde **solo** con texto respaldado por fragmentos recuperados;
- muestra **nombre del PDF, página y enlace local** al documento;
- bloquea conexiones salientes que no sean `localhost`.

## Estructura

- `app.py`: aplicación Streamlit
- `static/pdfs/`: corpus autorizado
- `data/approved_pdfs.json`: manifiesto cerrado con hashes
- `.streamlit/config.toml`: activa el servido de archivos estáticos

## Requisitos

1. Python 3.11 o similar
2. Ollama instalado y arrancado localmente
3. Modelos descargados en local

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate   # en Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Arrancar Ollama

En otra terminal:

```bash
ollama serve
ollama pull llama3.1:8b
ollama pull embeddinggemma
```

Si prefieres otros modelos locales, puedes cambiar estas variables:

```bash
export OLLAMA_CHAT_MODEL="llama3.1:8b"
export OLLAMA_EMBED_MODEL="embeddinggemma"
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
```

## Ejecutar la app

```bash
streamlit run app.py
```

## Notas importantes

- El enlace al PDF es **local a la propia app**, por ejemplo:
  - `http://localhost:8501/app/static/pdfs/01_Ley_Organica_2_2006_LOE_consolidada.pdf#page=12`
- Esto cumple tu requisito de no consultar fuentes externas: el navegador abre un PDF servido por la **misma app**, no por terceros.
- Si quieres desplegar esto fuera de tu ordenador pero seguir con Ollama, tendrás que alojar **también Ollama** en esa misma máquina o red privada. Para la **prueba inicial offline**, esta versión ya sirve.
