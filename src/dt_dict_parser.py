from enum import Enum
from functools import cached_property
from pathlib import Path
from xml.etree import ElementTree as ET

from pypdf import PdfReader

from parsers.acroform_pdf_parser import AcroformPDFParser
from parsers.flattened_pdf_parser import FlattenedPDFParser
from parsers.image_parser import ImageParser
from parsers.xml_parser import XMLParser

# ██████╗  ██████╗  ██████╗██╗   ██╗███╗   ███╗███████╗███╗   ██╗████████╗    ██╗███╗   ██╗███████╗ ██████╗██████╗ ███████╗ ██████╗████████╗ ██████╗ ██████╗
# ██╔══██╗██╔═══██╗██╔════╝██║   ██║████╗ ████║██╔════╝████╗  ██║╚══██╔══╝    ██║████╗  ██║██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
# ██║  ██║██║   ██║██║     ██║   ██║██╔████╔██║█████╗  ██╔██╗ ██║   ██║       ██║██╔██╗ ██║███████╗██║     ██████╔╝█████╗  ██║        ██║   ██║   ██║██████╔╝
# ██║  ██║██║   ██║██║     ██║   ██║██║╚██╔╝██║██╔══╝  ██║╚██╗██║   ██║       ██║██║╚██╗██║╚════██║██║     ██╔═══╝ ██╔══╝  ██║        ██║   ██║   ██║██╔══██╗
# ██████╔╝╚██████╔╝╚██████╗╚██████╔╝██║ ╚═╝ ██║███████╗██║ ╚████║   ██║       ██║██║ ╚████║███████║╚██████╗██║     ███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║
# ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝   ╚═╝       ╚═╝╚═╝  ╚═══╝╚══════╝ ╚═════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝


class FileType(Enum):
    PDF = "pdf"
    IMAGE = "image"
    XML = "xml"
    ZIP = "zip"
    UNKNOWN = "unknown"


class ContentType(Enum):
    ACROFORM_PDF = "acroform_pdf"
    FLATTENED_PDF = "flattened_pdf"
    SCANNED_PDF = "scanned_pdf"
    IMAGE = "image"
    XML = "xml"
    UNKNOWN = "unknown"


IMAGE_SIGNATURES: dict[str, bytes] = {
    "png": b"\x89PNG\r\n\x1a\n",
    "gif87": b"GIF87a",
    "gif89": b"GIF89a",
    "bmp": b"BM",
    "tiff_le": b"II*\x00",
    "tiff_be": b"MM\x00*",
    "ico": b"\x00\x00\x01\x00",
    "jpeg2000": b"\x00\x00\x00\x0cjP  \r\n\x87\n",
    "jpeg": b"\xff\xd8\xff",
}


