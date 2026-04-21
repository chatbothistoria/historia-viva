"""
Historia Viva · Infantil y Primaria  —  v7
─────────────────────────────────────────
Mejoras v7:
  1. Imágenes por época (Wikipedia REST API, cacheadas al arrancar)
  2. Panel "¿Sabías que?" con microfacts de la base de datos
  3. Panel docente con estadísticas de clase (sin base de datos externa)
"""

import streamlit as st
import json, re, os, random
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
    "paleolitico":            {"emoji":"🦣","color":"#8B6347","bg":"#fdf3ec"},
    "neolitico":              {"emoji":"🌾","color":"#5A8A3C","bg":"#f0f9ec"},
    "edad_metales":           {"emoji":"⚒️","color":"#B5830A","bg":"#fdf6e3"},
    "egipto":                 {"emoji":"🏺","color":"#C9960C","bg":"#fef9e7"},
    "grecia":                 {"emoji":"🏛️","color":"#2471A3","bg":"#ebf5fb"},
    "roma":                   {"emoji":"🦅","color":"#A93226","bg":"#fdedec"},
    "edad_media":             {"emoji":"🏰","color":"#6C3483","bg":"#f5eef8"},
    "america_precolombina":   {"emoji":"🌽","color":"#1E8449","bg":"#eafaf1"},
    "renacimiento":           {"emoji":"🎨","color":"#D35400","bg":"#fef5ec"},
    "revolucion_francesa":    {"emoji":"⚖️","color":"#1A5276","bg":"#eaf0fb"},
    "revolucion_industrial":  {"emoji":"🏭","color":"#4D5656","bg":"#f2f3f4"},
    "primera_guerra_mundial": {"emoji":"🕊️","color":"#6E7E5A","bg":"#f2f4ef"},
    "guerra_civil_espanola":  {"emoji":"📜","color":"#7E5109","bg":"#fdf0e3"},
    "segunda_guerra_mundial": {"emoji":"🌍","color":"#1B2631","bg":"#eaecee"},
    "dictadura_franquista":   {"emoji":"📢","color":"#78281F","bg":"#fdedec"},
    "democracia_actual":      {"emoji":"🗳️","color":"#117A65","bg":"#e8f8f5"},
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
/* Eliminar el hueco que deja el label oculto del st.radio */
div[data-testid="stRadio"] > label:first-child {
  display: none !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}
