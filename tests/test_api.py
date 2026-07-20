from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@patch("app.main.model_client.diagnose")
def test_diagnose_returns_structured_result(mock_diagnose) -> None:
    mock_diagnose.return_value = {
        "symptom": "Vibrations importantes au démarrage de la pompe",
        "severity": "high",
        "failure_hypothesis": (
            "Usure probable d'un roulement ou défaut d'alignement."
        ),
        "recommended_action": (
            "Contrôler les roulements et vérifier l'alignement de l'arbre."
        ),
        "confidence": 0.85,
        "requires_human_review": True,
    }

    response = client.post(
        "/diagnose",
        json={
            "technician_note": (
                "La pompe présente de fortes vibrations et une température "
                "anormale au démarrage."
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["symptom"] == (
        "Vibrations importantes au démarrage de la pompe"
    )
    assert result["severity"] == "high"
    assert result["confidence"] == 0.85
    assert result["requires_human_review"] is True

    mock_diagnose.assert_called_once_with(
        "La pompe présente de fortes vibrations et une température "
        "anormale au démarrage."
    )


def test_diagnose_rejects_empty_note() -> None:
    response = client.post(
        "/diagnose",
        json={"technician_note": ""},
    )

    assert response.status_code == 422


def test_diagnose_rejects_missing_note() -> None:
    response = client.post(
        "/diagnose",
        json={},
    )

    assert response.status_code == 422