from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import get_args, get_origin, get_type_hints

from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform as shapely_transform

from models.models import (
    DICT,
    DT,
    DeclarationType,
)
from models.pages import XMLPage
from parsers.base import ParserFactory
from parsers.flattened_pdf_parser import FlattenedPDFParser


class XMLParser(ParserFactory):
    TARGET_EPSG = FlattenedPDFParser.TARGET_EPSG

    def __init__(self, page: XMLPage):
        super().__init__(page)
        self.root = page.root

    def read_content(self) -> list[DT | DICT]:
        """
        Returns:
            list[DT | DICT]: the declarations found in the XML (both when
            the file is a joint DT-DICT).
        """

        declarations: list[DT | DICT] = []

        dt = self.root.find("DT")
        if dt is None:
            dt = self.root.find("dtDictConjointes/partieDT")
        if dt is not None:
            conjointe = dt.findtext("declarationConjointeDTDICT", "").strip() == "true"
            declaration_type = (
                DeclarationType.CONJOINTE if conjointe else DeclarationType.DT
            )
            overrides: dict[str, object] = {"declaration_type": declaration_type}
            source = (
                "noConsultationDuTeleservice"
                if conjointe
                else "noConsultationDuTeleserviceSeize"
            )
            overrides["mainNoConsultationDuTeleservice"] = (
                dt.findtext(source) or ""
            ).strip() or None
            declarations.append(self._build(DT, dt, **overrides))

        dict_part = self.root.find("dtDictConjointes/partieDICT")
        if dict_part is not None:
            declarations.append(
                self._build(DICT, dict_part, declaration_type=DeclarationType.DICT)
            )

        return declarations

    def _build(self, model: type, element: ET.Element, **overrides):
        """Instantiate a dataclass from the child elements named like its fields."""
        hints = get_type_hints(model)
        kwargs = {}
        for f in fields(model):
            if f.name in overrides:
                kwargs[f.name] = overrides[f.name]
                continue

            tp = FlattenedPDFParser._unwrap_optional(hints[f.name])
            child = element.find(f.name)

            if get_origin(tp) is list:
                (item_tp,) = get_args(tp)
                if isinstance(item_tp, type) and is_dataclass(item_tp):
                    items = (
                        [self._build(item_tp, c) for c in child]
                        if child is not None
                        else []
                    )
                else:
                    items = [
                        self._convert(c.text, item_tp) for c in element.findall(f.name)
                    ]
                kwargs[f.name] = [i for i in items if i is not None]
            elif child is None:
                kwargs[f.name] = None
            elif f.name == "geometrie":
                kwargs[f.name] = self._read_geometry(child)
            elif isinstance(tp, type) and is_dataclass(tp):
                kwargs[f.name] = self._build(tp, child)
            else:
                kwargs[f.name] = self._convert(child.text, tp)
        return model(**kwargs)

    @staticmethod
    def _convert(text: str | None, tp):
        """Coerce an element text to the dataclass field type."""
        text = (text or "").strip()
        if not text:
            return None
        try:
            if tp is bool:
                return text.lower() == "true"
            if tp is int:
                return int(text)
            if tp is float:
                return float(text)
            if tp is datetime:
                return datetime.fromisoformat(text)
            if tp is date:
                return date.fromisoformat(text[:10])  # drops the timezone suffix
            if isinstance(tp, type) and issubclass(tp, Enum):
                return tp(text.upper())
        except ValueError:
            return None
        return text

    @classmethod
    def _read_geometry(cls, element: ET.Element) -> str | None:
        """Read the first GML polygon and return its WKT in TARGET_EPSG."""
        polygon_el = element.find(".//Polygon")
        if polygon_el is None:
            return None

        def read_ring(ring: ET.Element) -> list[tuple[float, float]]:
            coordinates = ring.findtext("coordinates")
            if coordinates:
                points = []
                for pair in coordinates.split():
                    values = pair.split(",")
                    if len(values) < 2:
                        raise ValueError(f"Invalid coordinate pair: {pair}")
                    points.append((float(values[0]), float(values[1])))
                return points
            values = [float(v) for v in ring.findtext(".//posList", "").split()]
            return list(zip(values[::2], values[1::2]))

        exterior_ring = polygon_el.find("exterior/LinearRing")
        if exterior_ring is None:
            return None
        exterior = read_ring(exterior_ring)
        interiors = [read_ring(r) for r in polygon_el.findall("interior/LinearRing")]
        polygon = Polygon(exterior, interiors)

        transformer = Transformer.from_crs(
            element.get("srsName", "EPSG:4326"), cls.TARGET_EPSG, always_xy=True
        )
        return shapely_transform(transformer.transform, polygon).wkt
