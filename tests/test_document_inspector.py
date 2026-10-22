from pathlib import Path

import pytest

from dt_dict_parser import (
    IMAGE_SIGNATURES,
    ContentType,
    DocumentInspector,
    DocumentReader,
    FileType,
    parse_document,
)

# WebP is the only format identified beyond the first bytes (RIFF....WEBP).
SIGNATURES = {**IMAGE_SIGNATURES, "webp": b"RIFF\x00\x00\x00\x00WEBP"}


@pytest.mark.parametrize("signature", SIGNATURES.values(), ids=SIGNATURES.keys())
def test_detects_common_image_signatures(tmp_path, signature):
    path = tmp_path / "file.bin"
    path.write_bytes(signature)

    inspector = DocumentInspector(path)

    assert inspector.file_type == FileType.IMAGE
    assert inspector.content_type == ContentType.IMAGE


def test_image_extension_does_not_identify_non_image_content(tmp_path):
    path = tmp_path / "fake.png"
    path.write_bytes(b"not an image")

    inspector = DocumentInspector(path)

    assert inspector.file_type == FileType.UNKNOWN
    assert inspector.content_type == ContentType.UNKNOWN


def test_real_jpeg_is_an_image(conjointe_jpg):
    assert DocumentInspector(conjointe_jpg).document_info == [
        {
            "page_number": 1,
            "file_type": "image",
            "content_type": "image",
            "has_form_fields": False,
        }
    ]


def test_acroform_pdf(conjointe_pdf):
    inspector = DocumentInspector(conjointe_pdf)

    assert inspector.file_type == FileType.PDF
    assert inspector.content_type == ContentType.ACROFORM_PDF
    assert inspector.has_form_fields
    pages = inspector.document_info
    assert len(pages) == len(inspector.pdf_reader.pages)
    assert [p["page_number"] for p in pages] == list(range(1, len(pages) + 1))
    assert all(p["file_type"] == "pdf" for p in pages)
    assert any(p["content_type"] == "acroform_pdf" and p["has_form_fields"] for p in pages)


def test_xml(conjointe_xml):
    inspector = DocumentInspector(conjointe_xml)

    assert inspector.file_type == FileType.XML
    assert inspector.content_type == ContentType.XML
    assert not inspector.has_form_fields
    assert len(inspector.document_info) == 1
    assert inspector.document_info[0]["content_type"] == "xml"


def test_unknown_content(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("just some text, not XML")

    inspector = DocumentInspector(path)

    assert inspector.file_type == FileType.UNKNOWN
    assert inspector.content_type == ContentType.UNKNOWN


def test_missing_file_is_unknown(tmp_path):
    inspector = DocumentInspector(Path(tmp_path / "does_not_exist.pdf"))

    assert inspector.file_type == FileType.UNKNOWN
    assert inspector.content_type == ContentType.UNKNOWN


def test_pdf_reader_refuses_non_pdf(conjointe_xml):
    with pytest.raises(ValueError):
        DocumentInspector(conjointe_xml).pdf_reader


def test_reader_gives_one_page_per_pdf_page(conjointe_pdf):
    inspector = DocumentInspector(conjointe_pdf)

    with DocumentReader(inspector) as reader:
        assert len(reader.pages) == len(inspector.document_info)
        assert reader.pages[0].number == 1
        assert reader.pages[0].form_fields == {
            name: str(field["/V"]) for name, field in inspector.pdf_reader.get_fields().items()
            if field.get("/V") is not None
        }


def test_reader_gives_a_single_page_for_xml_and_image(conjointe_xml, conjointe_jpg):
    for path in (conjointe_xml, conjointe_jpg):
        with DocumentReader(DocumentInspector(path)) as reader:
            assert len(reader.pages) == 1


def test_parse_document_reads_every_file_type(conjointe_xml, conjointe_pdf):
    xml_declarations = parse_document(conjointe_xml)
    pdf_declarations = parse_document(conjointe_pdf)

    assert len(xml_declarations) == len(pdf_declarations) == 2


def test_acroform_page_is_detected_as_cerfa(conjointe_pdf, first_page):
    from parsers.acroform_pdf_parser import AcroformPDFParser

    with first_page(conjointe_pdf) as page:
        assert AcroformPDFParser(page).is_cerfa()
