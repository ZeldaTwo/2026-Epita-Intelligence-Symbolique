
import sys
from pathlib import Path

import streamlit as st

# =============================================================================
# 1. AUTO-DÉTECTION DU CHEMIN DES MODULES
# =============================================================================
def _find_project_modules():
    """Cherche translator.py dans les emplacements probables."""
    candidates = [
        Path.cwd(),
        Path.cwd() / "src",
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent / "src",
        Path(__file__).resolve().parent.parent,
        Path(__file__).resolve().parent.parent / "src",
    ]
    for candidate in candidates:
        if (candidate / "translator.py").exists():
            return str(candidate)
    return None

MODULES_DIR = _find_project_modules()
if MODULES_DIR and MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)

# =============================================================================
# 2. Imports (avec fallback explicite)
# =============================================================================
try:
    from config import get_default_max_attempts
    from translator import LLMTranslator, parse_symbolic_model
    from validator import validate
    from solver_backend import solve
    from interpreter import interpret_with_llm, interpret_without_llm
    from schema import ErrorCategory
except ImportError as exc:
    st.set_page_config(page_title="Erreur", layout="centered")
    st.error(f"Impossible d'importer les modules du projet : {exc}")
    st.markdown("""
    **Vérifiez que :**
    1. Le fichier `app.py` est placé à la racine de votre projet
    2. Vous lancez avec : `streamlit run app.py` depuis la racine du projet
    """)
    st.stop()

