import json
import logging
import re
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from paddleocr import PaddleOCR

from models.models import DICT, DT
from parsers.base import ParserFactory
from parsers.flattened_pdf_parser import FlattenedPDFParser

logger = logging.getLogger(__name__)


class ImageParser(FlattenedPDFParser):
    """Read a DT-DICT cerfa 14434*03 given as an image of an A4 page."""

    # Size (in PDF points) of the page the templates were drawn on.
    TEMPLATE_PAGE_SIZE = (595.0, 842.0)
    # Dark pixel ratio (inside a checkbox) above which it is considered checked
    # (measured: empty boxes <= 0.15, checked boxes >= 0.40).
    CHECKBOX_FILL_THRESHOLD = 0.3
    CHECKBOX_INNER_MARGIN = 0.2
    # White border added around crops: the OCR detector struggles on tight crops.
    CROP_PADDING_PX = 20
    # Below this confidence, the OCR is reading the form's boxes / underscores
    # of an empty field rather than text.
    MIN_OCR_SCORE = 0.7
    # Fields written character by character in boxes: the OCR reads the box
    # separators as punctuation, which is dropped.
    COMB_FIELDS = {
        "noConsultationDuTeleservice",
        "noConsultationDuTeleserviceSeize",
        "codePostal",
        "CP",
        "codeINSEE",
        "noSiret",
        "tel",
        "fax",
    }

    def __init__(self, file_path: Path):
        ParserFactory.__init__(self, file_path)

        with open("models/template_14434_03.json", encoding="utf-8") as f:
            self.template_cerfa = json.load(f)

        with open("models/template_cerfa_detection.json", encoding="utf-8") as f:
            self.template_cerfa_detection = json.load(f)

        image = cv2.imread(str(file_path))
        if image is None:
            raise ValueError(f"Unable to load the image {file_path}")
        self.image = image
        self._ocr: PaddleOCR | None = None

    @property
    def ocr(self) -> PaddleOCR:
        if self._ocr is None:
            self._ocr = PaddleOCR(
                lang="fr",
                use_textline_orientation=True,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                # oneDNN crashes with Paddle 3.3 (ConvertPirAttribute2RuntimeAttribute)
                enable_mkldnn=False,
            )
        return self._ocr

    def read_content(self) -> list[DT | DICT]:
        """
        Returns:
            list[DT | DICT]: the declarations found in the cerfa (both when
            the cerfa is filled as a joint DT-DICT).

        TODO : le polygone GML (page 2 du PDF) n'est pas lu depuis une image.
        TODO : Adapter le template pour les images qui ne sont pas totalement droite (et parfaitement scannée)
        """

        self._check_page_ratio()

        if not self._is_cerfa_image():
            logger.warning("No Cerfa 14434*03 form was detected in the image")
            return []

        return self._build_declarations(self._read_image_fields())

    def _check_page_ratio(self) -> None:
        height, width = self.image.shape[:2]
        template_width, template_height = self.TEMPLATE_PAGE_SIZE
        if abs(width / height - template_width / template_height) > 0.01:
            raise NotImplementedError("Image is not an A4 page / resize needed ?")

    def _is_cerfa_image(self) -> bool:
        """Check that the cerfa number is found where the template expects it."""

        field = self.template_cerfa_detection["fields"]["GLOBAL.cerfa_numero"]
        text = self._read_texts([field["bbox"]])[0]
        return "14434" in text

    def _read_image_fields(self) -> dict[str, dict[str, Any]]:
        """Return the values of every template field, grouped by section."""

        results: dict[str, dict[str, Any]] = {"DT": {}, "DICT": {}, "global": {}}

        fields = self.template_cerfa["fields"]
        ocr_fields = [name for name, f in fields.items() if f["type"] != "checkbox"]
        texts = dict(
            zip(
                ocr_fields,
                self._read_texts([fields[name]["bbox"] for name in ocr_fields]),
            )
        )
        for name, field in fields.items():
            if field["type"] == "checkbox":
                texts[name] = "X" if self._is_checked(field["bbox"]) else ""

        return self._fill_results(results, texts)

    def _clean_text(self, name: str, text: str) -> str:
        if name.rsplit(".", 1)[-1] in self.COMB_FIELDS:
            return re.sub(r"[^0-9A-Za-z+]", "", text)
        return text

    def _to_pixels(self, bbox: list[float]) -> tuple[int, int, int, int]:
        height, width = self.image.shape[:2]
        template_width, template_height = self.TEMPLATE_PAGE_SIZE
        x0, top, x1, bottom = bbox
        return (
            round(x0 * width / template_width),
            round(top * height / template_height),
            round(x1 * width / template_width),
            round(bottom * height / template_height),
        )

    def _is_checked(self, bbox: list[float]) -> bool:
        x0, top, x1, bottom = self._to_pixels(bbox)
        margin_x = round((x1 - x0) * self.CHECKBOX_INNER_MARGIN)
        margin_y = round((bottom - top) * self.CHECKBOX_INNER_MARGIN)
        inner = self.image[
            top + margin_y : bottom - margin_y, x0 + margin_x : x1 - margin_x
        ]
        if inner.size == 0:
            return False

        gray = cv2.cvtColor(inner, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray < 128)) > self.CHECKBOX_FILL_THRESHOLD

    def _read_texts(self, bboxes: list[list[float]]) -> list[str]:
        """OCR each bbox (in template points) and return its text, in order."""

        pad = self.CROP_PADDING_PX
        crops = []
        for bbox in bboxes:
            x0, top, x1, bottom = self._to_pixels(bbox)
            crop = self.image[max(top, 0) : bottom, max(x0, 0) : x1]
            crops.append(
                cv2.copyMakeBorder(
                    crop, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(255, 255, 255)
                )
            )

        return [self._join_texts(result) for result in self.ocr.predict(crops)]

    @classmethod
    def _join_texts(cls, result: dict) -> str:
        """Join the confidently recognized lines of a crop in reading order."""

        lines = sorted(
            (
                (text, box)
                for text, box, score in zip(
                    result["rec_texts"], result["rec_boxes"], result["rec_scores"]
                )
                if float(score) >= cls.MIN_OCR_SCORE
            ),
            key=lambda item: (round(float(item[1][1]) / 15), float(item[1][0])),
        )
        return " ".join(text for text, _ in lines).strip()
