# DiagOps M0

DiagOps M0 est une application de démonstration permettant de générer une première hypothèse de diagnostic à partir d'un rapport de maintenance industrielle à l'aide d'un modèle de langage local (Qwen 2.5).

L'interface utilisateur est développée avec **Streamlit** et le modèle est exécuté localement via **Transformers**.

---

## Prérequis

- Python 3.11 ou supérieur
- Git
- Environnement virtuel Python (`venv`)

---

## Installation

### 1. Cloner le dépôt

```bash
git clone <url-du-repository>
cd diagops
```

### 2. Créer un environnement virtuel

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## Lancer l'application

Depuis la racine du projet :

```bash
streamlit run ui/streamlit_app.py
```

Une fois l'application démarrée, Streamlit affiche une URL similaire à :

```
http://localhost:8501
```

Ouvrir cette adresse dans un navigateur.

---

## Premier lancement

Lors du premier démarrage :

* le modèle **Qwen/Qwen2.5-0.5B-Instruct** est téléchargé automatiquement depuis Hugging Face ;
* le téléchargement peut prendre quelques minutes selon la connexion Internet ;
* les lancements suivants sont beaucoup plus rapides grâce au cache local de Hugging Face.

---

## Structure du projet

```
diagops/
│
├── app/
│   ├── model_client.py
│   ├── schemas.py
│   └── ...
│
├── ui/
│   └── streamlit_app.py
│
├── requirements.txt
└── README.md
```

---

## Utilisation

1. Saisir un rapport technicien dans la zone de texte.
2. Cliquer sur **Analyser le rapport**.
3. Le modèle génère :

   * les symptômes identifiés ;
   * le niveau de sévérité ;
   * une hypothèse de panne ;
   * une action de maintenance recommandée ;
   * un niveau de confiance ;
   * un indicateur de validation humaine.

Le diagnostic constitue une aide à la décision et doit être validé par un technicien.

---

## Dépendances principales

* Streamlit
* PyTorch
* Transformers
* Hugging Face
* Pydantic

---

## Arrêter l'application

Dans le terminal exécutant Streamlit :

```
Ctrl + C
```
