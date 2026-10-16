from datetime import date

import pytest

from parsers.flattened_pdf_parser import FlattenedPDFParser

CHECKED_BOXES = [
    "DT.typeEntite_PERSONNE_MORALE",
    "DT.declarationConjointeDTDICT",
    "DT.projetEtSonCalendrier.emploiDeTechniquesSansTranchees_false",
    "DICT.travauxEtLeurCalendrier.communicationResultatsInvestigations_false",
]
UNCHECKED_BOXES = [
    "DT.typeEntite_PERSONNE_PHYSIQUE",
    "DT.projetEtSonCalendrier.emploiDeTechniquesSansTranchees_true",
    "DICT.travauxEtLeurCalendrier.communicationResultatsInvestigations_true",
    "DT.investigationsComplementaires.realisationDInvestigationsComplementaires_false",
    "DICT.travauxEtLeurCalendrier.modificationProfilTerrain",
]


@pytest.fixture
def flattened_parser(conjointe_pdf):
    parser = FlattenedPDFParser(conjointe_pdf)
    parser.template_cerfa = {
        "fields": {
            "DT.texte": {"type": "text"},
            "DT.vide": {"type": "text"},
            "DT.date": {"type": "date"},
            "DT.date_invalide": {"type": "date"},
            "DICT.case": {"type": "checkbox"},
            "DICT.case_vide": {"type": "checkbox"},
        }
    }
    return parser


def test_fill_results_converts_values_by_field_type(flattened_parser):
    texts = {
        "DT.texte": "abc",
        "DT.vide": "",
        "DT.date": "08 / 10 / 2026",
        "DT.date_invalide": "n'importe quoi",
        "DICT.case": "X",
        "DICT.case_vide": "",
    }

    results = flattened_parser._fill_results({"DT": {}, "DICT": {}}, texts)

    assert results == {
        "DT": {
            "texte": "abc",
            "vide": None,
            "date": date(2026, 10, 8),
            "date_invalide": None,
        },
        "DICT": {"case": True, "case_vide": False},
    }


def test_fill_results_applies_the_clean_text_hook(flattened_parser):
    flattened_parser._clean_text = lambda name, text: text.upper()
    texts = {name: "" for name in flattened_parser.template_cerfa["fields"]}
    texts["DT.texte"] = "abc"

    results = flattened_parser._fill_results({"DT": {}, "DICT": {}}, texts)

    assert results["DT"]["texte"] == "ABC"


def _is_checked(parser, field_name):
    return parser._is_checked(parser.template_cerfa["fields"][field_name]["bbox"])


@pytest.mark.parametrize("field_name", CHECKED_BOXES)
def test_checked_boxes_are_detected(image_parser, field_name):
    assert _is_checked(image_parser, field_name)


@pytest.mark.parametrize("field_name", UNCHECKED_BOXES)
def test_unchecked_boxes_are_detected(image_parser, field_name):
    assert not _is_checked(image_parser, field_name)


def test_pixel_conversion_scales_with_image_size(image_parser):
    height, width = image_parser.image.shape[:2]

    assert image_parser._to_pixels([0, 0, 595, 842]) == (0, 0, width, height)


def test_image_gives_a_dt_and_a_dict(image_declarations):
    dt, dict_ = image_declarations

    assert dt.declaration_type.value == "CONJOINTE"
    assert dict_.declaration_type.value == "DICT"


def test_image_texts_match_the_acroform_values(image_declarations, acroform_declarations):
    dt, _ = image_declarations
    expected_dt, _ = acroform_declarations

    assert dt.noConsultationDuTeleservice == "2026100801380T"
    assert dt.dateDeLaDeclaration == date(2026, 10, 8)
    assert dt.noAffaireDuResponsableDuProjet == "num_affaore"
    assert dt.representantDuResponsableDeProjet == expected_dt.representantDuResponsableDeProjet
    assert dt.projetEtSonCalendrier.dureeDuChantierEnJours == 5
    assert dt.projetEtSonCalendrier.datePrevuePourLeCommencementDesTravaux == date(2026, 10, 23)
    assert (
        dt.signatureDuResponsableDuProjetOuDeSonRepresentant
        == expected_dt.signatureDuResponsableDuProjetOuDeSonRepresentant
    )


def test_image_comb_fields_are_cleaned_of_separators(image_declarations):
    executant = image_declarations[1].executantDesTravaux

    assert executant.codePostal == "38080"
    assert executant.noSiret == "39927837300010"
    assert executant.tel == "0689230191"


def test_image_checkboxes_are_converted(image_declarations):
    dt = image_declarations[0]

    assert dt.declarationConjointeDTDICT
    assert dt.projetEtSonCalendrier.souhaitLesPlansDesReseauxElectriqueAeriens


def test_image_geometry_is_not_read(image_declarations):
    assert image_declarations[0].emprise is None


def test_image_empty_fields_are_none(image_declarations):
    dt = image_declarations[0]

    assert dt.noConsultationDuTeleserviceSeize is None
    assert dt.responsableDuProjet.noSiret is None
    assert dt.responsableDuProjet.codePostal is None


@pytest.fixture
def blank_image(tmp_path):
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")

    def write(width, height):
        path = tmp_path / "blank.png"
        cv2.imwrite(str(path), np.full((height, width, 3), 255, dtype=np.uint8))
        return path

    return write


def test_unreadable_image_raises(image_parser, tmp_path):
    path = tmp_path / "broken.png"
    path.write_bytes(b"not an image")

    with pytest.raises(ValueError):
        type(image_parser)(path)


def test_non_a4_image_is_rejected(image_parser, blank_image):
    parser = type(image_parser)(blank_image(1000, 1000))

    with pytest.raises(NotImplementedError):
        parser.read_content()


def test_a4_image_without_cerfa_gives_no_declaration(image_parser, blank_image):
    parser = type(image_parser)(blank_image(595, 842))

    assert parser.read_content() == []
