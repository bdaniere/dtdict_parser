# dtdict_parser

`dtdict_parser` est une bibliothèque Python conçue pour extraire automatiquement et structurer les données issues des déclarations de travaux **DT-DICT** (Déclaration de projet de Travaux - DT, Déclaration d'Intention de Commencement de Travaux - DICT, ou déclaration conjointe DT-DICT / Cerfa n° 14434*03).

Le projet transforme des fichiers hétérogènes en objets Python typés (dataclasses) facilitant l'intégration, la validation, le stockage en base de données géographique (PostGIS / GeoAlchemy) et l'analyse spatiale.

---

## 🎯 Fonctionnalités

### Formats supportés actuellement
- **Fichiers XML** : Extraction complète des métadonnées (responsable de projet, exécutant des travaux, emprise géographique GML convertie en WKT / Lambert-93 EPSG:2154, caractéristiques et calendrier du projet).
- **Fichiers PDF interactifs (AcroForm)** : Lecture directe des champs de formulaires PDF.
- **Fichiers PDF aplatis (Flattened PDF)** : Détection des gabarits Cerfa 14434*03, extraction de texte géolocalisé sur la page via `pdfplumber` et vectorisation des emprises.
- **Images (JPEG, PNG, GIF, BMP, TIFF, WebP...)** : Lecture d'une page de Cerfa 14434*03 au format A4. `ImageParser` réutilise le gabarit `template_14434_03.json` comme pour les PDF aplatis : chaque zone du gabarit est découpée dans l'image puis lue par OCR (PaddleOCR), les cases à cocher sont détectées par leur taux de remplissage, et les valeurs sont normalisées vers les dataclasses `DT` / `DICT`.
- **Inspection automatique** : La classe `DocumentInspector` qualifie automatiquement le type de fichier (`pdf`, `image`, `xml`) et la nature de son contenu (`acroform_pdf`, `flattened_pdf`, `scanned_pdf`, `image`, `xml`). Les images sont reconnues par leur signature binaire (et non par leur extension).

#### Limites actuelles du parser d'images
- L'image doit représenter une page A4 droite et cadrée (pas de redressement des photos ou scans penchés).
- L'emprise géographique (polygone GML, située en page 2 du PDF) n'est pas lue depuis une image : `emprise` reste à `None`.
- Les seuils de l'OCR (`MIN_OCR_SCORE`) et des cases à cocher (`CHECKBOX_FILL_THRESHOLD`) sont réglés sur des échantillons limités.

### Évolutions prévues (Roadmap)
- [x] **Images** : Extraction via OCR des Cerfa numérisés (voir limites ci-dessus).
- [ ] **PDF scannés** : Les PDF sans texte (`scanned_pdf`) ne sont pas encore traités.
- [ ] **Photos et scans non redressés** : Détection et correction de la perspective avant application du gabarit.
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

Poetry créera automatiquement un environnement virtuel dédié et y installera les dépendances (`pdfplumber`, `pypdf`, `geopandas`, `shapely`, `pyproj`, `sqlalchemy`, `paddleocr` / `paddlepaddle` et `opencv-python-headless` pour l'OCR, etc.).

> Au premier lancement, PaddleOCR télécharge ses modèles (mis en cache dans `~/.paddlex`).

---

## 💻 Utilisation

### Activer l'environnement virtuel

Pour exécuter des commandes ou lancer un shell dans le contexte de l'environnement virtuel créé par Poetry :

```bash
# Entrer dans l'environnement virtuel
poetry shell

# Ou exécuter un script directement via Poetry
poetry run python src/dt_dict_parser.py
```

Pour lancer les tests :

```bash
poetry install   # installe aussi pytest (groupe dev)
poetry run pytest
```

Le plan de test couvre : la détection des types de fichiers, les parsers XML et AcroForm
(valeurs, cohérence PDF/XML, DT seule), la conversion commune des valeurs du gabarit et le
parser d'images (cases à cocher, valeurs OCR comparées à l'AcroForm, images invalides).
Les tests du parser d'images sont ignorés si `paddleocr` / `opencv` sont absents, et prennent
une dizaine de secondes (OCR). Les fichiers d'exemple sont dans `tests/testdata/`.

---

## 📁 Arborescence du projet

```text
dtdict_parser/
├── pyproject.toml         # Configuration Poetry et liste des dépendances
├── README.md              # Documentation du projet
├── tests/                 # Tests unitaires
│   ├── conftest.py        # Fixtures : fichiers d'exemple et résultats parsés (OCR une seule fois)
│   ├── testdata/          # XML, PDF AcroForm et JPG d'exemple
│   ├── test_document_inspector.py
│   ├── test_xml_and_acroform_parsers.py
│   └── test_image_parser.py
└── src/
    ├── dt_dict_parser.py  # DocumentInspector et point d'entrée
    ├── parsers/
    │   ├── base.py                 # Classe de base des parsers
    │   ├── xml_parser.py           # Parser XML
    │   ├── acroform_pdf_parser.py  # Parser PDF interactif
    │   ├── flattened_pdf_parser.py # Parser PDF aplati (gabarit + pdfplumber)
    │   └── image_parser.py         # Parser d'images (gabarit + OCR)
    ├── models/
    │   ├── models.py      # Dataclasses et énumérations métier (DT, DICT, Acteur...)
    │   └── *.json         # Modèles et gabarits de détection Cerfa
    └── dev_tools/         # Outils de développement et échantillons de test
```

---

## 📝 Licence

Projet personnel en cours de développement.