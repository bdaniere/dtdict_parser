from datetime import date

from models.models import DICT, DT, DeclarationType, NatureProjet, TechniqueTravaux
from parsers.acroform_pdf_parser import AcroformPDFParser
from parsers.xml_parser import XMLParser


def test_xml_joint_declaration_gives_a_dt_and_a_dict(xml_declarations):
    dt, dict_ = xml_declarations

    assert isinstance(dt, DT)
    assert isinstance(dict_, DICT)
    assert dt.declaration_type == DeclarationType.CONJOINTE
    assert dict_.declaration_type == DeclarationType.DICT
    assert dt.noConsultationDuTeleservice == "2026100801380T"
    assert dict_.noConsultationDuTeleservice == "2026100801380T"


def test_xml_geometry_is_reprojected_to_wkt(xml_declarations):
    assert xml_declarations[0].emprise.geometrie.startswith("POLYGON ((")


def test_xml_dt_only_declaration(dt_xml):
    declarations = XMLParser(dt_xml).read_content()

    assert len(declarations) == 1
    assert declarations[0].declaration_type == DeclarationType.DT
    assert declarations[0].noConsultationDuTeleserviceSeize == "2026100801140TJG"


def test_acroform_joint_declaration_gives_a_dt_and_a_dict(acroform_declarations):
    dt, dict_ = acroform_declarations

    assert dt.declaration_type == DeclarationType.CONJOINTE
    assert dict_.declaration_type == DeclarationType.DICT
    assert dt.noConsultationDuTeleservice == "2026100801380T"
    assert dt.dateDeLaDeclaration.date() == date(2026, 10, 8)


def test_acroform_values_are_converted_to_their_model_types(acroform_declarations):
    dt, dict_ = acroform_declarations

    assert dt.projetEtSonCalendrier.datePrevuePourLeCommencementDesTravaux == date(2026, 10, 23)
    assert dt.projetEtSonCalendrier.dureeDuChantierEnJours == 5
    assert dt.projetEtSonCalendrier.natureDesTravaux == [NatureProjet.SOU, NatureProjet.RBL]
    assert dict_.travauxEtLeurCalendrier.profondeurMaxDExcavation == 10.0
    assert dict_.travauxEtLeurCalendrier.techniquesUtilisees == [TechniqueTravaux.VIB]
    assert dict_.executantDesTravaux.noSiret == "39927837300010"


def test_pdf_and_xml_agree_on_the_same_declaration(xml_declarations, acroform_declarations):
    xml_dt, xml_dict = xml_declarations
    pdf_dt, pdf_dict = acroform_declarations

    assert xml_dt.noConsultationDuTeleservice == pdf_dt.noConsultationDuTeleservice
    assert (
        xml_dt.signatureDuResponsableDuProjetOuDeSonRepresentant
        == pdf_dt.signatureDuResponsableDuProjetOuDeSonRepresentant
    )
    assert xml_dict.executantDesTravaux == pdf_dict.executantDesTravaux
    assert (
        xml_dt.projetEtSonCalendrier.natureDesTravaux
        == pdf_dt.projetEtSonCalendrier.natureDesTravaux
    )


def test_acroform_dt_only_declaration(dt_pdf):
    dt = AcroformPDFParser(dt_pdf).read_content()[0]

    assert dt.declaration_type == DeclarationType.DT
    assert dt.noConsultationDuTeleservice == "2026100801140TJG"