/* Hero card con imagen */
.hero-card {
  border-radius: 22px; overflow: hidden; margin-bottom: 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,.10); position: relative;
}
.hero-img {
  width: 100%; height: 200px; object-fit: cover;
  object-position: center center;
  display: block; filter: brightness(.72);
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

# ── Textos de apertura del personaje adaptados al nivel (4 × 16 épocas) ──────
# Fuente de verdad en app.py para evitar dependencia de caché de archivos JS.
APERTURA_NIVEL = {
    "paleolitico": {
        "infantil":   "¡Hola! Yo vivo hace muchísimo tiempo. ¿Me preguntas cómo comemos y dónde dormimos?",
        "basico":     "¡Hola! Soy una persona del Paleolítico, la época más antigua de todas. Cazamos animales, recogemos frutos y nos movemos de un sitio a otro. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo en el Paleolítico, hace miles y miles de años. Mi grupo se desplaza continuamente para encontrar comida y refugio. No tenemos casas fijas ni cultivos. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Soy una persona del Paleolítico, la etapa más larga de la historia humana. Mi vida depende del entorno: cazamos, pescamos y recolectamos. No vivimos en cuevas permanentes como se cree; elegimos el refugio según la estación. ¿Qué quieres saber sobre cómo sobrevivimos?",
    },
    "neolitico": {
        "infantil":   "¡Hola! Tenemos animales y plantamos comida. ¿Quieres saber cómo vivimos?",
        "basico":     "¡Hola! Soy del Neolítico. Aprendimos a plantar trigo y a cuidar ovejas y vacas. Ya no tenemos que ir tan lejos a buscar comida. ¿Qué quieres preguntarme?",
        "intermedio": "Hola. Soy del Neolítico. Todo cambió cuando aprendimos a cultivar la tierra y a domesticar animales. Podemos quedarnos en el mismo sitio, construir casas y guardar comida. ¿Qué te gustaría saber?",
        "avanzado":   "Hola. Vivo en el Neolítico, una época de grandes cambios. La agricultura y la ganadería transformaron por completo la vida humana: surgieron los poblados, la división del trabajo y las primeras desigualdades sociales. ¿Qué te gustaría preguntarme?",
    },
    "edad_metales": {
        "infantil":   "¡Hola! Hacemos cosas con metal, como espadas y herramientas. ¿Me preguntas cómo?",
        "basico":     "¡Hola! En mi época aprendimos a fundir metales como el cobre y el hierro para hacer herramientas y armas. Somos mucho más fuertes que antes. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo en la Edad de los Metales. Primero usamos el cobre, luego el bronce y después el hierro. Cada metal trajo nuevas herramientas, nuevas armas y cambios en cómo nos organizamos. ¿Qué quieres preguntarme?",
        "avanzado":   "Hola. Vivo en la Edad de los Metales, una época de profundas transformaciones. El dominio del metal no solo mejoró nuestras herramientas: también cambió el comercio, las relaciones de poder y la forma de hacer la guerra. ¿Qué te gustaría explorar?",
    },
    "egipto": {
        "infantil":   "¡Hola! Yo vivo cerca de un río muy grande que se llama el Nilo. ¡Pregúntame lo que quieras!",
        "basico":     "¡Hola! Vivo en el antiguo Egipto, junto al río Nilo. Tenemos pirámides enormes, un faraón que manda en todo y muchos dioses. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo en el antiguo Egipto. El Nilo lo es todo para nosotros: nos da agua, comida y tierra fértil. El faraón es nuestro dios y rey a la vez. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Soy una persona del antiguo Egipto. Nuestra civilización lleva miles de años junto al Nilo, que marca el ritmo de la agricultura y la vida entera. El faraón concentra el poder político y religioso, pero no todos vivimos igual. ¿Sobre qué quieres reflexionar?",
    },
    "grecia": {
        "infantil":   "¡Hola! Yo vivo en Grecia, junto al mar. Tenemos muchos dioses y me gusta mucho jugar. ¿Me preguntas?",
        "basico":     "¡Hola! Vivo en la antigua Grecia. Tenemos muchos dioses, los Juegos Olímpicos y ciudades muy importantes como Atenas. ¿Qué quieres saber?",
        "intermedio": "Hola. Soy del mundo griego antiguo. Vivimos en ciudades-estado llamadas polis, cada una con sus propias leyes. En Atenas inventamos algo nuevo: la democracia. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Vivo en la antigua Grecia, una civilización que sentó muchas bases del mundo occidental: la democracia, la filosofía, el teatro, los Juegos Olímpicos. Pero no todo era perfecto: había esclavitud y las mujeres no tenían los mismos derechos. ¿Qué quieres explorar?",
    },
    "roma": {
        "infantil":   "¡Hola! Yo vivo en Roma. Somos muy poderosos y tenemos un jefe que se llama el emperador. ¿Qué quieres saber?",
        "basico":     "¡Hola! Vivo en el Imperio Romano. Tenemos calzadas, acueductos, baños públicos y un ejército muy fuerte. ¿Qué quieres preguntarme?",
        "intermedio": "Hola. Soy romano. Nuestro imperio es enorme y llega a muchos países. Construimos carreteras, acueductos y ciudades por todas partes. El emperador manda, pero no todos vivimos igual. ¿Qué te gustaría saber?",
        "avanzado":   "Hola. Soy del Imperio Romano, uno de los más extensos y duraderos de la historia. Nuestra organización política, nuestras leyes y nuestra ingeniería siguen influyendo hoy. Pero el Imperio también se sostuvo sobre la esclavitud y la conquista. ¿Sobre qué quieres reflexionar?",
    },
    "edad_media": {
        "infantil":   "¡Hola! Yo vivo cerca de un castillo grande. Hay un rey que manda en todo. ¿Me preguntas cómo vivimos?",
        "basico":     "¡Hola! Vivo en la Edad Media. Hay castillos, caballeros con armadura, reyes y monasterios. La mayoría trabajamos en el campo. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo en la Edad Media. La sociedad se organiza en el feudalismo: los señores tienen tierras y los campesinos las trabajan a cambio de protección. La Iglesia tiene mucho poder. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Soy del Medievo, una época larga y muy variada. El feudalismo estructura la sociedad, la Iglesia guía la vida espiritual y política, y poco a poco nacen las ciudades y los gremios. Es una época de desigualdades, pero también de arte, fe y cambio. ¿Sobre qué quieres reflexionar?",
    },
    "america_precolombina": {
        "infantil":   "¡Hola! Yo vivo en un lugar muy lejos, con pirámides y selvas. ¿Quieres saber cómo es mi vida?",
        "basico":     "¡Hola! Vivo en América antes de que llegaran los europeos. Tenemos pirámides, cacao, maíz y un calendario propio. ¿Qué quieres preguntarme?",
        "intermedio": "Hola. Vivo en América antes de la llegada de los europeos. Existen grandes civilizaciones como la maya, la azteca y la inca, cada una con su organización, su arte y su religión. ¿Qué te gustaría saber?",
        "avanzado":   "Hola. Vivo en la América precolombina, un continente con civilizaciones avanzadas, complejas y diversas. Los mayas, aztecas e incas desarrollaron sistemas de escritura, astronomía, arquitectura y comercio. Su mundo cambió radicalmente con la llegada europea. ¿Qué quieres explorar?",
    },
    "renacimiento": {
        "infantil":   "¡Hola! En mi época pintamos cuadros muy bonitos y los barcos viajan muy lejos. ¿Me preguntas algo?",
        "basico":     "¡Hola! Vivo en el Renacimiento. Los artistas pintan cuadros increíbles, los barcos descubren nuevas tierras y se inventa la imprenta. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo en el Renacimiento, una época de grandes cambios. El arte, la ciencia y el pensamiento florecen en Europa. La imprenta permite que las ideas se extiendan mucho más rápido. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Vivo en el Renacimiento, una época que mira hacia el ser humano como centro del mundo. El arte, la ciencia, la filosofía y los viajes de exploración cambian la visión europea del universo. Pero estos avances no llegan a todos por igual. ¿Sobre qué quieres reflexionar?",
    },
    "revolucion_francesa": {
        "infantil":   "¡Hola! En mi ciudad hay mucho ruido y la gente está enfadada. ¿Quieres saber por qué?",
        "basico":     "¡Hola! Vivo en la Revolución Francesa. El pueblo está muy enfadado con el rey porque pasa mucha hambre. Todo está cambiando muy rápido. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo en la Revolución Francesa. El pueblo se levantó contra el rey Luis XVI porque había mucha desigualdad y hambre. Queremos libertad, igualdad y fraternidad. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Vivo en la Revolución Francesa, uno de los momentos más decisivos de la historia moderna. La monarquía absoluta cae, se proclaman los derechos del hombre y la soberanía popular. Pero la Revolución también trajo el Terror y la guerra. Sus ideales siguen vivos hoy. ¿Qué quieres explorar?",
    },
    "revolucion_industrial": {
        "infantil":   "¡Hola! En mi época hay fábricas grandes y trenes que van muy rápido. ¿Me preguntas cómo es esto?",
        "basico":     "¡Hola! Vivo en la Revolución Industrial. Las máquinas hacen ahora el trabajo que antes hacían personas. Hay muchas fábricas y las ciudades crecen mucho. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo en la Revolución Industrial. Las máquinas de vapor cambian todo: la producción, el transporte y la vida en las ciudades. Pero muchos obreros trabajan en condiciones muy duras. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Vivo en la Revolución Industrial, un período de transformación radical. La máquina de vapor, el ferrocarril y las fábricas redefinen la economía y la sociedad. Nacen la burguesía y el proletariado, y con ellos los primeros movimientos obreros. ¿Sobre qué quieres reflexionar?",
    },
    "primera_guerra_mundial": {
        "infantil":   "¡Hola! En mi época hay una guerra muy grande en muchos países. Es triste. ¿Me preguntas cómo vivimos?",
        "basico":     "¡Hola! Vivo en la Primera Guerra Mundial. Es una guerra enorme entre muchos países. Hay trincheras, miedo y mucha gente sufre. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo en la Primera Guerra Mundial. Es una guerra diferente a todas las anteriores: hay trincheras, gas venenoso y millones de muertos. En casa, la vida también cambia mucho. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Vivo en la Primera Guerra Mundial, el primer conflicto de escala verdaderamente global. Las alianzas entre naciones, el imperialismo y el nacionalismo desencadenaron una guerra devastadora que cambió el mapa de Europa y el mundo. ¿Qué quieres explorar?",
    },
    "guerra_civil_espanola": {
        "infantil":   "¡Hola! En España hay una guerra y mucha gente tiene miedo. ¿Me preguntas cómo vivimos los niños?",
        "basico":     "¡Hola! Vivo en la Guerra Civil Española. Hay dos bandos peleando y muchas familias tienen que huir de su casa. Es una época muy difícil. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo en la Guerra Civil Española, un conflicto que divide el país en dos. Muchas familias sufren, hay bombardeos y miles de personas tienen que exiliarse. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Vivo en la Guerra Civil Española, un conflicto que enfrentó a republicanos y nacionalistas entre 1936 y 1939. Fue una guerra de ideologías, con intervención extranjera y consecuencias que marcaron a generaciones. La memoria de ese tiempo sigue siendo importante hoy. ¿Qué quieres explorar?",
    },
    "segunda_guerra_mundial": {
        "infantil":   "¡Hola! Hay una guerra en todo el mundo y es muy difícil. ¿Quieres saber cómo vivimos?",
        "basico":     "¡Hola! Vivo en la Segunda Guerra Mundial. Es la guerra más grande que ha habido nunca. Hay bombardeos, mucho miedo y muchas familias separadas. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo en la Segunda Guerra Mundial. Es un conflicto enorme que afecta a casi todo el mundo. El nazismo, el Holocausto y los bombardeos marcan esta época de forma terrible. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Vivo en la Segunda Guerra Mundial, el conflicto más mortífero de la historia. El nazismo, el Holocausto, los bombardeos masivos y las bombas atómicas definen una época de horror. De ella nació la ONU y la Declaración Universal de Derechos Humanos. ¿Qué quieres explorar?",
    },
    "dictadura_franquista": {
        "infantil":   "¡Hola! En España manda una sola persona que se llama Franco. ¿Me preguntas cómo vivimos?",
        "basico":     "¡Hola! Vivo en la época de Franco, en España. Solo hay un jefe que manda en todo. No podemos decir lo que pensamos libremente. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo bajo la dictadura del general Franco en España. No hay elecciones, no hay libertad de prensa y quien se opone al régimen puede ser detenido. La vida cotidiana está marcada por el miedo y el control. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Vivo en la España franquista, una dictadura que duró casi cuarenta años. La represión política, la censura, el control de la Iglesia y la falta de libertades definieron la vida de varias generaciones. Entender este período es fundamental para entender la España de hoy. ¿Qué quieres explorar?",
    },
    "democracia_actual": {
        "infantil":   "¡Hola! Vivimos en un país donde todos podemos decir lo que pensamos. ¿Me preguntas cómo funciona?",
        "basico":     "¡Hola! Vivo en la democracia española. Los ciudadanos votamos para elegir a nuestros gobernantes y tenemos derechos que hay que cuidar. ¿Qué quieres saber?",
        "intermedio": "Hola. Vivo en la democracia actual de España, que empezó tras la muerte de Franco. Tenemos una Constitución, elecciones libres y derechos fundamentales. Pero la democracia no se mantiene sola: hay que participar y defenderla. ¿Qué te gustaría preguntarme?",
        "avanzado":   "Hola. Vivo en la democracia española, fruto de una Transición que transformó el país tras cuarenta años de dictadura. Tenemos separación de poderes, derechos fundamentales y libertad de expresión. Pero la democracia es un sistema que se construye cada día y tiene retos abiertos. ¿Sobre qué quieres reflexionar?",
    },
}

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
# IMÁGENES LOCALES POR ÉPOCA
# Archivos en images/{era_id}.jpg — 800×300 px, mismo tamaño para todas.
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_era_images() -> dict:
    """
    Carga las imágenes locales al arrancar y las cachea como bytes raw.
    Se sirven con st.image() — método nativo de Streamlit, sin restricciones
    de Content-Security-Policy ni problemas de data URI en Streamlit Cloud.
    """
    images = {}
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for era_id in ERA_META:
        img_path = os.path.join(base_dir, "images", f"{era_id}.jpg")
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                images[era_id] = f.read()
    return images

# ═══════════════════════════════════════════════════════════════════════════════
# MEJORA 3: ESTADÍSTICAS DE CLASE (compartidas entre todas las sesiones)
# ═══════════════════════════════════════════════════════════════════════════════
# Límites REALES verificados en AI Studio para esta cuenta (abril 2026):
#   RPD (peticiones/día):  20  → límite interno: 18 (margen de seguridad de 2)
#   RPM (peticiones/min):  10
#   TPM (tokens/minuto):   250.000
# IMPORTANTE: estos límites son específicos de esta cuenta y proyecto.
# Comprueba los tuyos en: aistudio.google.com/rate-limit
GEMINI_DAILY_LIMIT = 18

@st.cache_resource
def get_classroom_stats() -> dict:
    """
    Almacén compartido entre todas las sesiones activas del servidor.
    Funciona durante la vida del proceso (una sesión de clase).
    Se reinicia cuando Streamlit se redeploya o se duerme.
    """
    return {
        "questions":       [],   # {era, era_name, level, question, ts}
        "quiz_results":    [],   # {era, era_name, level, score, total, ts}
        "gemini_calls":    0,    # contador diario de llamadas a Gemini
        "gemini_date":     "",   # fecha del contador (reinicia a medianoche)
    }

def gemini_calls_today() -> int:
    """Devuelve el número de llamadas a Gemini hechas hoy (se resetea a medianoche)."""
    stats = get_classroom_stats()
    today = datetime.now().strftime("%Y-%m-%d")
    if stats["gemini_date"] != today:
        stats["gemini_calls"] = 0
        stats["gemini_date"]  = today
    return stats["gemini_calls"]

def increment_gemini_calls():
    """Incrementa el contador diario de llamadas a Gemini."""
    stats = get_classroom_stats()
    today = datetime.now().strftime("%Y-%m-%d")
    if stats["gemini_date"] != today:
        stats["gemini_calls"] = 0
        stats["gemini_date"]  = today
    stats["gemini_calls"] += 1

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

# (Motor local de FAQ eliminado — causaba falsos positivos en el matching
#  y devolvía respuestas de temas erróneos. Gemini recibe el contexto
#  completo de la época y responde directamente con precisión.)

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
# Qué categorías de microfacts son apropiadas para cada nivel de edad
MICROFACT_THEMES_BY_LEVEL = {
    "infantil":   ["cotidiana", "infancia"],
    "básico":     ["cotidiana", "infancia", "trabajo", "creencias"],
    "intermedio": ["cotidiana", "infancia", "trabajo", "creencias",
                   "poder", "conflicto", "fuentes", "comparacion"],
    "avanzado":   None,  # None = todos los temas disponibles
}

def get_random_microfact(era_data: dict, level: str = "básico") -> str:
    """
    Devuelve un microfact aleatorio de la base de datos, filtrado por nivel.
    - Infantil (3-5): solo hechos concretos y visuales (cotidiana, infancia).
      Evita temas abstractos como fuentes, desigualdad o comparacion.
    - Básico (6-8): añade trabajo y creencias.
    - Intermedio / Avanzado: todos los temas disponibles.
    """
    mf_dict    = era_data.get("microfacts", {})
    allowed    = MICROFACT_THEMES_BY_LEVEL.get(level)   # None = sin filtro
    all_facts  = []
    for theme, facts in mf_dict.items():
        if isinstance(facts, list):
            if allowed is None or theme in allowed:
                all_facts.extend(facts)
    # Fallback: si el filtro deja la lista vacía, usar todos
    if not all_facts:
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
                       prebuilt_context: str = ""):
    import google.generativeai as genai
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return None, "⚠️ IA no configurada. Añade GEMINI_API_KEY en los Secrets de Streamlit."
    genai.configure(api_key=api_key)

    level_cfg    = LEVELS[level]
    context_text = prebuilt_context if prebuilt_context else build_context(era_data)
    # ── Instrucciones pedagógicas específicas por nivel de edad ──────────────
    PEDAGOGICAL_INSTRUCTIONS = {
        "infantil": """
NIVEL: INFANTIL (3-5 años)
El niño que te habla tiene entre 3 y 5 años. Su pensamiento es concreto, egocéntrico y vive en el presente.

CÓMO HABLARLE:
- Usa SOLO palabras que un niño de 3 años conozca de su vida diaria: casa, comer, dormir, jugar, mamá, papá, amigos, frío, calor, miedo, contento.
- Compara SIEMPRE con su vida: "igual que tu casa, pero hecha de piedra", "como cuando tú comes pan, pero diferente".
- Habla en presente o pasado simple: "vivíamos", "comíamos", "nos gustaba". Nunca "se desarrolló", "existía la práctica de".
- Máximo 2 frases. Cada frase: máximo 8-10 palabras.
- UNA sola idea por respuesta. No encadenes conceptos.
- Sin fechas, sin siglos, sin números grandes. "Hace mucho, mucho tiempo" es suficiente.
- Sin palabras abstractas: nada de "sociedad", "civilización", "economía", "cultura", "período", "territorio".
- Tono cálido y cercano, como si le hablaras al oído. Usa el "tú".
- Puedes añadir una sola emoción: "y era muy divertido", "a veces teníamos miedo".

EJEMPLO CORRECTO: "¡Sí! Teníamos fuego. Nos calentaba mucho, igual que cuando tú te arropas."
EJEMPLO INCORRECTO: "El fuego fue fundamental para el desarrollo de nuestra civilización primitiva."
""",
        "básico": """
NIVEL: BÁSICO (6-8 años)
El niño que te habla tiene entre 6 y 8 años. Está aprendiendo a leer y a razonar de forma simple. Entiende causa-efecto sencilla ("porque", "para que").

CÓMO HABLARLE:
- Frases cortas: máximo 15-18 palabras por frase.
- Puedes usar 3-4 frases en total.
- Vocabulario cotidiano con alguna palabra nueva explicada al momento: "el faraón, que era como un rey muy poderoso".
- Puedes introducir UNA causa simple: "porque hacía mucho frío", "para protegernos".
- Puedes mencionar "hace muchos años" o "hace miles de años", pero sin siglos ni fechas concretas.
- Nada de conceptos abstractos complejos. "Los nobles" necesita explicación: "los nobles, que eran las personas más ricas".
- Relaciona con su experiencia cuando puedas: "como en tu colegio, pero...", "como cuando juegas a...".
- Tono animado y cercano. Puedes mostrar entusiasmo o emoción del personaje.
- Sin tecnicismos históricos sin explicar.

EJEMPLO CORRECTO: "¡Claro que íbamos a la escuela! Aprendíamos a escribir con un palito en barro. Era difícil, pero muy importante para trabajar de mayor."
EJEMPLO INCORRECTO: "La educación en el período clásico griego se desarrollaba en el contexto del gymnasium."
""",
        "intermedio": """
NIVEL: INTERMEDIO (8-10 años)
El alumno tiene entre 8 y 10 años. Puede manejar relaciones de causa-efecto encadenadas, comparaciones entre épocas y conceptos históricos básicos si se explican.

CÓMO HABLARLE:
- Respuestas de longitud media: 4-6 frases con buena coherencia.
- Puedes usar vocabulario histórico si lo explicas brevemente en la misma frase: "los siervos, personas que trabajaban las tierras del señor feudal".
- Introduce causas y consecuencias: "porque no había hospitales, muchos morían de enfermedades que hoy se curan fácilmente".
- Puedes mencionar épocas o períodos aproximados: "en la Edad Media", "hace unos 2.000 años".
- Puedes hacer comparaciones con el presente: "hoy en día esto sería ilegal, pero entonces...".
- Puedes mencionar que diferentes grupos vivían de forma distinta (desigualdad, diferencias sociales).
- El personaje puede mostrar reflexión o incertidumbre: "no sé si eso era justo, pero así era nuestra vida".
- Mantén el tono del personaje histórico, pero con algo más de profundidad emocional e histórica.

EJEMPLO CORRECTO: "Los niños de mi época no iban a la escuela como vosotros. Los hijos de familias ricas aprendían con un maestro en casa, pero los demás empezábamos a trabajar muy jóvenes, a veces con solo siete u ocho años. Era duro, pero no conocíamos otra vida."
""",
        "avanzado": """
NIVEL: AVANZADO (10-12 años)
El alumno tiene entre 10 y 12 años. Puede manejar pensamiento crítico, perspectivas múltiples, causalidad compleja y reflexión histórica. Está en los últimos cursos de primaria.

CÓMO HABLARLE:
- Respuestas completas: 5-7 frases bien estructuradas.
- Usa vocabulario histórico con precisión: feudalismo, absolutismo, ilustración, opresión, desigualdad, revolución.
- Desarrolla causa-efecto compleja: encadena razones y consecuencias.
- Muestra perspectivas diferentes: "los nobles pensaban que era justo, pero los campesinos sufrían enormemente".
- Puedes citar períodos, siglos o fechas aproximadas cuando aporten comprensión.
- Introduce dilemas éticos o morales de forma respetuosa: "¿era justo que...? Yo mismo me lo preguntaba a veces".
- Fomenta la reflexión comparando con el presente sin imponer conclusiones.
- El personaje puede tener una voz más elaborada, con matices, contradicciones y humanidad.
- Puedes mencionar fuentes históricas o cómo sabemos lo que sabemos.
- Aborda la desigualdad de género, clase social y étnica cuando sea relevante.

EJEMPLO CORRECTO: "La Revolución nos ilusionó a todos con la idea de libertad e igualdad, pero la realidad fue más complicada. Mientras los burgueses ganaban poder, muchos campesinos y trabajadores vieron que su vida apenas cambiaba. El Comité de Salvación Pública acabó usando el terror para mantener el orden, algo que contradecía los ideales que habíamos defendido. La historia raramente es tan sencilla como parece."
"""
    }

    pedagogical = PEDAGOGICAL_INSTRUCTIONS.get(level, PEDAGOGICAL_INSTRUCTIONS["intermedio"])


    system = f"""=== QUIÉN ERES ===
Eres {era_data['voz']} del período {era_data['name']} ({era_data['periodo']}).
Habla SIEMPRE en primera persona, como esa persona histórica real.
Habla desde tu experiencia vivida, no como un libro de texto ni un narrador externo.

=== LO QUE SABES DE TU ÉPOCA ===
{context_text}

=== CÓMO DEBES HABLAR (MUY IMPORTANTE) ===
{pedagogical}

=== REGLA PRINCIPAL — LEE ESTO PRIMERO ===
RESPONDE SIEMPRE EXACTAMENTE A LO QUE EL ALUMNO ACABA DE PREGUNTAR.
No respondas a una pregunta parecida si no es la que se hizo.
No des información general si te hacen una pregunta específica.
Si la pregunta es concreta ("¿qué comíais?"), da una respuesta concreta sobre eso.
Si la pregunta es abierta ("cuéntame algo"), puedes responder con más amplitud.

=== REGLAS QUE NUNCA PUEDES ROMPER ===
1. ROL: Nunca salgas del personaje. Eres esa persona, no una IA.

2. PREGUNTAS SOBRE COSAS DE HOY (coches, móviles, internet, aviones, TV, ordenadores...):
   Muestra curiosidad genuina: "¿Qué es eso? En mi época no existía algo así..."
   Explica qué se usaba en tu tiempo para lo mismo.

3. SI NO SABES ALGO CON CERTEZA: dilo en personaje.
   "No recuerdo bien ese nombre..." NUNCA inventes fechas, nombres o datos que no estén en tu contexto.

4. TEMAS DUROS (guerra, muerte, hambre, represión):
   Responde con honestidad apropiada para la edad.
   Nivel Infantil: suaviza y redirige. Niveles superiores: trata con respeto y contexto.

5. LONGITUD: Máximo {level_cfg['max_chars']} caracteres. RESPETA este límite.

6. FORMATO: Solo español. Sin asteriscos, guiones, listas ni markdown. Texto corrido."""

    chat_history = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
        for m in history[-8:]
        if m.get("content","").strip()
    ]
    while chat_history and chat_history[-1]["role"] == "user":
        chat_history.pop()

    try:
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite", system_instruction=system)
        chat  = model.start_chat(history=chat_history)
        return chat, None
    except Exception as e:
        return None, f"⚠️ Error configurando la IA: {str(e)[:80]}"

