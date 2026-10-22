"""Page objects produced by DocumentReader and consumed by the parsers."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import numpy as np
from pdfplumber.page import Page as PlumberPage


@dataclass(eq=False)
class XMLPage:
    """A whole XML file (a single page), with its namespaces removed."""

    root: ET.Element


@dataclass(eq=False)
class PDFPage:
    """One page of a PDF: its drawn content and the AcroForm fields it holds."""

    number: int
    content: PlumberPage
    form_fields: dict[str, str] = field(default_factory=dict)


@dataclass(eq=False)
class ImagePage:
    """An image file (a single page) loaded as a BGR array."""

    image: np.ndarray
