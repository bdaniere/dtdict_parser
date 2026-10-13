# dtdict_parser

`dtdict_parser` est une bibliothèque Python conçue pour extraire automatiquement et structurer les données issues des déclarations de travaux **DT-DICT** (Déclaration de projet de Travaux - DT, Déclaration d'Intention de Commencement de Travaux - DICT, ou déclaration conjointe DT-DICT / Cerfa n° 14434*03).

Le projet transforme des fichiers hétérogènes en objets Python typés (dataclasses) facilitant l'intégration, la validation, le stockage en base de données géographique (PostGIS / GeoAlchemy) et l'analyse spatiale.

---

## 🎯 Fonctionnalités

### Formats supportés actuellement
- **Fichiers XML** : Extraction complète des métadonnées (responsable de projet, exécutant des travaux, emprise géographique GML convertie en WKT / Lambert-93 EPSG:2154, caractéristiques et calendrier du projet).
- **Fichiers PDF interactifs (AcroForm)** : Lecture directe des champs de formulaires PDF.
- **Fichiers PDF aplatis (Flattened PDF)** : Détection des gabarits Cerfa 14434*03, extraction de texte géolocalisé sur la page via `pdfplumber` et vectorisation des emprises.
- **Inspection automatique** : La classe `DocumentInspector` qualifie automatiquement le type de fichier (`pdf`, `xml`) et la nature de son contenu (`acroform_pdf`, `flattened_pdf`, `scanned_pdf`, `xml`).

### Évolutions prévues (Roadmap)
- [ ] **Documents scannés et images** : Extraction via OCR et vision par ordinateur pour traiter les Cerfa numérisés ou photographiés.
- [ ] **Archives compressées (`.zip`)** : Prise en charge des archives complètes issues du téléservice (contenant la déclaration XML, le Cerfa PDF et les plans d'emprise joints).
- [ ] **Détection multi-Cerfa** : Prise en charge de plusieurs déclarations au sein d'un même document PDF.
- [ ] **Interface CLI et export JSON/GeoJSON** : Outils en ligne de commande pour faciliter l'intégration dans des pipelines de traitement batch.

---

## 📦 Structure des données extraites

Les données sont restituées sous forme de dataclasses Python modulaires :
- `DT` / `DICT` : Modèles principaux décrivant la déclaration (type, numéro de consultation, dates).
- `Acteur` : Informations sur le déclarant, le responsable du projet ou l'exécutant des travaux (coordonnées, SIRET, contact).
- `Emprise` : Géométrie (WKT) et informations cadastrales / communales.
- `ProjetEtSonCalendrier` / `TravauxEtLeurCalendrier` : Nature des travaux, calendrier, profondeur d'excavation, techniques utilisées.
- `SouhaitsPourLeRecepisse` : Modalités de réponse attendues (électronique, papier, formats vectoriels).

---

## 🛠️ Prérequis

- **Python** : `~3.13`
- **Poetry** : Gestionnaire de dépendances et d'environnements virtuels Python ([documentation officielle](https://python-poetry.org/docs/))

---

## 🚀 Installation avec Poetry

### 1. Installer Poetry (si nécessaire)

Si Poetry n'est pas encore installé sur votre système :

```bash
# Sous Linux / macOS / WSL
curl -sSL https://install.python-poetry.org | python3 -

# Sous Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Vérifiez l'installation :

```bash
poetry --version
```

### 2. Cloner le dépôt et installer les dépendances

Clonez le projet et placez-vous dans le répertoire :

```bash
cd dtdict_parser
```

Installez l'environnement et l'ensemble des dépendances spécifiées dans `pyproject.toml` :

```bash
poetry install
```

Poetry créera automatiquement un environnement virtuel dédié et y installera les dépendances (`pdfplumber`, `pypdf`, `geopandas`, `shapely`, `pyproj`, `sqlalchemy`, etc.).

---

## 💻 Utilisation

### Activer l'environnement virtuel

Pour exécuter des commandes ou lancer un shell dans le contexte de l'environnement virtuel créé par Poetry :

```bash
# Entrer dans l'environnement virtuel
poetry shell

# Ou exécuter un script directement via Poetry
poetry run python src/dt_dict_parser.py

---

## 📁 Arborescence du projet

```text
dtdict_parser/
├── pyproject.toml         # Configuration Poetry et liste des dépendances
├── README.md              # Documentation du projet
└── src/
    ├── dt_dict_parser.py  # Moteurs d'inspection et parsers (PDF, XML)
    ├── models/
    │   ├── models.py      # Dataclasses et énumérations métier (DT, DICT, Acteur...)
    │   └── *.json         # Modèles et gabarits de détection Cerfa
    └── dev_tools/         # Outils de développement et échantillons de test
```

---

## 📝 Licence

Projet personnel en cours de développement.