# ═══════════════════════════════════════════════════════════════════════════════
# STREAMING
# ═══════════════════════════════════════════════════════════════════════════════
def stream_gemini(question: str, era_data: dict, level: str, history: list,
                  prebuilt_context: str = ""):
    chat, error = _build_gemini_chat(era_data, level, history, prebuilt_context)
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
        err = str(e)
        if "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
            yield ("\n\n⏸️ La IA ha alcanzado su límite de peticiones. "
                   "Puedes ver el límite exacto de tu cuenta en: "
                   "aistudio.google.com/rate-limit — "
                   "Si el límite es diario (RPD), se reinicia a medianoche hora del Pacífico "
                   "(aproximadamente las 9h de España). "
                   "Si es por minuto (RPM), espera 60 segundos e inténtalo de nuevo.")
        else:
            yield f"\n⚠️ Error de conexión con la IA: {err[:80]}"

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
def build_quiz(messages: list, era_data: dict, level: str = "básico"):
    """
    Devuelve (items, error_msg).
    - items: lista de preguntas generadas, o [] si hay error
    - error_msg: None si todo fue bien, o texto del error para mostrar al alumno
    """
    import google.generativeai as genai
    api_key = st.secrets.get("GEMINI_API_KEY","")
    if not api_key:
        return [], "⚠️ IA no configurada. Añade GEMINI_API_KEY en los Secrets de Streamlit."
    genai.configure(api_key=api_key)

    cfg = QUIZ_CONFIG.get(level, QUIZ_CONFIG["básico"])

    # Contar pares usuario→asistente (no depende de signos de puntuación)
    pairs = [
        (messages[i-1]["content"], messages[i]["content"])
        for i in range(1, len(messages))
        if messages[i]["role"] == "assistant" and messages[i-1]["role"] == "user"
    ]
    if len(pairs) < 2:
        return [], "💬 Necesitas tener al menos 2 intercambios de preguntas y respuestas en el chat antes de generar el cuestionario."

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
        model    = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
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
        if not items:
            return [], "⚠️ Gemini generó el cuestionario pero no pudo analizarlo correctamente. Inténtalo de nuevo."
        return items[:cfg["n"]], None
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
            return [], "⏳ Se ha alcanzado el límite de peticiones a la IA. Espera unos minutos e inténtalo de nuevo."
        return [], f"⚠️ Error al generar el cuestionario: {err[:120]}. Inténtalo de nuevo."