class DocumentInspector:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    @cached_property
    def is_pdf(self) -> bool:
        try:
            with open(self.file_path, "rb") as f:
                return f.read(5) == b"%PDF-"
        except OSError:
            return False

    @cached_property
    def is_image(self) -> bool:
        try:
            with open(self.file_path, "rb") as f:
                header = f.read(12)
        except OSError:
            return False

        return header.startswith(tuple(IMAGE_SIGNATURES.values())) or (
            header.startswith(b"RIFF") and header[8:12] == b"WEBP"
        )

    @cached_property
    def is_xml(self) -> bool:
        try:
            next(ET.iterparse(self.file_path, events=("start",)))
            return True
        except (OSError, ET.ParseError, StopIteration):
            return False

    @cached_property
    def form_fields(self) -> dict[str, str]:
        """
        Extract AcroForm fields if present.
        """

        try:
            fields = self.pdf_reader.get_form_text_fields()
            return fields or {}

        except Exception:
            return {}

    @cached_property
    def pdf_reader(self) -> PdfReader:
        if not self.is_pdf:
            raise ValueError(f"{self.file_path} is not a PDF file.")

        return PdfReader(self.file_path)

    @cached_property
    def has_extractable_text(self) -> bool:

        for page in self.pdf_reader.pages:
            text = (page.extract_text() or "").strip()

            if len(text) >= 20:
                return True

        return False

    @property
    def has_form_fields(self) -> bool:
        return len(self.form_fields) > 0

    @property
    def file_type(self) -> FileType:
        if self.is_pdf:
            return FileType.PDF

        if self.is_image:
            return FileType.IMAGE

        if self.is_xml:
            return FileType.XML

        return FileType.UNKNOWN

    @property
    def content_type(self) -> ContentType:

        if self.file_type == FileType.XML:
            return ContentType.XML

        if self.file_type == FileType.IMAGE:
            return ContentType.IMAGE

        if self.file_type != FileType.PDF:
            return ContentType.UNKNOWN

        if self.has_form_fields:
            return ContentType.ACROFORM_PDF

        if self.has_extractable_text:
            return ContentType.FLATTENED_PDF

        return ContentType.SCANNED_PDF

    def _page_has_form_fields(self, page) -> bool:
        """True if the page holds at least one text widget of the AcroForm."""
        for annot in page.get("/Annots") or []:
            widget = annot.get_object()
            if widget.get("/Subtype") != "/Widget":
                continue
            name = widget.get("/T")
            node = widget
            while name is None and "/Parent" in node:
                node = node["/Parent"].get_object()
                name = node.get("/T")
            if name is not None and str(name) in self.form_fields:
                return True
        return False

    @staticmethod
    def _page_has_extractable_text(page) -> bool:
        return len((page.extract_text() or "").strip()) >= 20

    @property
    def document_info(self) -> list[dict]:
        """
        One dictionary per page. XML and image files are a single page.
        """

        file_type = self.file_type

        if file_type != FileType.PDF:
            return [
                {
                    "page_number": 1,
                    "file_type": file_type.value,
                    "content_type": self.content_type.value,
                    "has_form_fields": False,
                }
            ]

        pages_info = []
        for page_number, page in enumerate(self.pdf_reader.pages, start=1):
            has_form_fields = self._page_has_form_fields(page)

            if has_form_fields:
                content_type = ContentType.ACROFORM_PDF
            elif self._page_has_extractable_text(page):
                content_type = ContentType.FLATTENED_PDF
            else:
                content_type = ContentType.SCANNED_PDF

            pages_info.append(
                {
                    "page_number": page_number,
                    "file_type": file_type.value,
                    "content_type": content_type.value,
                    "has_form_fields": has_form_fields,
                }
            )
        return pages_info

    def __repr__(self) -> str:
        return (
            f"DocumentInspector({self.file_path}, document_info={self.document_info})"
        )


# ██████╗ ███████╗██████╗ ██╗   ██╗ ██████╗
# ██╔══██╗██╔════╝██╔══██╗██║   ██║██╔════╝
# ██║  ██║█████╗  ██████╔╝██║   ██║██║  ███╗
# ██║  ██║██╔══╝  ██╔══██╗██║   ██║██║   ██║
# ██████╔╝███████╗██████╔╝╚██████╔╝╚██████╔╝
# ╚═════╝ ╚══════╝╚═════╝  ╚═════╝  ╚═════╝

"""
TODO
    - gestion des checkbo avec valeur true et false que l'on met dans une seule variable in-fine
    - la méthode pour les PDF flat est trop rigide (si la taille du cerfa n'est pas la même, les résultats seront erroné)
"""

if __name__ == "__main__":
    # input_file_path = Path("/home/bn/Documents/maquette/Travaux-Prevelles-09-2026.pdf")
    # input_file_path = Path(
    #     "/home/bn/Documents/maquette/2026100801380T_DICT-DT Conjointe_1.pdf"
    # )
    input_file_path = Path(
        "dev_tools/2026100801380T_DDC/2026100801380T_DDC_description/2026100801380T_DDC_description.xml"
    )

    # input_file_path = Path(
    #     "/home/bn/Documents/maquette/2026100801380T_DICT-DT Conjointe_7_page-0001.jpg"
    # )  # JPEG image input file

    # input_file_path = Path(
    #     "/home/bn/Documents/Perso/dtdict_parser/src/dev_tools/2026100800884T_DDC/2026100800884T_DDC_emprise.pdf"
    # )

    document_inspector = DocumentInspector(input_file_path)
    print(document_inspector.document_info)

    breakpoint()

    if document_inspector.file_type == FileType.PDF:
        if document_inspector.content_type == ContentType.FLATTENED_PDF:
            flattened_pdf = FlattenedPDFParser(input_file_path)
            content = flattened_pdf.read_content()
        elif (
            document_inspector.content_type == ContentType.ACROFORM_PDF
            and document_inspector.has_form_fields
        ):
            pdf_acroform_parser = AcroformPDFParser(input_file_path)
            content = pdf_acroform_parser.read_content()
        elif document_inspector.content_type == ContentType.SCANNED_PDF:
            raise NotImplementedError("Scanned PDF parsing is not implemented yet.")
    elif document_inspector.file_type == FileType.XML:
        xml_parser = XMLParser(input_file_path)
        content = xml_parser.read_content()
    elif document_inspector.file_type == FileType.IMAGE:
        image_parser = ImageParser(input_file_path)
        content = image_parser.read_content()
    print(content)

    breakpoint()
