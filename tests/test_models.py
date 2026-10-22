from datetime import date

import pytest

from models.models import DICT, DT, Declaration, DeclarationType


@pytest.mark.parametrize(
    "numero",
    [
        "2026100801380T",
        "2026100801140TJG",
        "2026100801140Ta9",
    ],
)
def test_declaration_accepts_valid_consultation_number(numero):
    declaration = Declaration(
        declaration_type=DeclarationType.DT,
        mainNoConsultationDuTeleservice=numero,
        dateDeLaDeclaration=date(2026, 10, 8),
    )

    assert declaration.mainNoConsultationDuTeleservice == numero


@pytest.mark.parametrize(
    "numero",
    [
        None,
        "",
        "2026100801380",
        "20261008013800T",
        "2026100801380TTT9",
        "2026023001380T",
        "2026AA0801380T",
    ],
)
def test_declaration_rejects_invalid_consultation_number(numero):
    with pytest.raises(ValueError, match="mainNoConsultationDuTeleservice"):
        Declaration(
            declaration_type=DeclarationType.DT,
            mainNoConsultationDuTeleservice=numero,
            dateDeLaDeclaration=date(2026, 10, 8),
        )


def test_declaration_requires_consultation_number():
    with pytest.raises(ValueError):
        Declaration(
            declaration_type=DeclarationType.DT,
            dateDeLaDeclaration=date(2026, 10, 8),
        )


@pytest.mark.parametrize(
    "numero", ["2026100801140T", "2026100801140T1", "2026100801140TJG"]
)
def test_dt_accepts_valid_seize_consultation_number(numero):
    declaration = DT(
        declaration_type=DeclarationType.DT,
        mainNoConsultationDuTeleservice="2026100801380T",
        dateDeLaDeclaration=date(2026, 10, 8),
        noConsultationDuTeleserviceSeize=numero,
    )

    assert declaration.noConsultationDuTeleserviceSeize == numero


@pytest.mark.parametrize(
    "numero",
    ["", "2026100801140", "20261008011400T", "2026023001140T", "2026100801140T?"],
)
def test_dt_rejects_invalid_seize_consultation_number(numero):
    with pytest.raises(ValueError, match="noConsultationDuTeleserviceSeize"):
        DT(
            declaration_type=DeclarationType.DT,
            mainNoConsultationDuTeleservice="2026100801380T",
            dateDeLaDeclaration=date(2026, 10, 8),
            noConsultationDuTeleserviceSeize=numero,
        )


def test_dt_allows_missing_seize_consultation_number():
    declaration = DT(
        declaration_type=DeclarationType.CONJOINTE,
        mainNoConsultationDuTeleservice="2026100801380T",
        dateDeLaDeclaration=date(2026, 10, 8),
    )

    assert declaration.noConsultationDuTeleserviceSeize is None


def test_dict_main_number_comes_from_its_own_consultation_number():
    declaration = DICT(
        declaration_type=DeclarationType.DICT,
        dateDeLaDeclaration=date(2026, 10, 8),
        noConsultationDuTeleservice="2026100801380T",
    )

    assert declaration.mainNoConsultationDuTeleservice == "2026100801380T"


def test_dt_main_number_comes_from_the_seize_number():
    declaration = DT(
        declaration_type=DeclarationType.DT,
        dateDeLaDeclaration=date(2026, 10, 8),
        noConsultationDuTeleserviceSeize="2026100801140TJG",
    )

    assert declaration.mainNoConsultationDuTeleservice == "2026100801140TJG"