# ═══════════════════════════════════════════════════════════════════════════════
# TEXTO A VOZ
# ═══════════════════════════════════════════════════════════════════════════════
# Velocidad de lectura adaptada al nivel de edad
TTS_RATE_BY_LEVEL = {
    "infantil":   0.75,   # lento y muy claro: 3-5 años aún procesan despacio
    "básico":     0.82,   # algo más lento que normal: 6-8 años
    "intermedio": 0.88,   # velocidad estándar: 8-10 años
    "avanzado":   0.92,   # ligeramente más rápido: 10-12 años
}

def speak_text(text: str, level: str = "básico"):
    """
    Lectura en voz alta con velocidad adaptada a la edad del alumno.
    Siempre se llama con el texto COMPLETO (tras streaming) → TTS fluido sin cortes.
    """
    import streamlit.components.v1 as components
    rate = TTS_RATE_BY_LEVEL.get(level, 0.88)
    safe = json.dumps(text)
    components.html(
        f"<script>"
        f"window.speechSynthesis&&window.speechSynthesis.cancel();"
        f"var u=new SpeechSynthesisUtterance({safe});"
        f"u.lang='es-ES';u.rate={rate};u.pitch=1.05;"
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
    Todas las preguntas van a Gemini para garantizar voz de personaje y
    adaptación pedagógica correcta.

    Si existe una FAQ con coincidencia clara (score ≥ 3), se pasa a Gemini
    como "respuesta base" para que la reformule con voz y nivel apropiados,
    no como respuesta directa (que carecía de personalidad).

    Auto-lectura en Infantil: se dispara DESPUÉS de tener el texto completo
    → lectura fluida sin cortes ni pausas.
    """
    ss = st.session_state

    with st.chat_message("user", avatar="🧑‍🎓"):
        st.write(question)

    # Gemini recibe contexto completo — sin hints que puedan confundir
    # Comprobar límite diario de seguridad
    calls_today = gemini_calls_today()
    if calls_today >= GEMINI_DAILY_LIMIT:
        fallback = (
            "Se han usado todas las preguntas disponibles para hoy. "
            "El límite se reinicia a medianoche (hora española: 9h). "
            "Puedes seguir explorando las sugerencias del menú lateral."
        )
        with st.chat_message("assistant", avatar=era_meta["emoji"]):
            st.warning(fallback)
        full_text = fallback
    else:
        # Gemini responde siempre — con voz de personaje y nivel adaptado
        with st.chat_message("assistant", avatar=era_meta["emoji"]):
            full_text = st.write_stream(
                stream_gemini(question, current_era, level,
                              ss.messages[:-1], prebuilt_context)
            )
        increment_gemini_calls()

    ss.messages.append({"role": "assistant", "content": full_text})
    ss.last_bot_text  = full_text
    ss.last_microfact = get_random_microfact(current_era, level)

    # Log para panel docente
    log_question(ss.era_id, current_era.get("name",""), level, question)

    # Auto-lectura en Infantil (texto completo → TTS fluido sin cortes)
    if level == "infantil":
        speak_text(full_text, level)

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

    # ── Indicador de quota Gemini ────────────────────────────────────────────
    calls = gemini_calls_today()
    remaining = max(0, GEMINI_DAILY_LIMIT - calls)
    pct_used  = min(100, int(calls / GEMINI_DAILY_LIMIT * 100))
    quota_color = "#2e7d32" if pct_used < 60 else ("#f57c00" if pct_used < 85 else "#c62828")
    st.markdown(f"""
    <div class="teacher-stat-card" style="border-color:{quota_color}40;">
      <div class="teacher-stat-title">LLAMADAS A GEMINI HOY</div>
      <div class="teacher-stat-value" style="color:{quota_color};">{calls} / {GEMINI_DAILY_LIMIT}</div>
      <div style="background:#e8e5ff;border-radius:8px;height:8px;margin-top:8px;">
        <div style="background:{quota_color};width:{pct_used}%;height:8px;border-radius:8px;transition:width .3s;"></div>
      </div>
      <div style="font-size:.78rem;color:#667685;margin-top:4px;">
        {remaining} llamadas según contador interno · Límites reales en: aistudio.google.com/rate-limit
      </div>
    </div>
    """, unsafe_allow_html=True)

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
# TEXTOS DE INTERFAZ ADAPTADOS AL NIVEL
# ═══════════════════════════════════════════════════════════════════════════════
UI_TEXTS = {
    "infantil": {
        "welcome_title":    "¡Hola! 👋",
        "welcome_sub":      "¡Vamos a hablar con personas de hace mucho tiempo!",
        "welcome_step1":    "🗺️ Elige a quién visitar",
        "welcome_step2":    "📚 Di cuántos años tienes",
        "welcome_step3":    "💬 ¡Pregúntales cosas!",
        "welcome_btn":      "¡Vamos! 🚀",
        "sidebar_sub":      "¡Habla con el pasado!",
        "era_label":        "👇 ¿Con quién quieres hablar?",
        "level_label":      "🌱 ¿Cuántos años tienes?",
        "tools_label":      "✨ Botones de ayuda",
        "sug_label":        "👇 ¡Toca una pregunta!",
        "quiz_hint":        "¡Elige la respuesta correcta!",
        "quiz_correct":     "¡Muy bien! ✅ La respuesta era:",
        "quiz_wrong":       "¡Casi! ❌ La respuesta era:",
        "btn_prev":         "⬅️ Atrás",
        "btn_next":         "Siguiente ➡️",
        "btn_submit":       "¡Ver si lo sé! 🌟",
        "btn_review":       "🔍 Ver mis respuestas",
        "btn_close_quiz":   "✖ Cerrar",
        "btn_reiniciar":    "🔄 Borrar",
        "btn_sugerencia":   "💡 Ayuda",
        "btn_test":         "🌟 ¡Jugar!",
    },
    "básico": {
        "welcome_title":    "¡Historia Viva!",
        "welcome_sub":      "Habla con personas del pasado y descubre cómo vivían.",
        "welcome_step1":    "🗺️ Elige una época",
        "welcome_step2":    "📚 Elige tu curso",
        "welcome_step3":    "💬 ¡Haz preguntas!",
        "welcome_btn":      "¡Empezar! 🚀",
        "sidebar_sub":      "Habla con el pasado",
        "era_label":        "🗺️ Elige una época",
        "level_label":      "📚 Elige tu curso",
        "tools_label":      "🛠️ Herramientas",
        "sug_label":        "💬 ¿Qué quieres preguntar?",
        "quiz_hint":        "Elige la respuesta correcta.",
        "quiz_correct":     "✅ Respuesta correcta:",
        "quiz_wrong":       "❌ Respuesta correcta:",
        "btn_prev":         "← Anterior",
        "btn_next":         "Siguiente →",
        "btn_submit":       "✅ Ver resultados",
        "btn_review":       "📖 Ver mis respuestas",
        "btn_close_quiz":   "Cerrar",
        "btn_reiniciar":    "🔄 Reiniciar",
        "btn_sugerencia":   "💡 Ayuda",
        "btn_test":         "📝 Test final",
    },
    "intermedio": {
        "welcome_title":    "¡Historia Viva!",
        "welcome_sub":      "Viaja al pasado y habla con sus protagonistas.<br>¡Hazles todas las preguntas que quieras!",
        "welcome_step1":    "🗺️ Elige una época histórica",
        "welcome_step2":    "📚 Elige tu curso",
        "welcome_step3":    "💬 ¡Pregunta lo que quieras!",
        "welcome_btn":      "¡Empezar! 🚀",
        "sidebar_sub":      "Habla con el pasado",
        "era_label":        "🗺️ Elige una época",
        "level_label":      "📚 Elige tu curso",
        "tools_label":      "🛠️ Herramientas",
        "sug_label":        "💬 ¿Sobre qué quieres preguntar?",
        "quiz_hint":        "Responde todas las preguntas y luego pulsa Corregir.",
        "quiz_correct":     "✅ Respuesta correcta:",
        "quiz_wrong":       "❌ Respuesta correcta:",
        "btn_prev":         "← Anterior",
        "btn_next":         "Siguiente →",
        "btn_submit":       "✅ Ver resultados",
        "btn_review":       "📖 Ver mis respuestas",
        "btn_close_quiz":   "Cerrar",
        "btn_reiniciar":    "🔄 Reiniciar",
        "btn_sugerencia":   "💡 Ayuda",
        "btn_test":         "📝 Test final",
    },
    "avanzado": {
        "welcome_title":    "Historia Viva",
        "welcome_sub":      "Conversa con protagonistas históricos y explora el pasado en profundidad.",
        "welcome_step1":    "🗺️ Selecciona una época histórica",
        "welcome_step2":    "📚 Elige tu nivel educativo",
        "welcome_step3":    "💬 Formula tus preguntas",
        "welcome_btn":      "Comenzar 🚀",
        "sidebar_sub":      "Explora el pasado",
        "era_label":        "🗺️ Época histórica",
        "level_label":      "📚 Nivel educativo",
        "tools_label":      "🛠️ Herramientas",
        "sug_label":        "💬 Temas que puedes explorar:",
        "quiz_hint":        "Responde todas las preguntas y pulsa Corregir para ver tus resultados.",
        "quiz_correct":     "✅ Respuesta correcta:",
        "quiz_wrong":       "❌ Respuesta correcta:",
        "btn_prev":         "← Anterior",
        "btn_next":         "Siguiente →",
        "btn_submit":       "✅ Corregir respuestas",
        "btn_review":       "📖 Revisar mis respuestas",
        "btn_close_quiz":   "Cerrar cuestionario",
        "btn_reiniciar":    "🔄 Reiniciar",
        "btn_sugerencia":   "💡 Ayuda",
        "btn_test":         "📝 Cuestionario final",
    },
}

def tx(level: str, key: str) -> str:
    """Atajo para obtener un texto de interfaz adaptado al nivel."""
    return UI_TEXTS.get(level, UI_TEXTS["intermedio"]).get(key, "")


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
        wt = UI_TEXTS.get(level, UI_TEXTS["intermedio"])
        st.markdown(f"""
        <div class="welcome-container">
          <div class="bounce" style="font-size:4rem;margin-bottom:10px;">🏛️</div>
          <div class="welcome-title">{wt["welcome_title"]}</div>
          <div class="welcome-sub">{wt["welcome_sub"]}</div>
          <div class="welcome-steps">
            <div class="welcome-step"><div class="welcome-step-icon">🗺️</div><div class="welcome-step-text"><b>1.</b> {wt["welcome_step1"]}</div></div>
            <div class="welcome-step"><div class="welcome-step-icon">📚</div><div class="welcome-step-text"><b>2.</b> {wt["welcome_step2"]}</div></div>
            <div class="welcome-step"><div class="welcome-step-icon">💬</div><div class="welcome-step-text"><b>3.</b> {wt["welcome_step3"]}</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        _, col_btn, _ = st.columns([2,2,2])
        with col_btn:
            if st.button(wt["welcome_btn"], type="primary", use_container_width=True):
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
        st.markdown(f'<div style="font-size:.82rem;color:#9e9e9e;text-align:center;margin-bottom:4px;">{tx(level,"sidebar_sub")}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"**{tx(level,'era_label')}**")
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
        st.markdown(f"**{tx(level,'level_label')}**")
        new_level = st.radio(
            "Elige tu curso",           # label real pero oculto — elimina el botón "nivel"
            options=list(LEVELS.keys()),
            format_func=lambda x: LEVELS[x]["label"],
            index=list(LEVELS.keys()).index(level),
            label_visibility="hidden",  # oculta el label sin dejar hueco (antes "collapsed" dejaba un pequeño botón vacío)
        )
        if new_level != level:
            ss.level, ss.messages, ss.suggestions = new_level, [], []
            ss.show_quiz, ss.quiz_current_q = False, 0
            ss.quiz_reviewing, ss.quiz_show_score = False, False
            ss.last_microfact = ""
            # Letra grande automática en Infantil (3-5 años siempre necesitan texto grande)
            # Al salir de Infantil se desactiva para no forzar a los demás niveles.
            ss.big_text = False   # no forzar letra grande en ningún nivel
            st.rerun()

        st.markdown("---")
        st.markdown(f"**{tx(level,'tools_label')}**")
        # Forzar mismo tamaño en los dos botones con columnas de igual anchura
        # y altura mínima fija via CSS inline para evitar que el emoji haga
        # que "Sugerencia" sea más alto que "Reiniciar"
        st.markdown("""
        <style>
        div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
          min-height: 2.6rem !important;
          height:     2.6rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button(tx(level,"btn_sugerencia"), use_container_width=True):
                pool = get_suggestions(current_era, level, ss.era_id, 10)
                if pool:
                    ss.pending_q = re.sub(r"^[^\w¿¡]+","",random.choice(pool)).strip()
                    st.rerun()
        with c2:
            if st.button(tx(level,"btn_reiniciar"), use_container_width=True):
                ss.messages, ss.suggestions = [], []
                ss.show_quiz, ss.last_bot_text = False, ""
                ss.quiz_current_q, ss.quiz_reviewing = 0, False
                ss.quiz_show_score, ss.last_microfact = False, ""
                st.rerun()

        if ss.last_bot_text:
            c3, c4 = st.columns(2)
            with c3:
                if st.button("🔊 Leer", use_container_width=True):
                    speak_text(ss.last_bot_text, level)
            with c4:
                if st.button("⏹ Parar", use_container_width=True):
                    stop_speak()

        fl = "🔡 Normal" if ss.big_text else "🔠 Letra grande"
        if st.button(fl, use_container_width=True):
            ss.big_text = not ss.big_text
            st.rerun()

        if len(ss.messages) >= 4:
            if st.button(tx(level,"btn_test"), use_container_width=True, type="primary"):
                with st.spinner("Generando cuestionario…"):
                    quiz_items, quiz_error = build_quiz(ss.messages, current_era, level)
                if quiz_error:
                    st.warning(quiz_error)
                else:
                    ss.quiz_items      = quiz_items
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
            calls_now     = gemini_calls_today()
            remaining_now = max(0, GEMINI_DAILY_LIMIT - calls_now)
            pct_now       = min(100, int(calls_now / GEMINI_DAILY_LIMIT * 100))
            bar_color     = "#2e7d32" if pct_now < 60 else ("#f57c00" if pct_now < 85 else "#c62828")
            st.markdown(
                f'<div style="font-size:.75rem;color:#667685;margin:4px 0 6px;">'
                f'Gemini hoy: <b style="color:{bar_color}">{calls_now}/{GEMINI_DAILY_LIMIT}</b> '
                f'({remaining_now} restantes)</div>',
                unsafe_allow_html=True,
            )
            if st.button("👩‍🏫 Panel Docente", use_container_width=True, type="primary"):
                ss.teacher_mode = True
                st.rerun()

    # ──────────────────────────────────────────────────────────────────────────
    # ÁREA PRINCIPAL
    # ──────────────────────────────────────────────────────────────────────────

    # ── Hero con imagen ──────────────────────────────────────────────────────
    if current_era:
        color = era_meta["color"]
        bg    = era_meta["bg"]
        emoji = era_meta["emoji"]

        # Texto de apertura adaptado al nivel
        level_key = (level
                     .replace("á","a").replace("é","e").replace("í","i")
                     .replace("ó","o").replace("ú","u"))
        apertura_text = (
            APERTURA_NIVEL.get(ss.era_id, {}).get(level_key)
            or current_era.get("apertura", "")
        )

        # Imagen: st.image() con bytes raw — funciona en Streamlit Cloud
        # sin restricciones de Content-Security-Policy.
        img_bytes = era_images.get(ss.era_id)

        st.markdown(f"""
        <div class="hero-card" style="background:{bg}; border:2px solid {color}40;">
        """, unsafe_allow_html=True)

        if img_bytes:
            st.image(img_bytes, use_container_width=True)

        st.markdown(f"""
          <div class="hero-content">
            <span class="hero-avatar">{emoji}</span>
            <div class="hero-era-name" style="color:{color};">{current_era.get('name','')}</div>
            <div class="hero-period">{current_era.get('periodo','')}</div>
            <span class="hero-badge" style="background:{color}22;color:{color};">{LEVELS[level]['label']}</span>
            <div class="hero-voice" style="border-left-color:{color};">
              💬 <em>{apertura_text}</em>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

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

    # ──────────────────────────────────────────────────────────────────────────
    # CUESTIONARIO
    # ──────────────────────────────────────────────────────────────────────────
    if ss.show_quiz:
        # Ancla para scroll automático al inicio del cuestionario
        st.markdown('<div id="quiz-top"></div>', unsafe_allow_html=True)
        # Desplazar la página hasta el título del cuestionario
        import streamlit.components.v1 as components
        components.html(
            "<script>"
            "window.parent.document.getElementById('quiz-top')"
            "?.scrollIntoView({behavior:'smooth', block:'start'});"
            "</script>",
            height=0,
        )
        if not ss.quiz_items:
            st.warning("⚠️ El cuestionario no tiene preguntas. Ciérralo e inténtalo de nuevo.")
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
                if st.button(tx(level,"btn_review"), type="primary", use_container_width=True):
                    ss.quiz_show_score = False
                    ss.quiz_reviewing  = True
                    ss.quiz_current_q  = 0
                    st.rerun()
            with col_close:
                if st.button(tx(level,"btn_close_quiz"), use_container_width=True):
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
                    reveal_label = tx(level,"quiz_correct") if ok else tx(level,"quiz_wrong")
                    st.markdown(f'<div class="{css}">{reveal_label} <b>{short}</b></div>',
                                unsafe_allow_html=True)
                    cp, cn = st.columns([1,1])
                    with cp:
                        if idx > 0 and st.button(tx(level,"btn_prev"), key="rev_prev"):
                            ss.quiz_current_q -= 1; st.rerun()
                    with cn:
                        if idx < total - 1:
                            if st.button(tx(level,"btn_next"), key="rev_next", type="primary"):
                                ss.quiz_current_q += 1; st.rerun()
                        else:
                            if st.button(tx(level,"btn_close_quiz"), key="rev_close"):
                                ss.show_quiz, ss.quiz_reviewing = False, False
                                ss.quiz_current_q = 0; st.rerun()
                else:
                    answer = st.radio(f"q{idx}", options=item["options"],
                                      index=None,
                                      key=f"qz_{idx}", label_visibility="collapsed")
                    if answer is not None:
                        ss.quiz_answers[idx] = answer
                    cp, cn = st.columns([1,1])
                    with cp:
                        if idx > 0 and st.button(tx(level,"btn_prev"), key="q_prev"):
                            ss.quiz_current_q -= 1; st.rerun()
                    with cn:
                        if idx < total - 1:
                            if st.button(tx(level,"btn_next"), key="q_next", type="primary"):
                                ss.quiz_current_q += 1; st.rerun()
                        else:
                            if st.button(tx(level,"btn_submit"), key="q_submit", type="primary"):
                                ss.quiz_submitted  = True
                                ss.quiz_show_score = True
                                ss.quiz_current_q  = 0; st.rerun()
            else:
                st.caption(tx(level, "quiz_hint"))
                for i, item in enumerate(ss.quiz_items):
                    render_quiz_progress(i, total)
                    st.markdown(
                        f'<div class="quiz-question-card"><div class="quiz-q-text">{item["q"]}</div></div>',
                        unsafe_allow_html=True,
                    )
                    answer = st.radio(f"q{i}", options=item["options"],
                                      index=None,
                                      key=f"qz_{i}", disabled=ss.quiz_submitted,
                                      label_visibility="collapsed")
                    if answer is not None:
                        ss.quiz_answers[i] = answer
                    if ss.quiz_submitted:
                        ok    = ss.quiz_answers.get(i) == item["correct"]
                        short = item["correct"][:160] + ("…" if len(item["correct"]) > 160 else "")
                        css   = "quiz-reveal-ok" if ok else "quiz-reveal-bad"
                        icon  = "✅" if ok else "❌"
                        reveal_label2 = tx(level,"quiz_correct") if ok else tx(level,"quiz_wrong")
                        st.markdown(f'<div class="{css}">{reveal_label2} <b>{short}</b></div>',
                                    unsafe_allow_html=True)
                    st.markdown("---")
                if not ss.quiz_submitted:
                    ca, cb = st.columns([2,1])
                    with ca:
                        if st.button(tx(level,"btn_submit"), type="primary"):
                            ss.quiz_submitted  = True
                            ss.quiz_show_score = True; st.rerun()
                    with cb:
                        if st.button(tx(level,"btn_close_quiz")):
                            ss.show_quiz = False; st.rerun()
                else:
                    if st.button(tx(level,"btn_close_quiz")):
                        ss.show_quiz, ss.quiz_reviewing = False, False; st.rerun()


    # ── Sugerencias (chat vacío) ───────────────────────────────────────────────
    if not ss.messages:
        if not ss.suggestions:
            ss.suggestions = get_suggestions(current_era, level, ss.era_id)
        if ss.suggestions:
            st.markdown(f'<div class="sug-label">{tx(level,"sug_label")}</div>',
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

    CHAT_PLACEHOLDERS = {
        "infantil":   "¿Qué quieres saber? 😊",
        "básico":     f"Escribe tu pregunta para {current_era.get('name','esta época')}…",
        "intermedio": f"Pregunta a {current_era.get('voz','el personaje histórico')}…",
        "avanzado":   f"Haz tu pregunta histórica a {current_era.get('voz','el personaje')}…",
    }
    placeholder = CHAT_PLACEHOLDERS.get(level, "Escribe tu pregunta…") if current_era else "Elige una época para empezar…"
    if prompt := st.chat_input(placeholder):
        ss.messages.append({"role":"user","content":prompt})
        handle_question(prompt, current_era, level, era_meta, current_context)
        st.rerun()


if __name__ == "__main__":
    main()
