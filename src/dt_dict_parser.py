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


# TODO : avoir une approche page par page : es-ce nécéssaire ?
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

    @property
    def document_info(self) -> dict:
        info = {
            "file_type": self.file_type.value,
            "content_type": self.content_type.value,
            "has_form_fields": self.has_form_fields,
        }
        if self.file_type == FileType.PDF:
            info["page_count"] = len(self.pdf_reader.pages)
        return info

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
    # input_file_path = Path(
    #     "dev_tools/2026100801380T_DDC/2026100801380T_DDC_description/2026100801380T_DDC_description.xml"
    # )

    input_file_path = Path(
        "/home/bn/Documents/maquette/2026100801380T_DICT-DT Conjointe_7_page-0001.jpg"
    )  # JPEG image input file

    document_inspector = DocumentInspector(input_file_path)
    print(document_inspector.document_info)

    if document_inspector.document_info["file_type"] == "pdf":
        if document_inspector.document_info["content_type"] == "flattened_pdf":
            flattened_pdf = FlattenedPDFParser(input_file_path)
            content = flattened_pdf.read_content()
        elif (
            document_inspector.document_info["content_type"] == "acroform_pdf"
            and document_inspector.document_info["has_form_fields"] == True
        ):
            pdf_acroform_parser = AcroformPDFParser(input_file_path)
            content = pdf_acroform_parser.read_content()
        elif document_inspector.document_info["content_type"] == "scanned_pdf":
            raise NotImplementedError("Scanned PDF parsing is not implemented yet.")
    elif document_inspector.document_info["file_type"] == "xml":
        xml_parser = XMLParser(input_file_path)
        content = xml_parser.read_content()
    elif document_inspector.document_info["file_type"] == "image":
        image_parser = ImageParser(input_file_path)
        content = image_parser.read_content()
    print(content)

    breakpoint()
