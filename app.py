from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import socket
import textwrap
from pathlib import Path
from typing import Any

import numpy as np
import requests
import streamlit as st
from pypdf import PdfReader


APP_DIR = Path(__file__).parent.resolve()
PDF_DIR = APP_DIR / "static" / "pdfs"
APPROVED_MANIFEST_PATH = APP_DIR / "data" / "approved_pdfs.json"
INDEX_DIR = APP_DIR / "data" / "index"
INDEX_METADATA_PATH = INDEX_DIR / "metadata.json"
INDEX_EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"
INDEX_STAMP_PATH = INDEX_DIR / "manifest_digest.txt"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1:8b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "embeddinggemma")
TOP_K = int(os.getenv("TOP_K", "8"))
MAX_CONTEXT_SOURCES = int(os.getenv("MAX_CONTEXT_SOURCES", "8"))
SIMILARITY_MIN = float(os.getenv("SIMILARITY_MIN", "0.22"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1100"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "180"))

LOCAL_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
]

NETWORK_GUARD_ENABLED = False


def enable_local_only_network():
    global NETWORK_GUARD_ENABLED
    if NETWORK_GUARD_ENABLED:
        return

    original_getaddrinfo = socket.getaddrinfo
    original_connect = socket.socket.connect
    original_create_connection = socket.create_connection

    def _is_local_host(host: str) -> bool:
        if host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
            return True
        try:
            ip_obj = ipaddress.ip_address(host)
            return any(ip_obj in net for net in LOCAL_NETS)
        except ValueError:
            pass

        try:
            infos = original_getaddrinfo(host, None)
        except socket.gaierror:
            return False

        for info in infos:
            addr = info[4][0]
            try:
                ip_obj = ipaddress.ip_address(addr)
            except ValueError:
                return False
            if not any(ip_obj in net for net in LOCAL_NETS):
                return False
        return True

    def guarded_getaddrinfo(host, port, *args, **kwargs):
        if host is not None and not _is_local_host(str(host)):
            raise OSError(f"Conexión externa bloqueada por modo offline: {host}")
        return original_getaddrinfo(host, port, *args, **kwargs)

    def guarded_connect(self, address):
        host = address[0]
        if not _is_local_host(str(host)):
            raise OSError(f"Conexión externa bloqueada por modo offline: {host}")
        return original_connect(self, address)

    def guarded_create_connection(address, *args, **kwargs):
        host = address[0]
        if not _is_local_host(str(host)):
            raise OSError(f"Conexión externa bloqueada por modo offline: {host}")
        return original_create_connection(address, *args, **kwargs)

    socket.getaddrinfo = guarded_getaddrinfo
    socket.socket.connect = guarded_connect
    socket.create_connection = guarded_create_connection
    NETWORK_GUARD_ENABLED = True


enable_local_only_network()


def load_approved_manifest() -> list[dict[str, Any]]:
    with open(APPROVED_MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_pdf_corpus() -> tuple[list[dict[str, Any]], list[str]]:
    approved = load_approved_manifest()
    approved_map = {item["filename"]: item for item in approved}
    errors: list[str] = []

    found_files = sorted(PDF_DIR.glob("*.pdf"))
    found_names = {p.name for p in found_files}
    approved_names = set(approved_map)

    missing = sorted(approved_names - found_names)
    extras = sorted(found_names - approved_names)

    if missing:
        errors.append(f"Faltan PDFs aprobados: {', '.join(missing)}")
    if extras:
        errors.append(f"Hay PDFs no aprobados en la carpeta: {', '.join(extras)}")

    verified: list[dict[str, Any]] = []
    for path in found_files:
        if path.name not in approved_map:
            continue
        actual_hash = sha256_of_file(path)
        expected_hash = approved_map[path.name]["sha256"]
        if actual_hash != expected_hash:
            errors.append(f"Hash no válido para {path.name}")
            continue
        record = dict(approved_map[path.name])
        record["path"] = str(path)
        verified.append(record)

    return verified, errors


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        cut = text.rfind(". ", start, end)
        if cut == -1 or cut <= start + chunk_size // 2:
            cut = text.rfind(" ", start, end)
        if cut == -1 or cut <= start:
            cut = end
        else:
            cut += 1
        chunk = text[start:cut].strip()
        if chunk:
            chunks.append(chunk)
        if cut >= len(text):
            break
        start = max(0, cut - overlap)
    return chunks


def extract_chunks(pdf_path: Path, filename: str) -> list[dict[str, Any]]:
    reader = PdfReader(str(pdf_path))
    chunks: list[dict[str, Any]] = []

    for page_idx, page in enumerate(reader.pages):
        try:
            raw_text = page.extract_text() or ""
        except Exception:
            raw_text = ""
        raw_text = raw_text.strip()
        if not raw_text:
            continue

        page_number = page_idx + 1
        for part_idx, chunk in enumerate(split_text(raw_text), start=1):
            chunks.append(
                {
                    "chunk_id": f"{filename}::p{page_number}::c{part_idx}",
                    "filename": filename,
                    "page": page_number,
                    "text": chunk,
                }
            )
    return chunks


def ollama_post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{OLLAMA_BASE_URL}{endpoint}"
    response = requests.post(url, json=payload, timeout=600)
    response.raise_for_status()
    return response.json()


def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    vectors = []
    batch_size = 16
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        data = ollama_post(
            "/api/embed",
            {
                "model": OLLAMA_EMBED_MODEL,
                "input": batch,
                "truncate": True,
                "keep_alive": "5m",
            },
        )
        batch_vectors = np.asarray(data["embeddings"], dtype=np.float32)
        vectors.append(batch_vectors)

    arr = np.vstack(vectors).astype(np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1e-12
    return arr / norms


def build_index() -> tuple[np.ndarray, list[dict[str, Any]], list[str], str]:
    verified, errors = verify_pdf_corpus()
    if errors:
        raise RuntimeError("\n".join(errors))

    manifest_digest = hashlib.sha256(
        json.dumps(verified, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    if INDEX_METADATA_PATH.exists() and INDEX_EMBEDDINGS_PATH.exists() and INDEX_STAMP_PATH.exists():
        old_digest = INDEX_STAMP_PATH.read_text(encoding="utf-8").strip()
        if old_digest == manifest_digest:
            metadata = json.loads(INDEX_METADATA_PATH.read_text(encoding="utf-8"))
            embeddings = np.load(INDEX_EMBEDDINGS_PATH)
            return embeddings, metadata, errors, manifest_digest

    all_chunks: list[dict[str, Any]] = []
    for item in verified:
        all_chunks.extend(extract_chunks(Path(item["path"]), item["filename"]))

    if not all_chunks:
        raise RuntimeError("No se ha podido extraer texto de los PDFs aprobados.")

    texts = [c["text"] for c in all_chunks]
    embeddings = embed_texts(texts)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    np.save(INDEX_EMBEDDINGS_PATH, embeddings)
    INDEX_METADATA_PATH.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    INDEX_STAMP_PATH.write_text(manifest_digest, encoding="utf-8")

    return embeddings, all_chunks, errors, manifest_digest


@st.cache_resource(show_spinner=False)
def load_index_cached():
    return build_index()


def search_chunks(question: str, embeddings: np.ndarray, metadata: list[dict[str, Any]], top_k: int = TOP_K):
    query_vec = embed_texts([question])[0]
    scores = embeddings @ query_vec
    top_idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_idx:
        item = dict(metadata[int(idx)])
        item["score"] = float(scores[int(idx)])
        results.append(item)
    return results


def format_sources_for_prompt(results: list[dict[str, Any]]) -> str:
    lines = []
    for i, item in enumerate(results, start=1):
        lines.append(
            textwrap.dedent(
                f"""
                [S{i}]
                PDF: {item["filename"]}
                Página: {item["page"]}
                Texto:
                {item["text"]}
                """
            ).strip()
        )
    return "\n\n".join(lines)


def answer_question(question: str, retrieved: list[dict[str, Any]]) -> dict[str, Any]:
    if not retrieved or retrieved[0]["score"] < SIMILARITY_MIN:
        return {
            "answer": "No he encontrado evidencia suficiente en los PDFs aprobados para responder con seguridad.",
            "source_ids": [],
            "notes": "La similitud semántica de los fragmentos recuperados es demasiado baja.",
        }

    prompt_sources = format_sources_for_prompt(retrieved[:MAX_CONTEXT_SOURCES])

    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "source_ids": {
                "type": "array",
                "items": {"type": "integer"},
            },
            "notes": {"type": "string"},
        },
        "required": ["answer", "source_ids", "notes"],
    }

    system = (
        "Eres un asistente jurídico-documental. "
        "Debes responder SOLO con la información presente en los fragmentos proporcionados. "
        "No uses conocimiento externo, no completes huecos y no cites fuentes no incluidas. "
        "Si no hay base suficiente, di que no has encontrado evidencia suficiente. "
        "Devuelve JSON válido según el esquema."
    )

    user = f"""
Pregunta del usuario:
{question}

Fuentes autorizadas:
{prompt_sources}

Instrucciones:
- Responde únicamente con información respaldada por las fuentes.
- No generalices más allá del texto.
- En source_ids, indica los números de fuente S utilizados.
- Si la respuesta no está claramente respaldada, responde que no has encontrado evidencia suficiente y deja source_ids vacío o muy reducido.
"""

    data = ollama_post(
        "/api/chat",
        {
            "model": OLLAMA_CHAT_MODEL,
            "stream": False,
            "format": schema,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {
                "temperature": 0,
            },
            "keep_alive": "5m",
        },
    )

    content = data["message"]["content"]
    parsed = json.loads(content)

    valid_ids = []
    for sid in parsed.get("source_ids", []):
        if isinstance(sid, int) and 1 <= sid <= len(retrieved[:MAX_CONTEXT_SOURCES]):
            valid_ids.append(sid)

    return {
        "answer": parsed.get("answer", "").strip(),
        "source_ids": valid_ids,
        "notes": parsed.get("notes", "").strip(),
    }


def source_url(filename: str, page: int) -> str:
    return f"/app/static/pdfs/{filename}#page={page}"


def show_source_card(item: dict[str, Any], label_id: int):
    url = source_url(item["filename"], item["page"])
    st.markdown(
        f"""
**Fuente S{label_id}**  
**PDF:** {item["filename"]}  
**Página:** {item["page"]}  
[🔗 Abrir PDF en esa página]({url})
"""
    )
    with st.expander("Ver fragmento recuperado"):
        st.write(item["text"])


def main():
    st.set_page_config(page_title="Consulta normativa offline", layout="wide")
    st.title("Consulta normativa offline con Ollama")
    st.caption("Solo consulta los 38 PDFs aprobados. Sin acceso a Internet. Todo el procesamiento se limita a localhost y a esta carpeta.")

    with st.sidebar:
        st.subheader("Configuración")
        st.write(f"**Chat model:** `{OLLAMA_CHAT_MODEL}`")
        st.write(f"**Embedding model:** `{OLLAMA_EMBED_MODEL}`")
        st.write(f"**Ollama URL:** `{OLLAMA_BASE_URL}`")
        st.write("**Corpus aprobado:** `38 PDFs`")
        st.write("La app bloquea conexiones salientes que no sean localhost.")
        st.info(
            "Antes del primer uso, instala y arranca Ollama y descarga los modelos.\n\n"
            f"- `ollama serve`\n"
            f"- `ollama pull {OLLAMA_CHAT_MODEL}`\n"
            f"- `ollama pull {OLLAMA_EMBED_MODEL}`"
        )

    try:
        with st.spinner("Verificando PDFs autorizados e índice local..."):
            embeddings, metadata, verify_errors, digest = load_index_cached()
    except Exception as e:
        st.error(f"No se pudo cargar el índice: {e}")
        st.stop()

    approved = load_approved_manifest()
    total_pages = sum(item.get("page_count", 0) or 0 for item in approved)
    st.success(f"Corpus verificado: {len(approved)} PDFs aprobados, {total_pages} páginas totales, {len(metadata)} fragmentos indexados.")

    with st.expander("Ver PDFs incluidos"):
        for item in approved:
            st.write(f"- {item['filename']} ({item.get('page_count', '?')} páginas)")

    question = st.text_area(
        "Escribe tu consulta",
        placeholder="Ejemplo: ¿Qué dice la normativa sobre los criterios prioritarios de admisión en primaria?",
        height=120,
    )

    col1, col2 = st.columns([1, 1])
    ask = col1.button("Consultar")
    show_debug = col2.checkbox("Mostrar recuperación semántica", value=False)

    if ask:
        if not question.strip():
            st.warning("Escribe una pregunta antes de consultar.")
            st.stop()

        with st.spinner("Buscando en los PDFs autorizados y generando respuesta..."):
            retrieved = search_chunks(question.strip(), embeddings, metadata, top_k=TOP_K)
            result = answer_question(question.strip(), retrieved)

        st.subheader("Respuesta")
        st.write(result["answer"] or "No se ha generado respuesta.")

        if result["notes"]:
            st.caption(result["notes"])

        st.subheader("Fuentes")
        used_sources = []
        for sid in result["source_ids"]:
            item = retrieved[sid - 1]
            used_sources.append(item)
            show_source_card(item, sid)

        if not used_sources:
            st.info("No se muestran fuentes porque la app no ha encontrado soporte suficiente en los PDFs recuperados.")

        if show_debug:
            st.subheader("Recuperación semántica")
            for i, item in enumerate(retrieved, start=1):
                st.markdown(
                    f"**S{i}** — score={item['score']:.4f} — {item['filename']} — página {item['page']}"
                )
                st.write(item["text"])

    st.divider()
    st.caption(
        "La app solo indexa los PDFs incluidos en `static/pdfs` y verificados por hash en `data/approved_pdfs.json`. "
        "Los enlaces a los PDFs son locales al propio servidor/app."
    )


if __name__ == "__main__":
    main()