# =============================================================================
# 3. Configuration Streamlit
# =============================================================================
st.set_page_config(
    page_title="Symbolic Solver",
    page_icon="◈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #FAFAFA; }

    .sym-card {
        background-color: #FFFFFF;
        border-left: 4px solid #00695C;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-top: 0.75rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .sym-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }
    .sym-badge-sat   { background: #E8F5E9; color: #1B5E20; }
    .sym-badge-unsat { background: #FFEBEE; color: #B71C1C; }
    .sym-badge-err   { background: #FFF3E0; color: #E65100; }
    .sym-badge-info  { background: #E0F2F1; color: #00695C; }
    .sym-badge-neut  { background: #F5F5F5; color: #616161; }
    .sym-badge-form  { background: #ECEFF1; color: #37474F; border: 1px solid #CFD8DC; }
    .sym-answer { color: #263238; font-size: 1rem; line-height: 1.6; margin: 0; }
    .sym-divider { border: none; border-top: 1px solid #ECEFF1; margin: 0.75rem 0; }
    .sym-title { text-align: center; color: #263238; font-weight: 600; font-size: 1.5rem; margin-bottom: 0.2rem; }
    .sym-subtitle { text-align: center; color: #78909C; font-size: 0.9rem; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 4. Sidebar
# =============================================================================
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    model_name = st.text_input("Modèle Ollama", value="qwen2.5-coder")
    _default_attempts = get_default_max_attempts()
    _slider_max = max(10, _default_attempts)
    max_attempts = st.slider("Tentatives max", 1, _slider_max,
                             min(_default_attempts, _slider_max))
    use_llm_interp = st.toggle("Interprétation LLM", value=True)
    st.divider()
    st.caption("Pipeline IA Symbolique — v1.0")

# =============================================================================
# 5. État de session
# =============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if (
    "translator" not in st.session_state
    or st.session_state.get("_cached_model") != model_name
):
    try:
        st.session_state.translator = LLMTranslator(model_name=model_name)
        st.session_state._cached_model = model_name
    except Exception as exc:
        st.error(f"Impossible de se connecter à Ollama : {exc}")
        st.session_state.translator = None

# =============================================================================
# 6. Helpers d'affichage
# =============================================================================
def render_result_card(data: dict):
    """Affiche la carte de résultat en HTML brut via st.html."""
    status = data["solver_status"]
    if status in ("SAT", "PDDL_PARSED"):
        badge_cls, badge_icon, badge_txt = "sym-badge-sat", "✓", status
    elif status == "UNSAT":
        badge_cls, badge_icon, badge_txt = "sym-badge-unsat", "✗", "UNSAT"
    else:
        badge_cls, badge_icon, badge_txt = "sym-badge-err", "!", status

    coh_cls = "sym-badge-sat" if data["coherent"] else "sym-badge-err"
    coh_icon = "✓" if data["coherent"] else "✗"
    coh_txt = "Cohérent" if data["coherent"] else "Incohérent"

    attempts = data["attempts"]
    attempts_badge = (
        f'<span class="sym-badge sym-badge-info">🔄 {attempts} tentative{"s" if attempts > 1 else ""}</span>'
        if attempts > 1 else ""
    )

    expected = data.get("expected_status")
    expected_badge = f'<span class="sym-badge sym-badge-neut">Attendu : {expected}</span>' if expected else ""

    formalism = data.get("formalism", "—")
    form_badge = f'<span class="sym-badge sym-badge-form">◈ {formalism.upper()}</span>'

    html = f"""<div class="sym-card">
        <div style="margin-bottom:0.5rem;">
            {form_badge}
            <span class="sym-badge {badge_cls}">{badge_icon} {badge_txt}</span>
            <span class="sym-badge {coh_cls}">{coh_icon} {coh_txt}</span>
            {attempts_badge}
            {expected_badge}
        </div>
        <hr class="sym-divider">
        <p class="sym-answer">{data["answer"]}</p>
    </div>"""

    # st.html est le moyen le plus fiable d'injecter du HTML brut dans Streamlit
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)

# =============================================================================
# 7. Header
# =============================================================================
st.markdown('<div class="sym-title">◈ Symbolic Solver</div>', unsafe_allow_html=True)
st.markdown('<div class="sym-subtitle">Traduction et résolution symbolique par LLM local</div>', unsafe_allow_html=True)
st.divider()

# =============================================================================
# 8. Historique
# =============================================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and "result" in msg:
            render_result_card(msg["result"])
        else:
            st.markdown(msg["content"])

# =============================================================================
# 9. Input & traitement
# =============================================================================
if prompt := st.chat_input("Décrivez votre problème (ex: 'Si Paul vient alors Julie vient...')"):
    # --- Message utilisateur ---
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Vérification traducteur ---
    if st.session_state.translator is None:
        with st.chat_message("assistant"):
            st.error("Le traducteur n'est pas initialisé. Vérifiez qu'Ollama est démarré (`ollama serve`).")
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Le traducteur n'est pas initialisé. Vérifiez qu'Ollama est démarré."
        })
        st.stop()

    # --- Traitement ---
    with st.chat_message("assistant"):
        # Phase 1 : Thinking (déroulable, le contenu reste visible si on veut)
        with st.status("🔍 Le modèle réfléchit...", expanded=True) as status_box:
            translator = st.session_state.translator
            feedback = None
            errors = []
            last_model = None
            success = False
            attempt = 0

            while attempt < max_attempts:
                attempt += 1
                st.write(f"**Tentative {attempt}/{max_attempts}** — traduction & validation...")

                # 1. Appel LLM
                try:
                    raw = translator.translate(prompt, error_feedback=feedback)
                except Exception as exc:
                    st.write(f"❌ Échec appel LLM : {exc}")
                    errors.append(ErrorCategory.LLM_RESPONSE_ERROR)
                    break

                # 2. Parsing JSON
                model, parse_error, parse_category = parse_symbolic_model(raw)
                if model is None:
                    st.write(f"❌ JSON malformé : {parse_error}")
                    feedback = parse_error or "Réponse non conforme"
                    errors.append(parse_category or ErrorCategory.LLM_MALFORMED_JSON)
                    continue
                last_model = model

                # 3. Validation symbolique
                val_result, z3_vars = validate(model)
                if not val_result.is_valid:
                    st.write(f"❌ Validation : {val_result.message}")
                    feedback = (
                        f"Le modèle est invalide ({val_result.category.value if val_result.category else '?'}) : "
                        f"{val_result.message}"
                    )
                    if val_result.category is not None:
                        errors.append(val_result.category)
                    continue

                # Succès
                st.write("✅ Modèle symbolique validé")
                success = True
                break

            if not success:
                status_box.update(label="❌ Échec après tentatives", state="error", expanded=True)
                fail_msg = (
                    f"Impossible de produire un modèle valide après {attempt} tentative(s). "
                    f"Dernière erreur : {feedback or 'Inconnue'}"
                )
                st.error(fail_msg)
                st.session_state.messages.append({"role": "assistant", "content": fail_msg})
                st.stop()

            # 4. Résolution
            st.write("⚙️ Résolution par le backend symbolique...")
            solver_result = solve(last_model)

            # 5. Cohérence & statut final
            expected = last_model.expected_status
            if expected == "UNSAT":
                if solver_result.status == "UNSAT":
                    coherent, final_status = True, "UNSAT_PROVEN"
                elif solver_result.status == "SAT":
                    coherent, final_status = False, "UNSAT_BUT_SAT"
                else:
                    coherent, final_status = False, solver_result.status
            elif solver_result.status in ("SAT", "PDDL_PARSED"):
                coherent, final_status = True, solver_result.status
            elif solver_result.status == "UNSAT":
                coherent, final_status = True, "UNSAT"
            else:
                coherent, final_status = False, solver_result.status

            # 6. Interprétation NL
            st.write("📝 Génération de la réponse...")
            if use_llm_interp:
                try:
                    answer = interpret_with_llm(prompt, solver_result, last_model, translator)
                except Exception:
                    answer = interpret_without_llm(solver_result, last_model)
            else:
                answer = interpret_without_llm(solver_result, last_model)

            # On ferme le status mais on garde le label visible
            status_box.update(label="✅ Analyse terminée", state="complete", expanded=False)

        # ===================================================================
        # Phase 2 : RÉSULTAT AFFICHÉ DIRECTEMENT (hors du status déroulable)
        # ===================================================================
        result_payload = {
            "expected_status": expected or "SAT",
            "solver_status": solver_result.status,
            "final_status": final_status,
            "coherent": coherent,
            "attempts": attempt,
            "answer": answer,
            "formalism": last_model.formalism if last_model else "—",
        }
        render_result_card(result_payload)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "result": result_payload,
        })