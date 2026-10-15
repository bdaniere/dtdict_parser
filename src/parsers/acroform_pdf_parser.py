import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path
from typing import Any

from PyPDF2 import PdfReader

from models.models import (
    DICT,
    DT,
    EmplacementDeLaCommuneConcernee,
    ModeReceptionCourrier,
)
from parsers.base import ParserFactory
from parsers.flattened_pdf_parser import FlattenedPDFParser
from parsers.xml_parser import XMLParser


class AcroformPDFParser(FlattenedPDFParser):
    """Read a DT-DICT PDF whose AcroForm fields are filled."""

    def __init__(self, pdf_path: Path):
        ParserFactory.__init__(self, pdf_path)
        with open("./models/acroform_template.json", encoding="utf-8") as f:
            self.text_fields = json.load(f)
        self.reader = PdfReader(pdf_path)

    def read_content(self) -> list[DT | DICT]:
        """
        Returns:
            list[DT | DICT]: the declarations found in the form (both when
            the form is filled as a joint DT-DICT).
        """

        raw = {
            name: str(field["/V"]).strip()
            for name, field in (self.reader.get_fields() or {}).items()
            if field.get("/V") is not None
        }

        results = {
            "DT": self._extract_dt(raw),
            "DICT": self._extract_dict(raw),
            "global": {},
        }

        for name in ("empriseDT", "empriseDICT"):
            if raw.get(name):
                gml = ET.fromstring(raw[name].replace("gml:", ""))
                results["global"]["geom"] = XMLParser._read_geometry(gml)
                break

        return self._build_declarations(results)

    def _extract_dt(self, raw: dict[str, str]) -> dict[str, Any]:
        values = self._text_values(raw, "DT")
        calendar = "projetEtSonCalendrier."
        investigations = "investigationsComplementaires."

        values["dateDeLaDeclaration"] = self._datetime(
            raw, "Jour_DT", "Mois_DT", "Annee_DT"
        )
        values["typeEntite"] = {
            "/morale": "PERSONNE_MORALE",
            "/physique": "PERSONNE_PHYSIQUE",
        }.get(raw.get("ResponsableProjetCase", ""))
        values["declarationConjointeDTDICT"] = (
            raw.get("Declaration_conjointe") == "/Oui"
        )
        values["responsableDuProjet.noSiret"] = self._join(raw, "Siret{}_DT", 4)

        values["souhaitsPourLeRecepisse.souhaiteRecevoirLeRecepisse"] = (
            raw.get("Souhait_recepisse_DTDICTconjoint") == "/Oui"
        )
        values.update(self._recepisse(raw, "DT"))
        values.update(self._communes(raw.get("communesDT"), "emplacementDuProjet"))

        values[calendar + "natureDesTravaux"] = self._join(
            raw, "Nature_Travaux{}_DT", 5, sep=" ", codes=True
        )
        values[calendar + "decrivezLeProjet"] = self._join(
            raw, "Projet{}_DT", 3, first="Projet_DT"
        )
        values[calendar + "emploiDeTechniquesSansTranchees"] = (
            raw.get("TST") == "/TST_oui"
        )
        values[calendar + "distanceMinimaleEntreLesTravauxEtLaLigneElectrique"] = (
            self._distance(raw, "Distance_m_DT", "Distance_cm_DT")
        )
        values[calendar + "souhaitLesPlansDesReseauxElectriqueAeriens"] = (
            raw.get("Prox_reseaux_elec_CaseDT") == "/Oui"
        )
        values[calendar + "datePrevuePourLeCommencementDesTravaux"] = self._date(
            raw, "Jour_travaux_DT", "Mois_travaux_DT", "Annee_travaux_DT"
        )

        values[investigations + "realisationDInvestigationsComplementaires"] = (
            raw.get("Investigations") == "/IC_oui"
        )
        values[investigations + "dateDesInvestigationsComplementaires"] = self._date(
            raw, "Jour_IC", "Mois_IC", "Annee_IC"
        )
        values[investigations + "InvestigationsSusceptibleDeNecessiterUneDICT"] = (
            raw.get("IC_avec_DICT") == "/Oui"
        )
        values[
            investigations + "envoiDesResultatsAuxExploitantsDOuvragesEtAuxEntreprises"
        ] = raw.get("Envoi_resultats_IC") == "/Oui"
        return values

    def _extract_dict(self, raw: dict[str, str]) -> dict[str, Any]:
        values = self._text_values(raw, "DICT")
        calendar = "travauxEtLeurCalendrier."

        values["dateDeLaDeclaration"] = self._datetime(
            raw, "Jour_DICT", "Mois_DICT", "Annee_DICT"
        )
        nature = raw.get("Nature_DICT", "")
        values["natureDeLaDeclaration"] = {"3MR": "MR_3", "6MR": "MR_6"}.get(
            nature, nature
        )
        values["executantDesTravaux.noSiret"] = self._join(raw, "SiretDICT{}", 4)

        values.update(self._recepisse(raw, "DICT"))
        values.update(self._communes(raw.get("communesDICT"), "emplacementDesTravaux"))

        values[calendar + "natureDesTravaux"] = self._join(
            raw, "NatureTravaux{}_DICT", 5, sep=" ", codes=True
        )
        values[calendar + "decrivezLesTravaux"] = self._join(raw, "Travaux{}_DICT", 2)
        values[calendar + "techniquesUtilisees"] = self._join(
            raw, "Technique_DICT{}", 10, sep=" ", codes=True
        )
        if raw.get("AutreTechniqueCase_DICT") == "/Oui":
            values[calendar + "autreTechnique"] = (
                raw.get("Autre_technique_DICT") or None
            )
        values[calendar + "modificationProfilTerrain"] = (
            raw.get("Modif_profil_DICT") == "/Oui"
        )
        values[calendar + "communicationResultatsInvestigations"] = (
            raw.get("ResultatsInvestigations_DICT") == "/Res_IC_oui"
        )
        values[calendar + "distanceMinimaleEntreLesTravauxEtLaLigneElectrique"] = (
            self._distance(raw, "Distance_m_DICT", "Distance_cm_DICT")
        )
        values[calendar + "souhaitLesPlansDesReseauxElectriqueAeriens"] = (
            raw.get("PlansElecCase_DICT") == "/Oui"
        )
        values[calendar + "datePrevuePourLeCommencementDesTravaux"] = self._date(
            raw, "JourTravaux_DICT", "MoisTravaux_DICT", "AnneeTravaux_DICT"
        )
        return values

    def _text_values(self, raw: dict[str, str], section: str) -> dict[str, Any]:
        return {
            key: raw[name]
            for name, key in self.text_fields[section].items()
            if raw.get(name)
        }

    @staticmethod
    def _join(
        raw: dict[str, str],
        pattern: str,
        count: int,
        sep: str = "",
        codes: bool = False,
        first: str | None = None,
    ) -> str | None:
        """Concatenate numbered fields ('Siret1_DT', 'Siret2_DT', ...)."""
        names = [pattern.format(i) for i in range(1, count + 1)]
        if first:
            names[0] = first
        parts = [raw.get(n, "") for n in names]
        if codes:  # 'E B L*' -> 'EBL'
            parts = [re.sub(r"[\s*]", "", p) for p in parts]
        return sep.join(p for p in parts if p) or None

    @staticmethod
    def _date(raw: dict[str, str], day: str, month: str, year: str) -> date | None:
        try:
            return date(int(raw[year]), int(raw[month]), int(raw[day]))
        except (KeyError, ValueError):
            return None

    @classmethod
    def _datetime(cls, raw: dict[str, str], day: str, month: str, year: str):
        d = cls._date(raw, day, month, year)
        return datetime(d.year, d.month, d.day) if d else None

    @staticmethod
    def _distance(raw: dict[str, str], meters: str, centimeters: str) -> str | None:
        if not raw.get(meters):
            return None
        return f"{raw[meters]}.{raw.get(centimeters) or '0'}"

    @staticmethod
    def _recepisse(raw: dict[str, str], suffix: str) -> dict[str, Any]:
        prefix = "souhaitsPourLeRecepisse."
        mode = raw.get(f"Mode_recepisse_{suffix}")

        if mode == "Par courrier":
            return {prefix + "modeReceptionCourrier": ModeReceptionCourrier()}
        if mode != "Par voie électronique":
            return {}

        prefix += "modeReceptionElectronique."
        return {
            prefix + "tailleDesPlans": raw.get(f"Plans_taille_{suffix}") or None,
            prefix + "couleurDesPlans": raw.get(f"PlanCouleur_{suffix}") == "/Oui",
            prefix + "souhaitDePlansVectoriels": raw.get(f"PlansVectoriels_{suffix}")
            == "/Oui",
            prefix + "formatDesPlansVectoriels": raw.get(f"Plans_Formats_{suffix}")
            or None,
        }

    @staticmethod
    def _communes(text: str | None, section: str) -> dict[str, Any]:
        """Parse '38080 Commune (code INSEE 38352) (Commune principale)' lines."""
        communes = [
            EmplacementDeLaCommuneConcernee(
                nomDeLaCommune=name, codePostal=postal_code, codeINSEE=insee
            )
            for postal_code, name, insee in re.findall(
                r"(\d{5})\s+(.+?)\s+\(code INSEE (\w+)\)", text or ""
            )
        ]
        main_insee = re.search(r"code INSEE (\w+)\) \(Commune principale\)", text or "")
        return {
            f"{section}.listeDesEmplacementsDesCommunesConcernees": communes,
            f"{section}.codeINSEE": main_insee.group(1) if main_insee else None,
        }
