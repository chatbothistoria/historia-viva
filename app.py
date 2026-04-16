"""
Historia Viva · Infantil y Primaria
Chatbot educativo con personajes históricos — versión Streamlit + Claude AI
"""

import streamlit as st
import json
import re
import os
import unicodedata
import random

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG (debe ser la primera llamada a Streamlit)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Historia Viva · Infantil y Primaria",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS PERSONALIZADO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .stApp { background: linear-gradient(180deg,#f7f3eb 0%,#efe6d8 100%) !important; }
  section[data-testid="stSidebar"] > div { background: #fffdf9 !important; }
  .hero-box {
    background:#fffdf9; border:1px solid #dbcfc0; border-radius:16px;
    padding:18px 22px; margin-bottom:14px;
    box-shadow:0 6px 18px rgba(33,53,71,.07);
  }
  .hero-box h2 { margin:0 0 2px; color:#213547; font-size:1.45rem; }
  .hero-box .periodo { color:#667685; font-size:.9rem; margin:0 0 8px; }
  .hero-box .apertura { margin:10px 0 0; font-size:.96rem; line-height:1.55; }
  .level-chip {
    background:#8a4f23; color:white; border-radius:10px;
    padding:3px 11px; font-size:.8rem; display:inline-block;
  }
  .source-chip {
    background:#eef6f2; color:#275c4b; border-radius:8px;
    padding:2px 8px; font-size:.75rem; display:inline-block; margin-top:6px;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────
LEVELS = {
    "infantil":   {"label": "Infantil · 3-5 años",   "age": "3-5 años",   "max_chars": 300,  "sentences": 2},
    "básico":     {"label": "Básico · 6-8 años",      "age": "6-8 años",   "max_chars": 520,  "sentences": 3},
    "intermedio": {"label": "Intermedio · 8-10 años", "age": "8-10 años",  "max_chars": 1200, "sentences": 5},
    "avanzado":   {"label": "Avanzado · 10-12 años",  "age": "10-12 años", "max_chars": 1650, "sentences": 7},
}

THEME_KEYWORDS = {
    "identidad":    ["quien","eres","epoca","cuando","donde","vivias","periodo","cronologia","antes","despues","siglo","linea del tiempo","nomada","moverse"],
    "cotidiana":    ["vida","dia","comida","comias","comian","comer","alimentacion","casa","dormias","ropa","vestir","normal","cocina","pan","salud","medicina","hospital","higiene","baños","refugio","vivienda","ciudad","aldea"],
    "infancia":     ["nino","niño","nina","niña","escuela","jugar","jugabas","aprender","infancia","niños","niñas","colegio","maestro","juguetes","evacuados"],
    "trabajo":      ["trabajo","oficio","herramienta","fabricar","maquina","fabrica","tecnologia","tren","imprenta","metal","agricultura","comercio","moneda","barco","mina","ferrocarril","industria","invento","molino","escriba"],
    "poder":        ["mandaba","rey","reina","faraon","emperador","gobierno","gobernaba","poder","ley","democracia","dictadura","ciudadano","constitucion","elecciones","senado","parlamento","votar","republica"],
    "creencias":    ["dios","dioses","religion","creencias","templo","iglesia","mito","mitologia","ritual","ritos","arte","teatro","pintura","escultura","catedral","monasterio","mezquita","sinagoga","momia","piramide","olimpicos"],
    "conflicto":    ["guerra","miedo","hambre","bomba","trincheras","violencia","peligro","bombardeo","represion","refugio","muerte","persecucion","censura","exilio","genocidio","holocausto","terror","arma","carcel"],
    "desigualdad":  ["rico","pobre","igualdad","injusto","esclavo","mujeres","mujer","derechos","libertad","genero","clase social","obreros","burguesia","discriminacion","pobreza","siervos"],
    "comparacion":  ["hoy","ahora","actual","se parece","mejor","peor","diferente","comparar","todavia","nuestra epoca","coche","movil","internet","avion","ordenador","television","electronico","telefono"],
    "fuentes":      ["como sabemos","fuentes","pruebas","evidencia","archivo","testimonio","museo","patrimonio","yacimiento","monumento","restos","arqueologia","carta","documento","fotografia","fosa","memoria"],
    "delicada":     ["hiciste dano","mala","malo","culpa","arrepientes","equivocaste","injusta","terror","holocausto","genocidio","victimas","fosas","fusilados","censura"],
    "legado":       ["importante","recordar","legado","aprender","aprendemos","sirve","leccion","memoria democratica"],
}

STOPWORDS = set([
    "a","al","algo","algunas","algunos","ante","antes","asi","aunque","bajo","bien",
    "cada","casi","como","con","contra","cual","cuando","de","del","desde","donde",
    "dos","el","ella","ellas","ellos","en","entre","era","eran","eres","es","esa",
    "ese","eso","esta","estaba","estas","este","esto","fue","fueron","ha","habia",
    "hace","hacia","hasta","hay","la","las","le","les","lo","los","mas","me","mi",
    "mis","mucho","muy","no","nos","o","os","otra","otras","otro","para","pero",
    "poco","por","porque","que","quien","se","ser","si","sin","sobre","solo","son",
    "su","sus","tambien","te","ti","tu","tus","un","una","unas","unos","ya",
    "tiene","tienen","tenia","tenian","puede","pueden","hacen",
])

LEVEL_THEMES = {
    "infantil":   ["cotidiana", "infancia", "identidad"],
    "básico":     ["cotidiana", "infancia", "identidad", "trabajo"],
    "intermedio": ["cotidiana", "identidad", "poder", "fuentes", "conflicto"],
    "avanzado":   ["identidad", "cotidiana", "fuentes", "poder", "desigualdad", "legado"],
}

# ─────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS (cacheada)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_all_data():
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    with open(os.path.join(data_dir, "index.js"), "r", encoding="utf-8") as f:
        idx_content = f.read()
    idx_match = re.search(r"window\.HV_INDEX\s*=\s*(\[[\s\S]*?\]);", idx_content)
    era_index = json.loads(idx_match.group(1)) if idx_match else []

    eras = {}
    for era_info in era_index:
        era_id = era_info["id"]
        fp = os.path.join(data_dir, f"{era_id}.js")
        if not os.path.exists(fp):
            continue
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        start = content.rfind("= {")
        if start == -1:
            continue
        json_str = content[start + 2:].rstrip().rstrip(";").rstrip()
        try:
            eras[era_id] = json.loads(json_str)
        except json.JSONDecodeError:
            pass

    return era_index, eras

# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES DE TEXTO
# ─────────────────────────────────────────────────────────────────────────────
def normalize(text: str) -> str:
    text = text.lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return " ".join(text.split())

def tokens(text: str) -> set:
    return {t for t in normalize(text).split() if len(t) > 2 and t not in STOPWORDS}

def detect_theme(question: str) -> str:
    q = normalize(question)
    best_theme, best_score = "cotidiana", 0
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > best_score:
            best_score, best_theme = score, theme
    return best_theme

def best_faq(question: str, era_data: dict):
    q_norm = normalize(question)
    q_tok = tokens(question)
    best, best_score = None, 0
    for faq in era_data.get("faqs", []):
        kw_score = sum(1 for k in faq.get("keywords", []) if normalize(k) in q_norm)
        tok_score = len(q_tok & tokens(faq.get("question", "")))
        score = kw_score * 2 + tok_score
        if score > best_score:
            best_score, best = score, faq
    return best if best_score >= 2 else None

def faq_answer(faq: dict, level: str) -> str:
    mapping = {"infantil": "infantil", "básico": "basic",
               "intermedio": "intermediate", "avanzado": "advanced"}
    return faq.get(mapping.get(level, "basic"), "") or faq.get("basic", "")

def trim_to_level(text: str, level: str) -> str:
    cfg = LEVELS[level]
    if not text:
        return text
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    result = ""
    for p in parts[: cfg["sentences"]]:
        if len(result) + len(p) > cfg["max_chars"]:
            break
        result += p + " "
    return result.strip() or text[: cfg["max_chars"]]

# ─────────────────────────────────────────────────────────────────────────────
# MOTOR LOCAL DE RESPUESTAS
# ─────────────────────────────────────────────────────────────────────────────
def local_answer(question: str, era_data: dict, level: str):
    """Devuelve (respuesta, confianza). Confianza alta → no hace falta IA."""
    faq = best_faq(question, era_data)
    if faq:
        ans = faq_answer(faq, level)
        if ans:
            return trim_to_level(ans, level), 0.9

    theme = detect_theme(question)
    section = era_data.get("sections", {}).get(theme, "")
    if section:
        return trim_to_level(section, level), 0.5

    return None, 0.0

# ─────────────────────────────────────────────────────────────────────────────
# RESPUESTA CON CLAUDE
# ─────────────────────────────────────────────────────────────────────────────
def gemini_answer(question: str, era_data: dict, level: str, history: list) -> str:
    try:
        import google.generativeai as genai
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if not api_key:
            return "_[IA no configurada: añade GEMINI_API_KEY en los Secrets de Streamlit]_"
        genai.configure(api_key=api_key)
    except Exception as e:
        return f"_[Error al conectar con la IA: {str(e)[:80]}]_"

    level_cfg = LEVELS[level]
    sections  = era_data.get("sections", {})
    teacher   = era_data.get("teacher", {})

    # Contexto: secciones más relevantes para esta pregunta
    theme = detect_theme(question)
    context_keys = list(dict.fromkeys(["identidad", "cotidiana", theme, "comparacion"]))
    context_text = "\n\n".join(
        f"[{k.upper()}]\n{sections[k][:700]}"
        for k in context_keys if k in sections
    )

    anacronismos = teacher.get("anacronismos", [])
    anac_str = (
        "\n\nErrores históricos a evitar: " + "; ".join(anacronismos)
        if anacronismos else ""
    )

    system = f"""Eres {era_data['voz']} del período {era_data['name']} ({era_data['periodo']}).

Responde SIEMPRE en primera persona, como ese personaje histórico real.
Adapta vocabulario y complejidad para alumnos de {level_cfg['age']}.

CONTEXTO HISTÓRICO DE TU ÉPOCA:
{context_text}{anac_str}

REGLAS IMPORTANTES:
- Responde en personaje en todo momento, nunca rompas el rol.
- Si preguntan por algo que NO existía en tu época (coches, móviles, aviones, internet,
  ordenadores, televisión...), responde con curiosidad genuina desde tu perspectiva:
  "¿Qué es eso? Nunca he oído esa palabra..." y explica cómo hacíais lo equivalente en tu época.
- Si es un tema sensible (violencia, muerte, represión), responde con sensibilidad
  apropiada para niños, desde perspectiva histórica y sin morbo.
- Responde siempre en español.
- Máximo {level_cfg['max_chars']} caracteres en tu respuesta."""

    # Construir historial de conversación para Gemini
    chat_history = []
    for m in history[-6:]:
        role = "user" if m["role"] == "user" else "model"
        chat_history.append({"role": role, "parts": [m["content"]]})

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system,
        )
        chat = model.start_chat(history=chat_history)
        response = chat.send_message(question)
        return response.text
    except Exception as e:
        return f"_[Error de la IA: {str(e)[:80]}]_"

# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL DE RESPUESTA (híbrida)
# ─────────────────────────────────────────────────────────────────────────────
def get_answer(question: str, era_data: dict, level: str, history: list):
    """
    Lógica híbrida:
    - FAQ con buena coincidencia → local (rápida, sin coste ni llamada a IA)
    - Todo lo demás → Gemini gratis (responde cualquier pregunta, incluso anacrónicas)
    """
    answer, confidence = local_answer(question, era_data, level)
    if confidence >= 0.9:
        return answer, "local"
    return gemini_answer(question, era_data, level, history), "gemini"

# ─────────────────────────────────────────────────────────────────────────────
# SUGERENCIAS
# ─────────────────────────────────────────────────────────────────────────────
def get_suggestions(era_data: dict, level: str, n: int = 6) -> list:
    themes = LEVEL_THEMES.get(level, ["cotidiana", "identidad"])
    pool = [
        faq["question"]
        for faq in era_data.get("faqs", [])
        if faq.get("theme") in themes
    ]
    random.shuffle(pool)
    return pool[:n]

# ─────────────────────────────────────────────────────────────────────────────
# CUESTIONARIO FINAL
# ─────────────────────────────────────────────────────────────────────────────
def build_quiz(messages: list, era_data: dict) -> list:
    exchanges = [
        {"q": messages[i - 1]["content"], "a": messages[i]["content"]}
        for i in range(1, len(messages))
        if messages[i]["role"] == "assistant" and messages[i - 1]["role"] == "user"
    ]
    if len(exchanges) < 2:
        return []

    sections  = list(era_data.get("sections", {}).values())
    quiz = []

    for ex in exchanges[:5]:
        sents   = re.split(r"(?<=[.!?])\s+", ex["a"].strip())
        correct = (sents[0] if sents and len(sents[0]) > 20 else ex["a"])[:200]

        distractors = []
        shuffled = sections[:]
        random.shuffle(shuffled)
        for sec in shuffled:
            s = re.split(r"(?<=[.!?])\s+", sec.strip())
            if s and s[0] != correct and len(s[0]) > 20:
                distractors.append(s[0][:200])
            if len(distractors) >= 3:
                break

        if len(distractors) >= 2:
            options = [correct] + distractors[:3]
            random.shuffle(options)
            quiz.append({"q": ex["q"], "options": options, "correct": correct})

    return quiz[:5]

# ─────────────────────────────────────────────────────────────────────────────
# TEXTO A VOZ (JavaScript del navegador)
# ─────────────────────────────────────────────────────────────────────────────
def speak_text(text: str):
    import streamlit.components.v1 as components
    safe = json.dumps(text)
    components.html(
        f"<script>window.speechSynthesis&&window.speechSynthesis.cancel();"
        f"var u=new SpeechSynthesisUtterance({safe});"
        f"u.lang='es-ES';u.rate=0.92;"
        f"window.speechSynthesis&&window.speechSynthesis.speak(u);</script>",
        height=0,
    )

def stop_speak():
    import streamlit.components.v1 as components
    components.html(
        "<script>window.speechSynthesis&&window.speechSynthesis.cancel();</script>",
        height=0,
    )

# ─────────────────────────────────────────────────────────────────────────────
# ESTADO DE SESIÓN
# ─────────────────────────────────────────────────────────────────────────────
def init_state(first_era_id: str):
    defaults = {
        "era_id":         first_era_id,
        "level":          "básico",
        "messages":       [],
        "suggestions":    [],
        "pending_q":      None,
        "show_quiz":      False,
        "quiz_items":     [],
        "quiz_answers":   {},
        "quiz_submitted": False,
        "last_bot_text":  "",
        "big_text":       False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# APP PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def main():
    era_index, eras = load_all_data()
    if not era_index:
        st.error("No se encontraron datos. Comprueba que la carpeta `data/` está junto a `app.py`.")
        return

    init_state(era_index[0]["id"])
    ss          = st.session_state
    current_era = eras.get(ss.era_id, {})
    level       = ss.level

    if ss.big_text:
        st.markdown("<style>html{font-size:18px}</style>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # BARRA LATERAL
    # ════════════════════════════════════════════════════════════════════════
    with st.sidebar:
        st.markdown("## 🏛️ Historia Viva")
        st.caption("Infantil y Primaria · IA histórica")

        # 1. Época
        st.markdown("---")
        st.markdown("**1. Elige una época**")
        for era_info in era_index:
            eid = era_info["id"]
            is_active = eid == ss.era_id
            if st.button(
                f"{'▶ ' if is_active else ''}{era_info['name']}",
                key=f"era_{eid}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                help=era_info["periodo"],
            ):
                if eid != ss.era_id:
                    ss.era_id, ss.messages, ss.suggestions = eid, [], []
                    ss.show_quiz, ss.last_bot_text = False, ""
                    st.rerun()

        # 2. Nivel
        st.markdown("---")
        st.markdown("**2. Etapa educativa**")
        new_level = st.radio(
            "Nivel",
            options=list(LEVELS.keys()),
            format_func=lambda x: LEVELS[x]["label"],
            index=list(LEVELS.keys()).index(level),
            label_visibility="collapsed",
        )
        if new_level != level:
            ss.level, ss.messages, ss.suggestions = new_level, [], []
            ss.show_quiz = False
            st.rerun()

        # 3. Herramientas
        st.markdown("---")
        st.markdown("**3. Herramientas**")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💡 Sugerencia", use_container_width=True):
                pool = get_suggestions(current_era, level, 10)
                if pool:
                    ss.pending_q = random.choice(pool)
                    st.rerun()
        with c2:
            if st.button("🔄 Reiniciar", use_container_width=True):
                ss.messages, ss.suggestions = [], []
                ss.show_quiz, ss.last_bot_text = False, ""
                st.rerun()

        if ss.last_bot_text:
            c3, c4 = st.columns(2)
            with c3:
                if st.button("🔊 Leer", use_container_width=True):
                    speak_text(ss.last_bot_text)
            with c4:
                if st.button("⏹ Parar", use_container_width=True):
                    stop_speak()

        font_label = "🔡 Texto normal" if ss.big_text else "🔠 Texto grande"
        if st.button(font_label, use_container_width=True):
            ss.big_text = not ss.big_text
            st.rerun()

        if len(ss.messages) >= 4:
            if st.button("📝 Cuestionario final", use_container_width=True):
                ss.quiz_items = build_quiz(ss.messages, current_era)
                ss.quiz_answers, ss.quiz_submitted = {}, False
                ss.show_quiz = True
                st.rerun()

        if ss.messages:
            chat_export = (
                f"Historia Viva · {current_era.get('name','')}\n"
                f"Nivel: {LEVELS[level]['label']}\n\n"
            )
            for msg in ss.messages:
                role = "Alumno" if msg["role"] == "user" else current_era.get("voz", "Personaje")
                chat_export += f"{role}:\n{msg['content']}\n\n"
            st.download_button(
                "📥 Exportar chat",
                data=chat_export,
                file_name=f"historia_{ss.era_id}.txt",
                mime="text/plain",
                use_container_width=True,
            )

    # ════════════════════════════════════════════════════════════════════════
    # ÁREA PRINCIPAL
    # ════════════════════════════════════════════════════════════════════════

    # Hero
    if current_era:
        st.markdown(f"""
        <div class="hero-box">
          <h2>{current_era.get('name','')}</h2>
          <p class="periodo">{current_era.get('periodo','')}</p>
          <span class="level-chip">{LEVELS[level]['label']}</span>
          <p class="apertura"><em>{current_era.get('apertura','')}</em></p>
        </div>
        """, unsafe_allow_html=True)

    # Cuestionario
    if ss.show_quiz:
        if not ss.quiz_items:
            st.info("Necesitas al menos 2 intercambios en el chat para generar el cuestionario.")
            ss.show_quiz = False
        else:
            with st.container(border=True):
                st.markdown("### 📝 Cuestionario final de repaso")
                st.caption("Basado en los contenidos que han aparecido en este chat.")
                for i, item in enumerate(ss.quiz_items):
                    st.markdown(f"**Pregunta {i+1}:** {item['q']}")
                    answer = st.radio(
                        "Elige:",
                        options=item["options"],
                        key=f"qz_{i}",
                        disabled=ss.quiz_submitted,
                        label_visibility="collapsed",
                    )
                    ss.quiz_answers[i] = answer
                    if ss.quiz_submitted:
                        ok = ss.quiz_answers.get(i) == item["correct"]
                        c_short = item["correct"][:150] + ("…" if len(item["correct"]) > 150 else "")
                        st.caption(f"{'✅' if ok else '❌'} Respuesta: _{c_short}_")
                    st.markdown("---")

                if not ss.quiz_submitted:
                    col_a, col_b = st.columns([2, 1])
                    with col_a:
                        if st.button("✅ Autocorregir", type="primary"):
                            ss.quiz_submitted = True
                            st.rerun()
                    with col_b:
                        if st.button("Cerrar"):
                            ss.show_quiz = False
                            st.rerun()
                else:
                    correct_n = sum(
                        1 for i, item in enumerate(ss.quiz_items)
                        if ss.quiz_answers.get(i) == item["correct"]
                    )
                    total = len(ss.quiz_items)
                    if correct_n == total:
                        st.success(f"🎉 ¡Perfecto! {correct_n}/{total} respuestas correctas.")
                    elif correct_n >= total * 0.6:
                        st.warning(f"👍 Bien. {correct_n}/{total} correctas.")
                    else:
                        st.error(f"📚 {correct_n}/{total} correctas. Repasa el chat e inténtalo de nuevo.")
                    if st.button("Cerrar cuestionario"):
                        ss.show_quiz = False
                        st.rerun()

    # Mensajes del chat
    for msg in ss.messages:
        avatar = "🧑‍🎓" if msg["role"] == "user" else "🏛️"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
            if msg["role"] == "assistant" and msg.get("source") == "gemini":
                st.markdown('<span class="source-chip">✨ Respuesta con IA</span>', unsafe_allow_html=True)

    # Sugerencias (solo cuando el chat está vacío)
    if not ss.messages:
        if not ss.suggestions:
            ss.suggestions = get_suggestions(current_era, level)
        if ss.suggestions:
            st.markdown("**¿Sobre qué quieres preguntar?**")
            cols = st.columns(2)
            for idx, sug in enumerate(ss.suggestions[:6]):
                with cols[idx % 2]:
                    if st.button(f"💬 {sug}", key=f"sug_{idx}", use_container_width=True):
                        ss.pending_q = sug
                        st.rerun()

    # Pregunta pendiente (de sugerencias)
    if ss.pending_q:
        question = ss.pending_q
        ss.pending_q = None
        ss.messages.append({"role": "user", "content": question})
        with st.spinner("Pensando…"):
            ans, src = get_answer(question, current_era, level, ss.messages)
        ss.messages.append({"role": "assistant", "content": ans, "source": src})
        ss.last_bot_text = ans
        st.rerun()

    # Input del chat
    placeholder = (
        f"Pregunta a {current_era.get('voz', 'el personaje')}…"
        if current_era else "Elige una época para empezar…"
    )
    if prompt := st.chat_input(placeholder):
        ss.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.write(prompt)
        with st.chat_message("assistant", avatar="🏛️"):
            with st.spinner("Pensando…"):
                ans, src = get_answer(prompt, current_era, level, ss.messages)
            st.write(ans)
            if src == "gemini":
                st.markdown('<span class="source-chip">✨ Respuesta con IA</span>', unsafe_allow_html=True)
        ss.messages.append({"role": "assistant", "content": ans, "source": src})
        ss.last_bot_text = ans
        st.rerun()


if __name__ == "__main__":
    main()
