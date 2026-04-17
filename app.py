"""
Historia Viva · Infantil y Primaria  —  v7
─────────────────────────────────────────
Mejoras v7:
  1. Imágenes por época (Wikipedia REST API, cacheadas al arrancar)
  2. Panel "¿Sabías que?" con microfacts de la base de datos
  3. Panel docente con estadísticas de clase (sin base de datos externa)
"""

import streamlit as st
import json, re, os, unicodedata, random
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Historia Viva",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# METADATOS POR ÉPOCA
# ═══════════════════════════════════════════════════════════════════════════════
ERA_META = {
    "paleolitico":            {"emoji":"🦣","color":"#8B6347","bg":"#fdf3ec","wiki":"Cave_painting"},
    "neolitico":              {"emoji":"🌾","color":"#5A8A3C","bg":"#f0f9ec","wiki":"Neolithic"},
    "edad_metales":           {"emoji":"⚒️","color":"#B5830A","bg":"#fdf6e3","wiki":"Bronze_Age"},
    "egipto":                 {"emoji":"🏺","color":"#C9960C","bg":"#fef9e7","wiki":"Ancient_Egypt"},
    "grecia":                 {"emoji":"🏛️","color":"#2471A3","bg":"#ebf5fb","wiki":"Ancient_Greece"},
    "roma":                   {"emoji":"🦅","color":"#A93226","bg":"#fdedec","wiki":"Ancient_Rome"},
    "edad_media":             {"emoji":"🏰","color":"#6C3483","bg":"#f5eef8","wiki":"Middle_Ages"},
    "america_precolombina":   {"emoji":"🌽","color":"#1E8449","bg":"#eafaf1","wiki":"Pre-Columbian_era"},
    "renacimiento":           {"emoji":"🎨","color":"#D35400","bg":"#fef5ec","wiki":"Renaissance"},
    "revolucion_francesa":    {"emoji":"⚖️","color":"#1A5276","bg":"#eaf0fb","wiki":"French_Revolution"},
    "revolucion_industrial":  {"emoji":"🏭","color":"#4D5656","bg":"#f2f3f4","wiki":"Industrial_Revolution"},
    "primera_guerra_mundial": {"emoji":"🕊️","color":"#6E7E5A","bg":"#f2f4ef","wiki":"World_War_I"},
    "guerra_civil_espanola":  {"emoji":"📜","color":"#7E5109","bg":"#fdf0e3","wiki":"Spanish_Civil_War"},
    "segunda_guerra_mundial": {"emoji":"🌍","color":"#1B2631","bg":"#eaecee","wiki":"World_War_II"},
    "dictadura_franquista":   {"emoji":"📢","color":"#78281F","bg":"#fdedec","wiki":"Francoist_Spain"},
    "democracia_actual":      {"emoji":"🗳️","color":"#117A65","bg":"#e8f8f5","wiki":"Spanish_transition_to_democracy"},
}

# ═══════════════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

