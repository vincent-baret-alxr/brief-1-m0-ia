import json
import sys
from pathlib import Path
from typing import Any

import streamlit as st


# Ajoute la racine du projet au PYTHONPATH pour permettre l'import
# depuis le dossier app lorsque Streamlit est lancé avec :
# streamlit run ui/streamlit_app.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.model_client import ModelClient  # noqa: E402


EXAMPLE_REPORT = (
    "Pompe P-204 en zone A. Une vibration importante est constatée "
    "depuis deux jours. La température est anormalement élevée et "
    "un bruit métallique apparaît au démarrage."
)


st.set_page_config(
    page_title="DiagOps",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource(show_spinner=False)
def load_model() -> ModelClient:
    """
    Charge Qwen une seule fois.

    Sans ce cache, Streamlit rechargerait le modèle à chaque
    interaction avec l'interface.
    """
    return ModelClient()


def format_severity(severity: Any) -> str:
    """
    Traduit les valeurs de sévérité retournées par le modèle.
    """
    labels = {
        "low": "Faible",
        "medium": "Moyenne",
        "high": "Élevée",
        "critical": "Critique",
    }

    if severity is None:
        return "Non renseignée"

    normalized_severity = str(severity).strip().lower()

    return labels.get(
        normalized_severity,
        str(severity),
    )


def format_confidence(confidence: Any) -> str:
    """
    Convertit une confiance comprise entre 0 et 1 en pourcentage.
    """
    try:
        value = float(confidence)
    except (TypeError, ValueError):
        return "Non renseigné"

    if 0 <= value <= 1:
        value *= 100

    return f"{value:.0f} %"


def format_boolean(value: Any) -> str:
    """
    Affiche une valeur booléenne en français.
    """
    if value is True:
        return "Oui"

    if value is False:
        return "Non"

    return "Non renseigné"


def display_text(value: Any) -> str:
    """
    Retourne une valeur lisible ou un texte par défaut.
    """
    if value is None:
        return "Non renseigné"

    text = str(value).strip()

    return text if text else "Non renseigné"


def display_diagnosis(diagnosis: dict[str, Any]) -> None:
    """
    Affiche le diagnostic retourné par ModelClient.diagnose().
    """
    st.success("Analyse terminée.")

    severity = diagnosis.get("severity")
    confidence = diagnosis.get("confidence")
    requires_human_review = diagnosis.get(
        "requires_human_review"
    )

    severity_column, confidence_column, review_column = st.columns(3)

    with severity_column:
        st.metric(
            label="Sévérité",
            value=format_severity(severity),
        )

    with confidence_column:
        st.metric(
            label="Niveau de confiance",
            value=format_confidence(confidence),
        )

    with review_column:
        st.metric(
            label="Validation humaine requise",
            value=format_boolean(requires_human_review),
        )

    st.divider()

    diagnosis_column, action_column = st.columns(
        2,
        gap="large",
    )

    with diagnosis_column:
        st.subheader("Diagnostic")

        st.markdown("#### Symptôme identifié")
        st.write(
            display_text(
                diagnosis.get("symptom")
            )
        )

        st.markdown("#### Hypothèse de panne")
        st.write(
            display_text(
                diagnosis.get("failure_hypothesis")
            )
        )

    with action_column:
        st.subheader("Recommandation")

        st.markdown("#### Action de maintenance recommandée")
        st.write(
            display_text(
                diagnosis.get("recommended_action")
            )
        )

        st.markdown("#### Contrôle humain")
        st.write(
            (
                "Le diagnostic doit être vérifié par un technicien."
                if requires_human_review is True
                else "Aucune validation humaine n'a été demandée."
            )
        )

    with st.expander("Afficher la réponse JSON"):
        st.code(
            json.dumps(
                diagnosis,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            language="json",
        )


st.title("🛠️ DiagOps")

st.markdown(
    """
    ### Assistant de diagnostic de maintenance industrielle

    Saisissez un rapport technicien pour générer une première
    hypothèse de panne et une recommandation de maintenance.
    """
)

st.warning(
    "Le diagnostic généré par le modèle constitue une aide à la décision. "
    "Il ne remplace pas l'analyse d'un technicien qualifié."
)


# La valeur du champ est conservée dans session_state afin de pouvoir
# remplir correctement le rapport d'exemple.
if "technician_note" not in st.session_state:
    st.session_state["technician_note"] = ""


example_column, clear_column = st.columns(
    [1, 1],
)

with example_column:
    if st.button(
        "Utiliser un exemple",
        use_container_width=True,
    ):
        st.session_state["technician_note"] = EXAMPLE_REPORT
        st.rerun()

with clear_column:
    if st.button(
        "Effacer le rapport",
        use_container_width=True,
    ):
        st.session_state["technician_note"] = ""
        st.session_state.pop("diagnosis", None)
        st.rerun()


with st.form(
    key="diagnosis_form",
    clear_on_submit=False,
):
    technician_note = st.text_area(
        label="Rapport technicien",
        key="technician_note",
        placeholder=(
            "Décrivez l'équipement concerné, les symptômes observés, "
            "les bruits, les vibrations, les températures ou les "
            "mesures relevées..."
        ),
        height=220,
        max_chars=3000,
    )

    submitted = st.form_submit_button(
        label="Analyser le rapport",
        type="primary",
        use_container_width=True,
    )


if submitted:
    cleaned_note = technician_note.strip()

    if not cleaned_note:
        st.warning(
            "Veuillez saisir un rapport technicien avant de lancer "
            "l'analyse."
        )
    else:
        try:
            with st.spinner(
                "Chargement du modèle et analyse du rapport..."
            ):
                model_client = load_model()

                # Ton ModelClient attend directement une chaîne de caractères
                # et retourne déjà un dictionnaire.
                diagnosis = model_client.diagnose(
                    cleaned_note
                )

            if not isinstance(diagnosis, dict):
                raise TypeError(
                    "ModelClient.diagnose() doit retourner "
                    "un dictionnaire."
                )

            st.session_state["diagnosis"] = diagnosis

        except Exception as error:
            st.session_state.pop("diagnosis", None)

            st.error(
                "Une erreur est survenue pendant l'analyse du rapport."
            )

            with st.expander("Afficher le détail technique"):
                st.exception(error)


if "diagnosis" in st.session_state:
    display_diagnosis(
        st.session_state["diagnosis"]
    )
