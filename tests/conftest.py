"""Shared fixtures: sample documents and parsed results (OCR is run once per session)."""

import os
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
TESTDATA = Path(__file__).resolve().parent / "testdata"


@pytest.fixture(scope="session", autouse=True)
def _run_from_src():
    # The parsers load their templates with paths relative to src/.
    previous = Path.cwd()
    os.chdir(SRC)
    yield
    os.chdir(previous)


@pytest.fixture(scope="session")
def conjointe_xml() -> Path:
    return TESTDATA / "dt_dict_conjointe.xml"


@pytest.fixture(scope="session")
def conjointe_pdf() -> Path:
    return TESTDATA / "dt_dict_conjointe.pdf"


@pytest.fixture(scope="session")
def conjointe_jpg() -> Path:
    return TESTDATA / "dt_dict_conjointe.jpg"


@pytest.fixture(scope="session")
def dt_xml() -> Path:
    return TESTDATA / "dt_seule.xml"


@pytest.fixture(scope="session")
def dt_pdf() -> Path:
    return TESTDATA / "dt_seule.pdf"


@pytest.fixture(scope="session")
def xml_declarations(conjointe_xml):
    from parsers.xml_parser import XMLParser

    return XMLParser(conjointe_xml).read_content()


@pytest.fixture(scope="session")
def acroform_declarations(conjointe_pdf):
    from parsers.acroform_pdf_parser import AcroformPDFParser

    return AcroformPDFParser(conjointe_pdf).read_content()


@pytest.fixture(scope="session")
def image_parser(conjointe_jpg):
    pytest.importorskip("paddleocr")
    pytest.importorskip("cv2")
    from parsers.image_parser import ImageParser

    return ImageParser(conjointe_jpg)


@pytest.fixture(scope="session")
def image_declarations(image_parser):
    return image_parser.read_content()
