# dtdict_parser

`dtdict_parser` est une bibliothèque Python conçue pour extraire automatiquement et structurer les données issues des déclarations de travaux **DT-DICT** (Déclaration de projet de Travaux - DT, Déclaration d'Intention de Commencement de Travaux - DICT, ou déclaration conjointe DT-DICT / Cerfa n° 14434*03).

Le projet transforme des fichiers hétérogènes en objets Python typés (dataclasses) facilitant l'intégration, la validation, le stockage en base de données géographique (PostGIS / GeoAlchemy) et l'analyse spatiale.

---

## 🎯 Fonctionnalités

### Formats supportés actuellement
- **Fichiers XML** : Extraction complète des métadonnées (responsable de projet, exécutant des travaux, emprise géographique GML convertie en WKT / Lambert-93 EPSG:2154, caractéristiques et calendrier du projet).
- **Fichiers PDF interactifs (AcroForm)** : Lecture directe des champs de formulaires PDF.
- **Fichiers PDF aplatis (Flattened PDF)** : Détection page par page des pages Cerfa 14434*03 et extraction des données par texte géolocalisé avec `pdfplumber`. Les pages contenant une emprise GML sont également lues et leur géométrie est associée aux déclarations extraites.
- **Images (JPEG, PNG, GIF, BMP, TIFF, WebP...)** : Une image est traitée comme une page. `ImageParser` vérifie par OCR le titre et le numéro Cerfa aux emplacements définis par `template_cerfa_detection.json`, puis utilise `template_14434_03.json` pour extraire les champs. Les cases à cocher sont détectées par leur taux de remplissage et les valeurs sont normalisées vers les dataclasses `DT` / `DICT`.
- **Inspection et lecture page par page** : `DocumentInspector.document_info` retourne une liste de dictionnaires contenant les informations de chaque page (`page_number`, `file_type`, `content_type`, `has_form_fields`). Un XML ou une image produit une seule entrée ; un PDF en produit une par page. `DocumentReader` charge chaque page dans un objet adapté au format, puis `parse_document()` la transmet au parser correspondant.
- **Détection des Cerfa** : Les parsers PDF et image utilisent les mêmes emplacements du gabarit `template_cerfa_detection.json` pour vérifier le titre et le numéro du Cerfa 14434*03. Pour les images, cette vérification est faite sur le texte reconnu par OCR.

#### Limites actuelles
- Les PDF scannés sans texte sont identifiés (`scanned_pdf`), mais leurs pages sont ignorées par le parsing avec un avertissement.
- L'image doit représenter une page A4 droite et cadrée (pas de redressement des photos ou scans penchés).
- L'emprise géographique (polygone GML, située en page 2 du PDF) n'est pas lue depuis une image : `emprise` reste à `None`.
- Les seuils de l'OCR (`MIN_OCR_SCORE`) et des cases à cocher (`CHECKBOX_FILL_THRESHOLD`) sont réglés sur des échantillons limités.
- Les formats image sont lus en une seule page ; les images multipages (par exemple certains TIFF) ne sont pas séparées en plusieurs pages.
- La détection de page Cerfa s'appuie sur un titre et un numéro fixes du formulaire 14434*03 ; les autres formulaires ne sont pas encore pris en charge.

### Évolutions prévues (Roadmap)
- [x] **Images** : Extraction via OCR des Cerfa numérisés (voir limites ci-dessus).
- [ ] **PDF scannés** : Extraction OCR des pages classées `scanned_pdf`.
- [ ] **Photos et scans non redressés** : Détection et correction de la perspective avant application du gabarit.
- [ ] **Archives compressées (`.zip`)** : Prise en charge des archives complètes issues du téléservice (contenant la déclaration XML, le Cerfa PDF et les plans d'emprise joints).
- [ ] **Détection multi-Cerfa** : Gestion et validation de plusieurs formulaires / déclarations dans un même document PDF, y compris leur association aux pages annexes.
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

### Inspection et parsing d'un document

```python
from pathlib import Path

from dt_dict_parser import DocumentInspector, parse_document

file_path = Path("chemin/vers/document.pdf")
for page_info in DocumentInspector(file_path).document_info:
    print(page_info)

declarations = parse_document(file_path)
```

`document_info` est une liste, avec une entrée par page. `parse_document()` lit le fichier, transmet chaque page au parser adapté et retourne les déclarations trouvées.

Le plan de test couvre :
- **Inspection des fichiers** : signatures d'images, extensions trompeuses, fichiers absents ou inconnus, types de contenu et structure de `document_info` page par page.
- **Lecture des pages** : une page par page PDF, et une page unique pour XML / image ; extraction des valeurs AcroForm associées aux pages.
- **Orchestration** : parsing XML et PDF AcroForm par `parse_document()`.
- **Parsers XML et AcroForm** : déclaration conjointe et DT seule, conversion des valeurs, géométrie XML en WKT et cohérence entre les données XML et PDF.
- **Parser PDF aplati** : conversion des valeurs du gabarit (texte, cases à cocher, dates) et nettoyage via le hook prévu.
- **Parser d'images** : détection Cerfa par OCR sur le titre et le numéro aux emplacements du gabarit, rejet d'une page ne correspondant pas au Cerfa, cases à cocher, valeurs OCR comparées à l'AcroForm, pages non A4 et fichier image illisible.
- **Modèles** : validation des numéros de consultation et des valeurs métier.

Les exemples sont dans `tests/testdata/`. Les tests avec OCR nécessitent PaddleOCR et OpenCV et peuvent prendre plusieurs secondes. Les PDF d'exemple ne couvrent pas encore un document multipage réel ; les tests actuels de lecture page par page utilisent un PDF d'une page.

---

## 📁 Arborescence du projet

```text
dtdict_parser/
├── pyproject.toml         # Configuration Poetry et liste des dépendances
├── README.md              # Documentation du projet
├── tests/                 # Tests unitaires
│   ├── conftest.py        # Fixtures : fichiers d'exemple, pages et résultats parsés
│   ├── testdata/          # XML, PDF AcroForm et JPG d'exemple
│   ├── test_document_inspector.py
│   ├── test_xml_and_acroform_parsers.py
│   ├── test_image_parser.py
│   └── test_models.py
└── src/
    ├── dt_dict_parser.py  # DocumentInspector, DocumentReader et parse_document
    ├── parsers/
    │   ├── base.py                 # Classe de base des parsers
    │   ├── xml_parser.py           # Parser XML
    │   ├── acroform_pdf_parser.py  # Parser PDF interactif
    │   ├── flattened_pdf_parser.py # Parser PDF aplati (gabarit + pdfplumber)
    │   └── image_parser.py         # Parser d'images (gabarit + OCR)
    ├── models/
    │   ├── models.py      # Dataclasses et énumérations métier (DT, DICT, Acteur...)
    │   ├── pages.py       # Objets page remis aux parsers
    │   └── *.json         # Modèles et gabarits de détection Cerfa
    └── dev_tools/         # Outils de développement et échantillons de test
```

---

## 📝 Licence

Projet personnel en cours de développement.