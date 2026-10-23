"""Shared fixtures: sample documents and parsed results (OCR is run once per session)."""

import os
from contextlib import contextmanager
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
def first_page():
    """Context manager giving the first page of a file, as read by DocumentReader."""
    from dt_dict_parser import DocumentInspector, DocumentReader

    @contextmanager
    def _first_page(path: Path):
        with DocumentReader(DocumentInspector(path)) as reader:
            yield reader.pages[0]

    return _first_page


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
def xml_declarations(conjointe_xml, first_page):
    from parsers.xml_parser import XMLParser

    with first_page(conjointe_xml) as page:
        return XMLParser(page).read_content()


@pytest.fixture(scope="session")
def acroform_declarations(conjointe_pdf, first_page):
    from parsers.acroform_pdf_parser import AcroformPDFParser

    with first_page(conjointe_pdf) as page:
        return AcroformPDFParser(page).read_content()


@pytest.fixture(scope="session")
def image_parser(conjointe_jpg, first_page):
    pytest.importorskip("paddleocr")
    pytest.importorskip("cv2")
    from parsers.image_parser import ImageParser

    with first_page(conjointe_jpg) as page:
        return ImageParser(page)


@pytest.fixture(scope="session")
def image_declarations(image_parser):
    return image_parser.read_content()