html, body, .stApp, [class*="css"] {
  font-family: 'Nunito', 'Segoe UI', sans-serif !important;
}
.stApp { background: linear-gradient(145deg, #f0f4ff 0%, #fff8f6 100%) !important; }
section[data-testid="stSidebar"] > div {
  background: #ffffff !important; border-right: 2px solid #e8eaf6;
}
/* Botones */
div[data-testid="stButton"] > button {
  border-radius: 12px !important; font-weight: 700 !important;
  font-size: .83rem !important; transition: all .15s !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, #7c4dff, #5c35d9) !important;
  border: none !important; color: white !important;
}
div[data-testid="stButton"] > button[kind="secondary"] {
  background: #f8f7ff !important; border: 2px solid #e8e5ff !important;
  color: #5c35d9 !important;
}
div[data-testid="stButton"] > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(124,77,255,.2) !important;
}
/* Radio nivel */
div[data-testid="stRadio"] label {
  background: #f8f7ff; border: 2px solid #e8e5ff;
  border-radius: 12px; padding: 6px 12px; margin: 3px 0;
  font-weight: 600; font-size: .85rem; cursor: pointer;
  transition: all .15s; display: block;
}
/* Hero card con imagen */
.hero-card {
  border-radius: 22px; overflow: hidden; margin-bottom: 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,.10); position: relative;
}
.hero-img {
  width: 100%; height: 180px; object-fit: cover;
  display: block; filter: brightness(.75);
}
.hero-content {
  padding: 16px 22px 18px; position: relative;
}
.hero-avatar  { font-size: 3rem; display: block; margin-bottom: 4px; line-height:1; }
.hero-era-name{ font-size: 1.6rem; font-weight: 900; margin: 0 0 2px; }
.hero-period  { font-size: .86rem; opacity: .72; margin: 0 0 8px; }
.hero-badge   {
  display: inline-block; border-radius: 10px;
  padding: 3px 12px; font-size: .78rem; font-weight: 700; margin-bottom: 8px;
}
.hero-voice {
  font-size: .9rem; font-style: italic; line-height: 1.55;
  background: rgba(255,255,255,.55); border-radius: 12px;
  padding: 10px 14px; border-left: 4px solid rgba(255,255,255,.8);
}
/* Chat */
div[data-testid="stChatMessage"] {
  border-radius: 18px !important; margin-bottom: 6px !important;
  border: 1px solid rgba(0,0,0,.06) !important;
}
/* ¿Sabías que? */
.microfact-card {
  background: linear-gradient(135deg, #f0f4ff, #fef5ec);
  border: 1.5px solid #e8e0ff; border-radius: 14px;
  padding: 10px 14px; margin: 8px 0 14px; font-size: .88rem;
  color: #3d3061; display: flex; gap: 10px; align-items: flex-start;
}
.microfact-icon { font-size: 1.3rem; flex-shrink: 0; }
.microfact-text { line-height: 1.5; }
/* Sugerencias */
.sug-label { font-size: .95rem; font-weight: 800; color: #5c35d9; margin-bottom: 8px; }
/* Quiz */
.quiz-progress-bar {
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 8px; font-size: .85rem; font-weight: 700; color: #7c4dff;
}
.quiz-dot {
  width: 11px; height: 11px; border-radius: 50%;
  background: #e8e5ff; display: inline-block; transition: background .2s;
}
.quiz-dot.done    { background: #7c4dff; }
.quiz-dot.current { background: #ff6b6b; transform: scale(1.3); }
.quiz-question-card {
  background: white; border: 2px solid #e8e5ff;
  border-radius: 18px; padding: 18px 20px; margin-bottom: 14px;
}
.quiz-q-text { font-weight: 800; font-size: 1.08rem; color: #2d3561; margin-bottom: 2px; }
.quiz-reveal-ok  {
  background: #e8f8f0; border: 1.5px solid #6bcb77;
  border-radius: 10px; padding: 7px 12px; font-size: .87rem;
  margin-top: 6px; color: #2e7d32;
}
.quiz-reveal-bad {
  background: #fff0f0; border: 1.5px solid #ff6b6b;
  border-radius: 10px; padding: 7px 12px; font-size: .87rem;
  margin-top: 6px; color: #c0392b;
}
/* Score screen */
.quiz-score-screen {
  text-align: center; padding: 32px 24px 28px;
  background: white; border-radius: 22px;
  border: 2px solid #e8e5ff;
  box-shadow: 0 6px 24px rgba(0,0,0,.08); margin-bottom: 20px;
}
.quiz-score-big  { font-size: 4.5rem; display:block; margin-bottom: 8px; }
.quiz-score-msg  { font-size: 1.25rem; font-weight: 900; color: #5c35d9; margin-bottom: 10px; }
.quiz-score-badge {
  display: inline-block; background: linear-gradient(135deg,#7c4dff,#5c35d9);
  color: white; border-radius: 14px; padding: 7px 22px;
  font-size: 1.1rem; font-weight: 800; margin: 6px 0 22px;
}
/* Panel docente */
.teacher-stat-card {
  background: white; border: 2px solid #e8e5ff; border-radius: 16px;
  padding: 16px 20px; margin-bottom: 12px;
}
.teacher-stat-title { font-size: .8rem; font-weight: 700; color: #667685; margin-bottom: 4px; }
.teacher-stat-value { font-size: 2rem; font-weight: 900; color: #5c35d9; }
.teacher-q-row {
  background: #f8f7ff; border-radius: 10px; padding: 8px 12px;
  margin-bottom: 6px; font-size: .85rem; color: #2d3561;
  border-left: 3px solid #7c4dff;
}
.teacher-q-meta { font-size: .75rem; color: #667685; margin-top: 2px; }
/* Bienvenida */
.welcome-container {
  text-align: center; max-width: 660px; margin: 20px auto; padding: 0 16px;
}
.welcome-title { font-size: 2.4rem; font-weight: 900; color: #5c35d9; margin-bottom: 4px; }
.welcome-sub   { font-size: 1.1rem; color: #6c6c9b; margin-bottom: 28px; }
.welcome-steps { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; margin-bottom: 30px; }
.welcome-step  {
  background: white; border: 2px solid #e8e5ff; border-radius: 18px;
  padding: 18px 16px; width: 180px; text-align: center;
  box-shadow: 0 4px 16px rgba(124,77,255,.1);
}
.welcome-step-icon { font-size: 2.4rem; margin-bottom: 8px; }
.welcome-step-text { font-size: .88rem; font-weight: 700; color: #3d3d6b; line-height: 1.4; }
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50%       { transform: translateY(-8px); }
}
.bounce { animation: bounce 2s infinite; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════
LEVELS = {
    "infantil":   {"label":"🌱 Infantil  3-5 años",  "age":"3-5 años",  "max_chars":280},
    "básico":     {"label":"⭐ Básico  6-8 años",     "age":"6-8 años",  "max_chars":500},
    "intermedio": {"label":"🚀 Intermedio  8-10 años","age":"8-10 años", "max_chars":1100},
    "avanzado":   {"label":"🎓 Avanzado  10-12 años", "age":"10-12 años","max_chars":1600},
}

STEPWISE_QUIZ_LEVELS = {"infantil","básico"}

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
    "infantil":   ["cotidiana","infancia","identidad"],
    "básico":     ["cotidiana","infancia","identidad","trabajo"],
    "intermedio": ["cotidiana","identidad","poder","fuentes","conflicto"],
    "avanzado":   ["identidad","cotidiana","fuentes","poder","desigualdad","legado"],
}

THEME_EMOJI = {
    "cotidiana":"🍞","infancia":"🎮","identidad":"🗓️","trabajo":"⚒️","poder":"👑",
    "creencias":"🙏","conflicto":"⚔️","desigualdad":"⚖️","comparacion":"🔄",
    "fuentes":"🏛️","legado":"💡","delicada":"💬",
}

INFANTIL_ERA_SUGGESTIONS = {
    "paleolitico":            ["¿Vivíais en cuevas?","¿Veíais mamuts de verdad?","¿Teníais fuego?","¿Qué comíais?","¿Había niños como yo?","¿Teníais casa?"],
    "neolitico":              ["¿Teníais animales?","¿Plantabais cosas para comer?","¿Cómo era tu casa?","¿Teníais perros?","¿Qué comíais?","¿Había niños como yo?"],
    "edad_metales":           ["¿De qué estaban hechas vuestras espadas?","¿Trabajabais el metal?","¿Qué comíais?","¿Cómo era tu casa?","¿Había niños como yo?","¿Teníais castillos?"],
    "egipto":                 ["¿Teníais pirámides?","¿Cómo eran las momias?","¿El Nilo estaba cerca?","¿Teníais gatos?","¿Cómo era vuestro faraón?","¿Qué comíais?"],
    "grecia":                 ["¿Ibais a los Juegos Olímpicos?","¿Teníais muchos dioses?","¿Cómo eran los templos?","¿Los niños iban a la escuela?","¿Qué comíais?","¿Quién mandaba?"],
    "roma":                   ["¿Teníais gladiadores?","¿Cómo eran los soldados romanos?","¿Teníais un emperador?","¿Qué comíais?","¿Los niños iban a la escuela?","¿Teníais baños?"],
    "edad_media":             ["¿Vivíais en castillos?","¿Había caballeros con armadura?","¿Teníais un rey?","¿Qué comíais?","¿Los niños iban a la escuela?","¿Había dragones?"],
    "america_precolombina":   ["¿Teníais pirámides?","¿Comíais chocolate?","¿Quién mandaba?","¿Cómo eran vuestras casas?","¿Qué animales teníais?","¿Había niños como yo?"],
    "renacimiento":           ["¿Pintabais cuadros?","¿Cómo eran los barcos?","¿Qué comíais?","¿Los niños iban a la escuela?","¿Cómo os vestíais?","¿Quién mandaba?"],
    "revolucion_francesa":    ["¿Había un rey?","¿Por qué estabais enfadados?","¿Qué pasó con el rey?","¿Qué comíais?","¿Teníais miedo?","¿Había niños como yo?"],
    "revolucion_industrial":  ["¿Teníais trenes?","¿Había muchas fábricas?","¿Teníais electricidad?","¿Los niños trabajaban?","¿Cómo eran las ciudades?","¿Qué comíais?"],
    "primera_guerra_mundial": ["¿Había mucha guerra?","¿Teníais miedo?","¿Qué pasaba en la guerra?","¿Cómo vivíais?","¿Había niños como yo?","¿Os hacía daño la guerra?"],
    "guerra_civil_espanola":  ["¿Había guerra en España?","¿Teníais miedo?","¿Los niños tenían que huir?","¿Cómo vivíais?","¿Qué comíais?","¿Por qué había guerra?"],
    "segunda_guerra_mundial": ["¿Había bombardeos?","¿Teníais miedo?","¿Los niños podían ir a la escuela?","¿Qué comíais?","¿Cómo vivíais?","¿Cuándo acabó la guerra?"],
    "dictadura_franquista":   ["¿Quién mandaba en España?","¿Los niños podían jugar?","¿Podíais decir lo que pensabais?","¿Cómo vivíais?","¿Qué comíais?","¿Ibais a la escuela?"],
    "democracia_actual":      ["¿Podéis votar?","¿Todos somos iguales?","¿Quién manda ahora?","¿Los niños tienen derechos?","¿Hay escuelas para todos?","¿Podéis decir lo que pensáis?"],
}
INFANTIL_FALLBACK = ["¿Dónde vivíais?","¿Qué comíais?","¿Había niños como yo?","¿Cómo era tu casa?","¿A qué jugabais?","¿Quién mandaba?"]

QUIZ_CONFIG = {
    "infantil":   {"n":3,"instruccion":(
        "Genera exactamente 3 preguntas de VERDAD o MENTIRA para niños de 3-5 años. "
        "Frases muy simples, máximo 8 palabras. "
        'Opciones SIEMPRE: ["✅ Verdad", "❌ Mentira"]'
    )},
    "básico":     {"n":4,"instruccion":(
        "Genera exactamente 4 preguntas de opción múltiple con 3 opciones para niños de 6-8 años. "
        "Preguntas cortas y claras. Opciones de máximo 7 palabras."
    )},
    "intermedio": {"n":5,"instruccion":(
        "Genera exactamente 5 preguntas de opción múltiple con 4 opciones para alumnos de 8-10 años. "
        "Incluye preguntas sobre causas y comparaciones sencillas."
    )},
    "avanzado":   {"n":5,"instruccion":(
        "Genera exactamente 5 preguntas de opción múltiple con 4 opciones para alumnos de 10-12 años. "
        "Incluye preguntas de comprensión profunda y reflexión histórica."
    )},
}

QUIZ_FEEDBACK = {
    "infantil":   {"perfect":"🌟🌟🌟 ¡Eres un campeón! ¡Lo sabías todo!","good":"😊 ¡Muy bien! ¡Has aprendido mucho!","low":"🤗 ¡Ánimo! Vuelve a chatear y luego inténtalo de nuevo."},
    "básico":     {"perfect":"🏆 ¡Perfecto! ¡Todas correctas! Eres un historiador increíble.","good":"👍 ¡Muy bien! Casi lo tienes. Repasa un poco más.","low":"📚 No pasa nada. Lee el chat otra vez y vuelve a intentarlo."},
    "intermedio": {"perfect":"🥇 ¡Sobresaliente! Has respondido todo correctamente.","good":"👏 ¡Buen trabajo! Tienes casi todo claro.","low":"📖 Hay cosas que repasar. Vuelve a leer el chat con atención."},
    "avanzado":   {"perfect":"🎓 ¡Excelente! Dominas perfectamente los contenidos.","good":"✅ Buen nivel. Hay algún detalle que merece un repaso.","low":"📚 Conviene revisar los contenidos con más detalle."},
}

# ═══════════════════════════════════════════════════════════════════════════════
# MEJORA 1: IMÁGENES POR ÉPOCA (Wikipedia REST API, cacheado)
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_era_images() -> dict:
    """
    Obtiene la imagen principal de Wikipedia para cada época.
    Solo se ejecuta una vez al arrancar el servidor.
    Si falla la descarga de alguna imagen, la época muestra solo el emoji.
    """
    import urllib.request
    images = {}
    for era_id, meta in ERA_META.items():
        wiki_title = meta.get("wiki","")
        if not wiki_title:
            continue
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
            req = urllib.request.Request(
                url, headers={"User-Agent": "HistoriaViva-EduApp/1.0 (educational)"}
            )
            with urllib.request.urlopen(req, timeout=4) as r:
                data = json.loads(r.read().decode())
            img = data.get("thumbnail", {}).get("source", "")
            if img:
                images[era_id] = img
        except Exception:
            pass
    return images

# ═══════════════════════════════════════════════════════════════════════════════
# MEJORA 3: ESTADÍSTICAS DE CLASE (compartidas entre todas las sesiones)
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_classroom_stats() -> dict:
    """
    Almacén compartido entre todas las sesiones activas del servidor.
    Funciona durante la vida del proceso (una sesión de clase).
    Se reinicia cuando Streamlit se redeploya o se duerme.
    """
    return {
        "questions":    [],   # {era, era_name, level, question, ts}
        "quiz_results": [],   # {era, era_name, level, score, total, ts}
    }

def log_question(era_id: str, era_name: str, level: str, question: str):
    stats = get_classroom_stats()
    stats["questions"].append({
        "era": era_id, "era_name": era_name,
        "level": level, "question": question[:120],
        "ts": datetime.now().strftime("%H:%M"),
    })
    # Limitar a las últimas 200 para no saturar la memoria
    if len(stats["questions"]) > 200:
        stats["questions"] = stats["questions"][-200:]

def log_quiz_result(era_id: str, era_name: str, level: str, score: int, total: int):
    stats = get_classroom_stats()
    stats["quiz_results"].append({
        "era": era_id, "era_name": era_name,
        "level": level, "score": score, "total": total,
        "ts": datetime.now().strftime("%H:%M"),
        "pct": round(score / total * 100) if total else 0,
    })

# ═══════════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def load_all_data():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    with open(os.path.join(data_dir, "index.js"), "r", encoding="utf-8") as f:
        idx_content = f.read()
    idx_match = re.search(r"window\.HV_INDEX\s*=\s*(\[[\s\S]*?\]);", idx_content)
    era_index = json.loads(idx_match.group(1)) if idx_match else []
    eras = {}
    for era_info in era_index:
        eid = era_info["id"]
        fp  = os.path.join(data_dir, f"{eid}.js")
        if not os.path.exists(fp):
            continue
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        start = content.rfind("= {")
        if start == -1:
            continue
        try:
            eras[eid] = json.loads(content[start+2:].rstrip().rstrip(";").rstrip())
        except json.JSONDecodeError:
            pass
    # Pre-compute context strings (zero overhead per question)
    era_contexts = {eid: build_context(data) for eid, data in eras.items()}
    return era_index, eras, era_contexts

# ═══════════════════════════════════════════════════════════════════════════════
# UTILIDADES DE TEXTO
# ═══════════════════════════════════════════════════════════════════════════════
def normalize(text: str) -> str:
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return " ".join(text.split())

def tokens(text: str) -> set:
    return {t for t in normalize(text).split() if len(t) > 2 and t not in STOPWORDS}

def best_faq(question: str, era_data: dict):
    q_norm = normalize(question)
    q_tok  = tokens(question)
    best, best_score = None, 0
    for faq in era_data.get("faqs", []):
        kw_score  = sum(1 for k in faq.get("keywords", []) if normalize(k) in q_norm)
        tok_score = len(q_tok & tokens(faq.get("question", "")))
        score     = kw_score * 2 + tok_score
        if score > best_score:
            best_score, best = score, faq
    return best if best_score >= 3 else None

def faq_answer(faq: dict, level: str) -> str:
    mapping = {"infantil":"infantil","básico":"basic","intermedio":"intermediate","avanzado":"advanced"}
    return faq.get(mapping.get(level,"basic"),"") or faq.get("basic","")

def local_faq_hint(question: str, era_data: dict, level: str) -> str:
    faq = best_faq(question, era_data)
    if faq:
        ans = faq_answer(faq, level)
        if ans:
            return ans
    return ""

# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXTO PARA GEMINI
# ═══════════════════════════════════════════════════════════════════════════════
def build_context(era_data: dict) -> str:
    sections      = era_data.get("sections", {})
    topic_details = era_data.get("topicDetails", {})
    teacher       = era_data.get("teacher", {})
    faqs          = era_data.get("faqs", [])
    parts = []
    if sections:
        parts.append("=== INFORMACIÓN DE TU ÉPOCA (base principal) ===")
        for k, v in sections.items():
            if v: parts.append(f"[{k.upper()}]\n{v}")
    if topic_details:
        parts.append("\n=== DETALLES ESPECÍFICOS POR TEMA ===")
        for k, v in topic_details.items():
            if v: parts.append(f"[{k}]: {v}")
    ideas = teacher.get("ideas_clave", [])
    if ideas:
        parts.append("\n=== IDEAS CLAVE ===\n" + "; ".join(ideas))
    anacs = teacher.get("anacronismos", [])
    if anacs:
        parts.append("\n=== ERRORES HISTÓRICOS A EVITAR ===\n" + "; ".join(anacs))
    if faqs:
        parts.append("\n=== EJEMPLOS DE RESPUESTAS CORRECTAS ===")
        for faq in faqs[:5]:
            parts.append(f"P: {faq.get('question','')}\nR: {faq.get('basic','')[:200]}")
    return "\n\n".join(parts)

# ═══════════════════════════════════════════════════════════════════════════════
# MEJORA 2: MICROFACTS "¿SABÍAS QUE?"
# ═══════════════════════════════════════════════════════════════════════════════
def get_random_microfact(era_data: dict) -> str:
    """
    Devuelve un microfact aleatorio de la base de datos de la época.
    Los microfacts son hechos breves, concretos y sorprendentes.
    """
    mf_dict = era_data.get("microfacts", {})
    all_facts = []
    for facts in mf_dict.values():
        if isinstance(facts, list):
            all_facts.extend(facts)
    if not all_facts:
        return ""
    return random.choice(all_facts)

# ═══════════════════════════════════════════════════════════════════════════════
# GEMINI — CONSTRUCCIÓN DEL CHAT
# ═══════════════════════════════════════════════════════════════════════════════
def _build_gemini_chat(era_data: dict, level: str, history: list,
                       faq_hint: str = "", prebuilt_context: str = ""):
    import google.generativeai as genai
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return None, "⚠️ IA no configurada. Añade GEMINI_API_KEY en los Secrets de Streamlit."
    genai.configure(api_key=api_key)

    level_cfg    = LEVELS[level]
    context_text = prebuilt_context if prebuilt_context else build_context(era_data)
    hint_block   = (
        f"\n\n=== RESPUESTA BASE (reformúlala de forma natural y precisa) ===\n{faq_hint}\n==="
        if faq_hint else ""
    )

    system = f"""Eres {era_data['voz']} del período {era_data['name']} ({era_data['periodo']}).

Responde SIEMPRE en primera persona, como ese personaje histórico que habla con un niño.
Adapta vocabulario y complejidad para alumnos de {level_cfg['age']}.

{context_text}{hint_block}

=== REGLAS ===
1. ROL: Nunca rompas el personaje. Eres esa persona, no un narrador externo.

2. PREGUNTAS ANACRÓNICAS (coches, móviles, internet, aviones, ordenadores, TV...):
   Muestra curiosidad genuina: "¿Qué es eso? Nunca he oído esa palabra..."
   Explica qué se usaba en tu época para lo mismo.

3. NOMBRES Y FECHAS: Si no estás seguro, dilo en personaje:
   "no recuerdo exactamente..." NUNCA inventes nombres o fechas que no estén en tu contexto.

4. TEMAS SENSIBLES (violencia, muerte, represión):
   Responde con honestidad apropiada para niños, sin morbo ni detalle gráfico.

5. LONGITUD: Máximo {level_cfg['max_chars']} caracteres.
   Infantil (3-5 años): máximo 2 frases MUY cortas y simples.
   Básico (6-8 años): frases cortas y concretas, sin tecnicismos.
   Intermedio/Avanzado: puedes añadir contexto, causas y consecuencias.

6. IDIOMA: Siempre en español. Sin asteriscos ni formato markdown."""

    chat_history = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
        for m in history[-8:]
        if m.get("content","").strip()
    ]
    while chat_history and chat_history[-1]["role"] == "user":
        chat_history.pop()

    try:
        model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system)
        chat  = model.start_chat(history=chat_history)
        return chat, None
    except Exception as e:
        return None, f"⚠️ Error configurando la IA: {str(e)[:80]}"

# ═══════════════════════════════════════════════════════════════════════════════
# STREAMING
# ═══════════════════════════════════════════════════════════════════════════════
def stream_gemini(question: str, era_data: dict, level: str, history: list,
                  faq_hint: str = "", prebuilt_context: str = ""):
    chat, error = _build_gemini_chat(era_data, level, history, faq_hint, prebuilt_context)
    if error:
        yield error
        return
    try:
        response = chat.send_message(question, stream=True)
        for chunk in response:
            text = getattr(chunk, "text", None)
            if text:
                yield text
    except Exception as e:
        yield f"\n⚠️ Error: {str(e)[:80]}"

# ═══════════════════════════════════════════════════════════════════════════════
# SUGERENCIAS
# ═══════════════════════════════════════════════════════════════════════════════
def get_suggestions(era_data: dict, level: str, era_id: str = "", n: int = 6) -> list:
    if level == "infantil":
        pool = list(INFANTIL_ERA_SUGGESTIONS.get(era_id, INFANTIL_FALLBACK))
        random.shuffle(pool)
        return pool[:n]
    themes = LEVEL_THEMES.get(level, ["cotidiana","identidad"])
    pool = []
    for faq in era_data.get("faqs", []):
        theme = faq.get("theme","")
        if theme in themes:
            pool.append(f"{THEME_EMOJI.get(theme,'💬')} {faq['question']}")
    random.shuffle(pool)
    return pool[:n]

# ═══════════════════════════════════════════════════════════════════════════════
# CUESTIONARIO
# ═══════════════════════════════════════════════════════════════════════════════
def build_quiz(messages: list, era_data: dict, level: str = "básico") -> list:
    import google.generativeai as genai
    api_key = st.secrets.get("GEMINI_API_KEY","")
    if not api_key:
        return []
    genai.configure(api_key=api_key)

    cfg = QUIZ_CONFIG.get(level, QUIZ_CONFIG["básico"])
    pairs = [
        (messages[i-1]["content"], messages[i]["content"])
        for i in range(1, len(messages))
        if messages[i]["role"] == "assistant" and messages[i-1]["role"] == "user"
    ]
    if len(pairs) < 2:
        return []

    chat_text = ""
    for q, a in pairs[:6]:
        chat_text += f"Alumno: {q}\nPersonaje: {a[:350]}\n\n"

    prompt = f"""Eres experto en educación infantil y primaria especializado en historia.
Conversación entre un alumno y un personaje del {era_data.get('name','esta época')}:

{chat_text}

TAREA: {cfg["instruccion"]}

NORMAS:
- Basa TODAS las preguntas solo en lo que aparece en la conversación.
- Indica exactamente cuál es la opción correcta (copiando el texto exacto).
- Responde ÚNICAMENTE con JSON válido, sin texto adicional ni bloques markdown.

FORMATO JSON EXACTO:
{{
  "preguntas": [
    {{
      "pregunta": "Texto de la pregunta",
      "opciones": ["Opción A", "Opción B", "Opción C"],
      "correcta": "Opción A"
    }}
  ]
}}"""

    try:
        model    = genai.GenerativeModel(model_name="gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw      = re.sub(r"^```[a-z]*\n?","", response.text.strip())
        raw      = re.sub(r"\n?```$","", raw)
        data     = json.loads(raw)
        items    = []
        for p in data.get("preguntas",[]):
            pregunta = p.get("pregunta","").strip()
            opciones = [str(o).strip() for o in p.get("opciones",[]) if str(o).strip()]
            correcta = p.get("correcta","").strip()
            if pregunta and len(opciones) >= 2 and correcta in opciones:
                items.append({"q":pregunta,"options":opciones,"correct":correcta})
        return items[:cfg["n"]]
    except Exception:
        return []

# ═══════════════════════════════════════════════════════════════════════════════
# TEXTO A VOZ
# ═══════════════════════════════════════════════════════════════════════════════
def speak_text(text: str):
    import streamlit.components.v1 as components
    safe = json.dumps(text)
    components.html(
        f"<script>"
        f"window.speechSynthesis&&window.speechSynthesis.cancel();"
        f"var u=new SpeechSynthesisUtterance({safe});"
        f"u.lang='es-ES';u.rate=0.88;u.pitch=1.05;"
        f"window.speechSynthesis&&window.speechSynthesis.speak(u);"
        f"</script>",
        height=0,
    )

def stop_speak():
    import streamlit.components.v1 as components
    components.html("<script>window.speechSynthesis&&window.speechSynthesis.cancel();</script>", height=0)

# ═══════════════════════════════════════════════════════════════════════════════
# ESTADO DE SESIÓN
# ═══════════════════════════════════════════════════════════════════════════════
def init_state(first_era_id: str):
    defaults = {
        "era_id":          first_era_id,
        "level":           "básico",
        "messages":        [],
        "suggestions":     [],
        "pending_q":       None,
        "show_quiz":       False,
        "quiz_items":      [],
        "quiz_answers":    {},
        "quiz_submitted":  False,
        "quiz_current_q":  0,
        "quiz_reviewing":  False,
        "quiz_show_score": False,
        "last_bot_text":   "",
        "last_microfact":  "",
        "big_text":        False,
        "show_welcome":    True,
        "teacher_mode":    False,
        "teacher_authed":  False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS UI
# ═══════════════════════════════════════════════════════════════════════════════
def render_quiz_progress(current: int, total: int):
    dots = "".join(
        f'<span class="quiz-dot {"done" if i<current else "current" if i==current else ""}"></span>'
        for i in range(total)
    )
    st.markdown(
        f'<div class="quiz-progress-bar">Pregunta {current+1} de {total} &nbsp; {dots}</div>',
        unsafe_allow_html=True,
    )

def handle_question(question: str, current_era: dict, level: str,
                    era_meta: dict, prebuilt_context: str = ""):
    """
    Streaming + auto-lectura fluida en Infantil + microfact + log de stats.
    La lectura se dispara DESPUÉS de write_stream (texto completo) → sin cortes.
    """
    ss = st.session_state

    with st.chat_message("user", avatar="🧑‍🎓"):
        st.write(question)

    faq_hint = local_faq_hint(question, current_era, level)

    with st.chat_message("assistant", avatar=era_meta["emoji"]):
        full_text = st.write_stream(
            stream_gemini(question, current_era, level, ss.messages[:-1],
                          faq_hint, prebuilt_context)
        )

    ss.messages.append({"role": "assistant", "content": full_text})
    ss.last_bot_text  = full_text
    ss.last_microfact = get_random_microfact(current_era)

    # Log para panel docente
    log_question(ss.era_id, current_era.get("name",""), level, question)

    # Auto-lectura en Infantil (texto completo → TTS fluido sin cortes)
    if level == "infantil":
        speak_text(full_text)

# ═══════════════════════════════════════════════════════════════════════════════
# PANEL DOCENTE
# ═══════════════════════════════════════════════════════════════════════════════
def render_teacher_panel():
    """
    Vista exclusiva para el docente. Muestra estadísticas de la sesión de clase.
    Accesible con contraseña (configurable en Streamlit Secrets: TEACHER_PASSWORD).
    """
    stats = get_classroom_stats()
    questions    = stats["questions"]
    quiz_results = stats["quiz_results"]

    st.markdown("## 👩‍🏫 Panel Docente — Sesión de hoy")
    st.caption(
        "Las estadísticas se acumulan mientras el servidor está activo. "
        "Se reinician al redesplegar o cuando la app se duerme."
    )

    # ── Resumen numérico ─────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="teacher-stat-card">
          <div class="teacher-stat-title">PREGUNTAS HOY</div>
          <div class="teacher-stat-value">{len(questions)}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="teacher-stat-card">
          <div class="teacher-stat-title">TESTS COMPLETADOS</div>
          <div class="teacher-stat-value">{len(quiz_results)}</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        avg_pct = (
            round(sum(r["pct"] for r in quiz_results) / len(quiz_results))
            if quiz_results else 0
        )
        st.markdown(f"""
        <div class="teacher-stat-card">
          <div class="teacher-stat-title">NOTA MEDIA TESTS</div>
          <div class="teacher-stat-value">{avg_pct}%</div>
        </div>""", unsafe_allow_html=True)

    # ── Preguntas por época ───────────────────────────────────────────────────
    if questions:
        st.markdown("### 🗺️ Preguntas por época")
        from collections import Counter
        era_counts = Counter(q["era_name"] for q in questions)
        # Usar st.bar_chart con un dict simple
        import pandas as pd
        df = pd.DataFrame(
            list(era_counts.items()), columns=["Época","Preguntas"]
        ).sort_values("Preguntas", ascending=False)
        st.bar_chart(df.set_index("Época"))

    # ── Resultados de tests ───────────────────────────────────────────────────
    if quiz_results:
        st.markdown("### 📝 Resultados de tests")
        for r in reversed(quiz_results[-10:]):
            icon = "✅" if r["pct"] == 100 else ("⚠️" if r["pct"] >= 60 else "❌")
            st.markdown(
                f'<div class="teacher-q-row">'
                f'{icon} <b>{r["score"]}/{r["total"]}</b> ({r["pct"]}%) — '
                f'{r["era_name"]} · {LEVELS.get(r["level"],{}).get("label","")}'
                f'<div class="teacher-q-meta">🕐 {r["ts"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Últimas preguntas ─────────────────────────────────────────────────────
    if questions:
        st.markdown("### 💬 Últimas preguntas")
        for q in reversed(questions[-15:]):
            era_emoji = ERA_META.get(q["era"], {}).get("emoji", "🏛️")
            st.markdown(
                f'<div class="teacher-q-row">'
                f'{era_emoji} <em>"{q["question"]}"</em>'
                f'<div class="teacher-q-meta">'
                f'🕐 {q["ts"]} · {q["era_name"]} · {LEVELS.get(q["level"],{}).get("label","")}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    # ── Exportar ─────────────────────────────────────────────────────────────
    if questions or quiz_results:
        st.markdown("---")
        export = f"HISTORIA VIVA — Resumen sesión {datetime.now().strftime('%d/%m/%Y')}\n\n"
        export += f"Preguntas totales: {len(questions)}\n"
        export += f"Tests completados: {len(quiz_results)}\n"
        if quiz_results:
            export += f"Nota media: {avg_pct}%\n"
        export += "\n--- PREGUNTAS ---\n"
        for q in questions:
            export += f"[{q['ts']}] {q['era_name']} ({q['level']}): {q['question']}\n"
        export += "\n--- TESTS ---\n"
        for r in quiz_results:
            export += f"[{r['ts']}] {r['era_name']} ({r['level']}): {r['score']}/{r['total']} ({r['pct']}%)\n"
        st.download_button(
            "📥 Exportar resumen de clase",
            data=export,
            file_name=f"historia_viva_clase_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )

    st.markdown("---")
    if st.button("← Volver a la app"):
        st.session_state.teacher_mode = False
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# APP PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    era_index, eras, era_contexts = load_all_data()
    if not era_index:
        st.error("No se encontraron datos.")
        return

    init_state(era_index[0]["id"])
    ss          = st.session_state
    current_era = eras.get(ss.era_id, {})
    level       = ss.level
    era_meta    = ERA_META.get(ss.era_id, {"emoji":"🏛️","color":"#5c35d9","bg":"#f3efff"})
    era_images  = load_era_images()   # cacheado, no bloquea
    current_context = era_contexts.get(ss.era_id, "")

    if ss.big_text:
        st.markdown("<style>html{font-size:18px}</style>", unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # PANTALLA DE BIENVENIDA
    # ──────────────────────────────────────────────────────────────────────────
    if ss.show_welcome:
        st.markdown("""
        <div class="welcome-container">
          <div class="bounce" style="font-size:4rem;margin-bottom:10px;">🏛️</div>
          <div class="welcome-title">¡Historia Viva!</div>
          <div class="welcome-sub">Viaja al pasado y habla con sus protagonistas.<br>¡Hazles todas las preguntas que quieras!</div>
          <div class="welcome-steps">
            <div class="welcome-step"><div class="welcome-step-icon">🗺️</div><div class="welcome-step-text"><b>1.</b> Elige una época histórica</div></div>
            <div class="welcome-step"><div class="welcome-step-icon">📚</div><div class="welcome-step-text"><b>2.</b> Elige tu curso o edad</div></div>
            <div class="welcome-step"><div class="welcome-step-icon">💬</div><div class="welcome-step-text"><b>3.</b> ¡Pregunta lo que quieras!</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        _, col_btn, _ = st.columns([2,2,2])
        with col_btn:
            if st.button("¡Empezar! 🚀", type="primary", use_container_width=True):
                ss.show_welcome = False
                st.rerun()
        return

    # ──────────────────────────────────────────────────────────────────────────
    # PANEL DOCENTE (vista dedicada)
    # ──────────────────────────────────────────────────────────────────────────
    if ss.teacher_mode:
        render_teacher_panel()
        return

    # ──────────────────────────────────────────────────────────────────────────
    # BARRA LATERAL
    # ──────────────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div style="font-size:1.5rem;font-weight:900;color:#5c35d9;text-align:center;padding:10px 0 4px;">🏛️ Historia Viva</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:.82rem;color:#9e9e9e;text-align:center;margin-bottom:4px;">Habla con el pasado</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**🗺️ Elige una época**")
        cols_era = st.columns(2)
        for i, era_info in enumerate(era_index):
            eid  = era_info["id"]
            meta = ERA_META.get(eid, {"emoji":"🏛️"})
            with cols_era[i % 2]:
                if st.button(
                    f"{meta['emoji']}\n{era_info['name']}",
                    key=f"era_{eid}",
                    use_container_width=True,
                    type="primary" if eid == ss.era_id else "secondary",
                    help=era_info["periodo"],
                ):
                    if eid != ss.era_id:
                        ss.era_id, ss.messages, ss.suggestions = eid, [], []
                        ss.show_quiz, ss.last_bot_text = False, ""
                        ss.quiz_current_q, ss.quiz_reviewing = 0, False
                        ss.quiz_show_score = False
                        ss.last_microfact  = ""
                        st.rerun()

        st.markdown("---")
        st.markdown("**📚 Elige tu curso**")
        new_level = st.radio(
            "nivel", options=list(LEVELS.keys()),
            format_func=lambda x: LEVELS[x]["label"],
            index=list(LEVELS.keys()).index(level),
            label_visibility="collapsed",
        )
        if new_level != level:
            ss.level, ss.messages, ss.suggestions = new_level, [], []
            ss.show_quiz, ss.quiz_current_q = False, 0
            ss.quiz_reviewing, ss.quiz_show_score = False, False
            ss.last_microfact = ""
            st.rerun()

        st.markdown("---")
        st.markdown("**🛠️ Herramientas**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💡 Sugerencia", use_container_width=True):
                pool = get_suggestions(current_era, level, ss.era_id, 10)
                if pool:
                    ss.pending_q = re.sub(r"^[^\w¿¡]+","",random.choice(pool)).strip()
                    st.rerun()
        with c2:
            if st.button("🔄 Reiniciar", use_container_width=True):
                ss.messages, ss.suggestions = [], []
                ss.show_quiz, ss.last_bot_text = False, ""
                ss.quiz_current_q, ss.quiz_reviewing = 0, False
                ss.quiz_show_score, ss.last_microfact = False, ""
                st.rerun()

        if ss.last_bot_text:
            c3, c4 = st.columns(2)
            with c3:
                if st.button("🔊 Leer", use_container_width=True):
                    speak_text(ss.last_bot_text)
            with c4:
                if st.button("⏹ Parar", use_container_width=True):
                    stop_speak()

        fl = "🔡 Normal" if ss.big_text else "🔠 Letra grande"
        if st.button(fl, use_container_width=True):
            ss.big_text = not ss.big_text
            st.rerun()

        if len(ss.messages) >= 4:
            if st.button("📝 Test final", use_container_width=True, type="primary"):
                with st.spinner("Generando cuestionario…"):
                    ss.quiz_items = build_quiz(ss.messages, current_era, level)
                ss.quiz_answers    = {}
                ss.quiz_submitted  = False
                ss.quiz_current_q  = 0
                ss.quiz_reviewing  = False
                ss.quiz_show_score = False
                ss.show_quiz       = True
                st.rerun()

        if ss.messages:
            chat_export = f"Historia Viva · {current_era.get('name','')}\nNivel: {LEVELS[level]['label']}\n\n"
            for msg in ss.messages:
                role = "Alumno" if msg["role"] == "user" else current_era.get("voz","Personaje")
                chat_export += f"{role}:\n{msg['content']}\n\n"
            st.download_button("📥 Exportar chat", data=chat_export,
                               file_name=f"historia_{ss.era_id}.txt",
                               mime="text/plain", use_container_width=True)

        st.markdown("---")
        if st.button("🏠 Inicio", use_container_width=True):
            ss.show_welcome = True
            st.rerun()

        # ── Acceso docente ────────────────────────────────────────────────────
        st.markdown("---")
        if not ss.teacher_authed:
            with st.expander("🔑 Modo Docente"):
                pwd = st.text_input("Contraseña docente", type="password",
                                    key="teacher_pwd_input",
                                    placeholder="Contraseña…")
                if st.button("Entrar", key="teacher_login"):
                    correct = st.secrets.get("TEACHER_PASSWORD", "docente")
                    if pwd == correct:
                        ss.teacher_authed = True
                        ss.teacher_mode   = True
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta.")
                st.caption("Contraseña por defecto: **docente**\n\nCámbiala añadiendo `TEACHER_PASSWORD` en los Secrets de Streamlit.")
        else:
            if st.button("👩‍🏫 Panel Docente", use_container_width=True, type="primary"):
                ss.teacher_mode = True
                st.rerun()

    # ──────────────────────────────────────────────────────────────────────────
    # ÁREA PRINCIPAL
    # ──────────────────────────────────────────────────────────────────────────

    # ── MEJORA 1: Hero con imagen ─────────────────────────────────────────────
    if current_era:
        color = era_meta["color"]
        bg    = era_meta["bg"]
        emoji = era_meta["emoji"]
        img_url = era_images.get(ss.era_id, "")

        era_name_safe = current_era.get('name', '')
        img_html = (
            f'<img src="{img_url}" class="hero-img" onerror="this.style.display=none" alt="{era_name_safe}" />'
            if img_url else ""
        )

        st.markdown(f"""
        <div class="hero-card" style="background:{bg}; border:2px solid {color}40;">
          {img_html}
          <div class="hero-content">
            <span class="hero-avatar">{emoji}</span>
            <div class="hero-era-name" style="color:{color};">{current_era.get('name','')}</div>
            <div class="hero-period">{current_era.get('periodo','')}</div>
            <span class="hero-badge" style="background:{color}22;color:{color};">{LEVELS[level]['label']}</span>
            <div class="hero-voice" style="border-left-color:{color};">
              💬 <em>{current_era.get('apertura','')}</em>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # CUESTIONARIO
    # ──────────────────────────────────────────────────────────────────────────
    if ss.show_quiz:
        if not ss.quiz_items:
            st.warning("⚠️ No se pudo generar el cuestionario. Asegúrate de haber hecho al menos 2 preguntas e inténtalo de nuevo.")
            ss.show_quiz = False

        elif ss.quiz_submitted and ss.get("quiz_show_score", False):
            total_q   = len(ss.quiz_items)
            correct_n = sum(1 for i, it in enumerate(ss.quiz_items)
                            if ss.quiz_answers.get(i) == it["correct"])
            fb   = QUIZ_FEEDBACK.get(level, QUIZ_FEEDBACK["básico"])
            pct  = correct_n / total_q if total_q else 0
            msg  = fb["perfect"] if pct==1.0 else (fb["good"] if pct>=0.6 else fb["low"])
            big_emoji = "🌟" if pct==1.0 else ("😊" if pct>=0.6 else "📚")

            # Log resultado al panel docente
            log_quiz_result(ss.era_id, current_era.get("name",""), level, correct_n, total_q)

            st.markdown(f"""
            <div class="quiz-score-screen">
              <span class="quiz-score-big">{big_emoji}</span>
              <div class="quiz-score-msg">{msg}</div>
              <div class="quiz-score-badge">{correct_n} de {total_q} correctas</div>
            </div>
            """, unsafe_allow_html=True)

            col_rev, col_close = st.columns([2,1])
            with col_rev:
                if st.button("📖 Ver mis respuestas", type="primary", use_container_width=True):
                    ss.quiz_show_score = False
                    ss.quiz_reviewing  = True
                    ss.quiz_current_q  = 0
                    st.rerun()
            with col_close:
                if st.button("✖ Cerrar", use_container_width=True):
                    ss.show_quiz       = False
                    ss.quiz_show_score = False
                    ss.quiz_current_q  = 0
                    st.rerun()

        else:
            level_titles = {
                "infantil":"🌟 ¡Vamos a jugar! ¿Qué recuerdas?",
                "básico":"📝 Test de repaso",
                "intermedio":"📝 Cuestionario final",
                "avanzado":"📝 Cuestionario final",
            }
            st.markdown(f"### {level_titles.get(level,'📝 Test')}")
            total = len(ss.quiz_items)

            if level in STEPWISE_QUIZ_LEVELS:
                idx  = min(ss.quiz_current_q, total - 1)
                item = ss.quiz_items[idx]
                render_quiz_progress(idx, total)
                st.markdown(
                    f'<div class="quiz-question-card"><div class="quiz-q-text">{item["q"]}</div></div>',
                    unsafe_allow_html=True,
                )
                if ss.quiz_reviewing:
                    ok    = ss.quiz_answers.get(idx) == item["correct"]
                    ans   = ss.quiz_answers.get(idx, "—")
                    short = item["correct"][:160] + ("…" if len(item["correct"]) > 160 else "")
                    css   = "quiz-reveal-ok" if ok else "quiz-reveal-bad"
                    icon  = "✅" if ok else "❌"
                    st.radio("tu_respuesta", options=item["options"],
                             index=item["options"].index(ans) if ans in item["options"] else 0,
                             key=f"qz_rev_{idx}", disabled=True, label_visibility="collapsed")
                    st.markdown(f'<div class="{css}">{icon} Respuesta correcta: <b>{short}</b></div>',
                                unsafe_allow_html=True)
                    cp, cn = st.columns([1,1])
                    with cp:
                        if idx > 0 and st.button("← Anterior", key="rev_prev"):
                            ss.quiz_current_q -= 1; st.rerun()
                    with cn:
                        if idx < total - 1:
                            if st.button("Siguiente →", key="rev_next", type="primary"):
                                ss.quiz_current_q += 1; st.rerun()
                        else:
                            if st.button("Cerrar test", key="rev_close"):
                                ss.show_quiz, ss.quiz_reviewing = False, False
                                ss.quiz_current_q = 0; st.rerun()
                else:
                    answer = st.radio(f"q{idx}", options=item["options"],
                                      key=f"qz_{idx}", label_visibility="collapsed")
                    ss.quiz_answers[idx] = answer
                    cp, cn = st.columns([1,1])
                    with cp:
                        if idx > 0 and st.button("← Anterior", key="q_prev"):
                            ss.quiz_current_q -= 1; st.rerun()
                    with cn:
                        if idx < total - 1:
                            if st.button("Siguiente →", key="q_next", type="primary"):
                                ss.quiz_current_q += 1; st.rerun()
                        else:
                            if st.button("✅ Ver resultados", key="q_submit", type="primary"):
                                ss.quiz_submitted  = True
                                ss.quiz_show_score = True
                                ss.quiz_current_q  = 0; st.rerun()
            else:
                st.caption("Responde todas las preguntas y luego pulsa Corregir.")
                for i, item in enumerate(ss.quiz_items):
                    render_quiz_progress(i, total)
                    st.markdown(
                        f'<div class="quiz-question-card"><div class="quiz-q-text">{item["q"]}</div></div>',
                        unsafe_allow_html=True,
                    )
                    answer = st.radio(f"q{i}", options=item["options"],
                                      key=f"qz_{i}", disabled=ss.quiz_submitted,
                                      label_visibility="collapsed")
                    ss.quiz_answers[i] = answer
                    if ss.quiz_submitted:
                        ok    = ss.quiz_answers.get(i) == item["correct"]
                        short = item["correct"][:160] + ("…" if len(item["correct"]) > 160 else "")
                        css   = "quiz-reveal-ok" if ok else "quiz-reveal-bad"
                        icon  = "✅" if ok else "❌"
                        st.markdown(f'<div class="{css}">{icon} Respuesta correcta: <b>{short}</b></div>',
                                    unsafe_allow_html=True)
                    st.markdown("---")
                if not ss.quiz_submitted:
                    ca, cb = st.columns([2,1])
                    with ca:
                        if st.button("✅ Corregir respuestas", type="primary"):
                            ss.quiz_submitted  = True
                            ss.quiz_show_score = True; st.rerun()
                    with cb:
                        if st.button("Cerrar"):
                            ss.show_quiz = False; st.rerun()
                else:
                    if st.button("✖ Cerrar test"):
                        ss.show_quiz, ss.quiz_reviewing = False, False; st.rerun()

    # ── Mensajes del chat ─────────────────────────────────────────────────────
    for msg in ss.messages:
        avatar = "🧑‍🎓" if msg["role"] == "user" else era_meta["emoji"]
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    # ── MEJORA 2: ¿Sabías que? (después del último mensaje del personaje) ─────
    if ss.last_microfact and ss.messages and ss.messages[-1]["role"] == "assistant":
        st.markdown(
            f'<div class="microfact-card">'
            f'<span class="microfact-icon">💡</span>'
            f'<span class="microfact-text"><b>¿Sabías que...?</b> {ss.last_microfact}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Sugerencias (chat vacío) ───────────────────────────────────────────────
    if not ss.messages:
        if not ss.suggestions:
            ss.suggestions = get_suggestions(current_era, level, ss.era_id)
        if ss.suggestions:
            st.markdown('<div class="sug-label">💬 ¿Sobre qué quieres preguntar?</div>',
                        unsafe_allow_html=True)
            cols = st.columns(2)
            for idx, sug in enumerate(ss.suggestions[:6]):
                with cols[idx % 2]:
                    if st.button(sug, key=f"sug_{idx}", use_container_width=True):
                        ss.pending_q = re.sub(r"^[^\w¿¡]+","",sug).strip()
                        st.rerun()

    if ss.pending_q:
        question     = ss.pending_q
        ss.pending_q = None
        ss.messages.append({"role":"user","content":question})
        handle_question(question, current_era, level, era_meta, current_context)
        st.rerun()

    placeholder = (
        f"Pregunta a {current_era.get('voz','el personaje histórico')}…"
        if current_era else "Elige una época para empezar…"
    )
    if prompt := st.chat_input(placeholder):
        ss.messages.append({"role":"user","content":prompt})
        handle_question(prompt, current_era, level, era_meta, current_context)
        st.rerun()


if __name__ == "__main__":
    main()
