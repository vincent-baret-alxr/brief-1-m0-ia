import json
import re
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


class ModelClient:
    def __init__(self) -> None:
        self.device = self._get_device()

        print(f"Chargement de {MODEL_NAME} sur {self.device}...")

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=(
                torch.float16
                if self.device == "mps"
                else torch.float32
            ),
        )

        self.model = self.model.to(self.device)
        self.model.eval()

    @staticmethod
    def _get_device() -> str:
        if torch.backends.mps.is_available():
            return "mps"

        return "cpu"

    def diagnose(self, technician_note: str) -> dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "Tu es un assistant de diagnostic en maintenance industrielle. "
                    "Tu réponds obligatoirement en français. "
                    "Toutes les valeurs textuelles du JSON doivent être rédigées "
                    "en français, même si le rapport contient des mots anglais. "
                    "Tu analyses uniquement les informations présentes dans le rapport. "
                    "Tu proposes une hypothèse prudente et tu ne présentes jamais "
                    "ton diagnostic comme une certitude."
                ),
            },
            {
                "role": "user",
                "content": self._build_prompt(technician_note),
            },
        ]

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=300,
                do_sample=False,
            )

        response_ids = generated_ids[
            0,
            inputs["input_ids"].shape[1] :,
        ]

        generated_text = self.tokenizer.decode(
            response_ids,
            skip_special_tokens=True,
        )

        return self._parse_json(generated_text)

    @staticmethod
    def _build_prompt(technician_note: str) -> str:
        return f"""
Tu dois analyser un rapport de maintenance industrielle et produire
un diagnostic technique concret.

Règles importantes :

- Appuie chaque hypothèse sur les symptômes réellement présents.
- Identifie un composant ou une cause technique plausible.
- Ne retourne jamais une formule générique comme :
  "panne prudente",
  "problème mécanique",
  "dysfonctionnement possible",
  "contrôle supplémentaire".
- Si plusieurs causes sont possibles, indique la cause principale,
  puis les alternatives les plus plausibles.
- L'action recommandée doit permettre de confirmer ou corriger
  l'hypothèse.
- N'invente aucune observation absente du rapport.
- Le diagnostic reste une hypothèse et doit être validé par un humain.

Exemple :

Rapport :
Pompe de dosage. Débit inférieur à la consigne malgré une vanne ouverte.
Aucune fuite visible. Le filtre amont semble encrassé.

Réponse attendue :
{{
  "symptom": "Débit de la pompe inférieur à la consigne malgré l'ouverture de la vanne",
  "severity": "medium",
  "failure_hypothesis": "Colmatage probable du filtre amont limitant l'alimentation de la pompe. Une obstruction de la conduite d'aspiration ou une perte de performance de la pompe restent également possibles.",
  "recommended_action": "Contrôler puis nettoyer ou remplacer le filtre amont, vérifier la pression d'aspiration et mesurer le débit après remise en service.",
  "confidence": 0.85,
  "requires_human_review": true
}}

Analyse maintenant le rapport suivant :

--- RAPPORT ---
{technician_note}
--- FIN DU RAPPORT ---

Retourne uniquement un objet JSON valide avec exactement ces champs :

{{
  "symptom": "description précise du symptôme observé",
  "severity": "low, medium, high ou critical",
  "failure_hypothesis": "cause technique principale et éventuelles alternatives",
  "recommended_action": "contrôles et actions de maintenance concrètes",
  "confidence": 0.0,
  "requires_human_review": true
}}

Contraintes de sortie :

- Aucun texte avant ou après le JSON.
- Toutes les valeurs textuelles doivent être rédigées en français.
- N'utilise aucun mot ni aucune phrase en anglais.
- severity doit être low, medium, high ou critical.
- confidence doit être un nombre compris entre 0 et 1.
- requires_human_review doit toujours être true.
- N'invente pas d'identifiant d'équipement.
"""

    @staticmethod
    def _parse_json(generated_text: str) -> dict[str, Any]:
        match = re.search(r"\{.*\}", generated_text, re.DOTALL)

        if match is None:
            raise ValueError(
                "Le modèle n'a pas retourné d'objet JSON."
            )

        try:
            return json.loads(match.group())
        except json.JSONDecodeError as error:
            raise ValueError(
                "Le modèle a retourné un JSON invalide."
            ) from error