from pathlib import Path

import pytest

from dt_dict_parser import IMAGE_SIGNATURES, ContentType, DocumentInspector, FileType

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
    assert DocumentInspector(conjointe_jpg).document_info == {
        "file_type": "image",
        "content_type": "image",
        "has_form_fields": False,
    }


def test_acroform_pdf(conjointe_pdf):
    inspector = DocumentInspector(conjointe_pdf)

    assert inspector.file_type == FileType.PDF
    assert inspector.content_type == ContentType.ACROFORM_PDF
    assert inspector.has_form_fields
    assert inspector.document_info["page_count"] == 1


def test_xml(conjointe_xml):
    inspector = DocumentInspector(conjointe_xml)

    assert inspector.file_type == FileType.XML
    assert inspector.content_type == ContentType.XML
    assert not inspector.has_form_fields


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
