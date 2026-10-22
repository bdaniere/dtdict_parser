import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class NatureProjet(Enum):
    CNS = "CNS"
    CSP = "CSP"
    CUR = "CUR"
    DEC = "DEC"
    DEM = "DEM"
    DRA = "DRA"
    EBL = "EBL"
    ELG = "ELG"
    ERE = "ERE"
    ESC = "ESC"
    FAC = "FAC"
    FOH = "FOH"
    FOV = "FOV"
    OTR = "OTR"
    OUV = "OUV"
    RBL = "RBL"
    SFP = "SFP"
    SOU = "SOU"
    TER = "TER"
    CHA = "CHA"


class TechniqueTravaux(Enum):
    BTO = "BTO"
    BRO = "BRO"
    DBR = "DBR"
    TRA = "TRA"
    ELE = "ELE"
    TUB = "TUB"
    VIB = "VIB"
    STA = "STA"
    EXP = "EXP"
    TED = "TED"


class NatureDeclaration(Enum):
    INITIAL = "INITIAL"
    INVEST = "INVEST"
    MR_3 = "MR3"
    INTERUP = "INTERUP"
    MR_6 = "MR6"


class TypeEntite(Enum):
    PERSONNE_PHYSIQUE = "PERSONNE_PHYSIQUE"
    PERSONNE_MORALE = "PERSONNE_MORALE"


class DeclarationType(Enum):
    DT = "DT"
    DICT = "DICT"
    CONJOINTE = "CONJOINTE"


@dataclass
class Acteur:
    denomination: str | None = None
    complementService: str | None = None
    numero: str | None = None
    voie: str | None = None
    lieuDitBP: str | None = None
    codePostal: str | None = None
    commune: str | None = None
    pays: str | None = None
    noSiret: str | None = None
    personneAcontacter: str | None = None  # DT
    nomDeLaPersonneAContacter: str | None = None  # DICT
    tel: str | None = None
    fax: str | None = None
    courriel: str | None = None


@dataclass
class EmplacementDeLaCommuneConcernee:
    nomDeLaCommune: str | None = None
    codePostal: str | None = None
    codeINSEE: str | None = None


@dataclass
class Emplacement:
    adresse: str | None = None  # DT uniquement
    CP: str | None = None
    communePrincipale: str | None = None
    codeINSEE: str | None = None
    nombreDeCommunes: int | None = None
    listeDesEmplacementsDesCommunesConcernees: list[EmplacementDeLaCommuneConcernee] = (
        field(default_factory=list)
    )


@dataclass
class Emprise:
    geometrie: str | None = None  # WKT reprojeté
    surface: float | None = None
    referenceDelaCarte: str | None = None


@dataclass
class ModeReceptionElectronique:
    tailleDesPlans: str | None = None
    couleurDesPlans: bool | None = None
    souhaitDePlansVectoriels: bool | None = None
    formatDesPlansVectoriels: str | None = None


@dataclass
class ModeReceptionCourrier:
    """Balise vide : sa présence indique une réception par courrier."""


@dataclass
class SouhaitsPourLeRecepisse:
    souhaiteRecevoirLeRecepisse: bool | None = None  # DT uniquement
    modeReceptionElectronique: ModeReceptionElectronique | None = None
    modeReceptionCourrier: ModeReceptionCourrier | None = None


@dataclass
class InvestigationsComplementaires:
    realisationDInvestigationsComplementaires: bool | None = None
    motifDeRealisationOuNonDInvestigation: str | None = None
    dateDesInvestigationsComplementaires: date | None = None
    InvestigationsSusceptibleDeNecessiterUneDICT: bool | None = None
    envoiDesResultatsAuxExploitantsDOuvragesEtAuxEntreprises: bool | None = None


@dataclass
class Signature:
    nomDuSignataire: str | None = None
    nombrePagesJointes: int | None = None


@dataclass
class ProjetEtSonCalendrier:
    natureDesTravaux: list[NatureProjet] = field(default_factory=list)
    decrivezLeProjet: str | None = None
    emploiDeTechniquesSansTranchees: bool | None = None
    distanceMinimaleEntreLesTravauxEtLaLigneElectrique: float | None = None
    souhaitLesPlansDesReseauxElectriqueAeriens: bool | None = None
    datePrevuePourLeCommencementDesTravaux: date | None = None
    dureeDuChantierEnJours: int | None = None


@dataclass
class TravauxEtLeurCalendrier:
    natureDesTravaux: list[NatureProjet] = field(default_factory=list)
    decrivezLesTravaux: str | None = None
    techniquesUtilisees: list[TechniqueTravaux] = field(default_factory=list)
    autreTechnique: str | None = None
    profondeurMaxDExcavation: float | None = None
    modificationProfilTerrain: bool | None = None
    communicationResultatsInvestigations: bool | None = None
    distanceMinimaleEntreLesTravauxEtLaLigneElectrique: float | None = None
    souhaitLesPlansDesReseauxElectriqueAeriens: bool | None = None
    datePrevuePourLeCommencementDesTravaux: date | None = None
    dureeDuChantierEnJours: int | None = None


@dataclass
class Declaration:
    """
    Classe racine commune à tous les documents DT-DICT.
    """

    declaration_type: DeclarationType  # hors XML
    dateDeLaDeclaration: date
    # DT seule : noConsultationDuTeleserviceSeize ; DICT ou DT-DICT conjointe :
    # noConsultationDuTeleservice
    mainNoConsultationDuTeleservice: str | None = None
    emprise: Emprise | None = None
    souhaitsPourLeRecepisse: SouhaitsPourLeRecepisse | None = None

    def __post_init__(self) -> None:
        _validate_no_consultation_number(
            self.mainNoConsultationDuTeleservice, "mainNoConsultationDuTeleservice"
        )


@dataclass
class DT(Declaration):
    """
    Déclaration de Travaux.
    """

    noConsultationDuTeleserviceSeize: str | None = None  # DT seule (hors conjointe)
    noAffaireDuResponsableDuProjet: str | None = None
    typeEntite: TypeEntite | None = None
    declarationConjointeDTDICT: bool | None = None
    responsableDuProjet: Acteur | None = None
    representantDuResponsableDeProjet: Acteur | None = None
    emplacementDuProjet: Emplacement | None = None
    projetEtSonCalendrier: ProjetEtSonCalendrier | None = None
    investigationsComplementaires: InvestigationsComplementaires | None = None
    signatureDuResponsableDuProjetOuDeSonRepresentant: Signature | None = None

    def __post_init__(self) -> None:
        numero = self.noConsultationDuTeleserviceSeize
        if numero is not None:
            _validate_no_consultation_number(numero, "noConsultationDuTeleserviceSeize")
            if (
                self.declaration_type == DeclarationType.DT
                and self.mainNoConsultationDuTeleservice is None
            ):
                self.mainNoConsultationDuTeleservice = numero
        super().__post_init__()


@dataclass
class DICT(Declaration):
    """
    Déclaration d'Intention de Commencement de Travaux.
    """

    noConsultationDuTeleservice: str | None = None
    noAffaireDeLexecutantDesTravaux: str | None = None
    natureDeLaDeclaration: NatureDeclaration | None = None
    executantDesTravaux: Acteur | None = None
    emplacementDesTravaux: Emplacement | None = None
    travauxEtLeurCalendrier: TravauxEtLeurCalendrier | None = None
    signatureDeLExecutantDesTravauxOuDeSonRepresentant: Signature | None = None

    def __post_init__(self) -> None:
        if self.noConsultationDuTeleservice is not None:
            _validate_no_consultation_number(
                self.noConsultationDuTeleservice, "noConsultationDuTeleservice"
            )
            if self.mainNoConsultationDuTeleservice is None:
                self.mainNoConsultationDuTeleservice = self.noConsultationDuTeleservice
        super().__post_init__()


def _validate_no_consultation_number(numero: str, field_name: str) -> None:
    if not isinstance(numero, str) or not re.fullmatch(
        r"[0-9]{13}[A-Za-z][A-Za-z0-9]{0,2}", numero
    ):
        raise ValueError(
            f"{field_name} must contain an AAAAMMDD date, five digits, "
            "one letter, and zero to two optional alphanumeric characters"
        )

    try:
        date.fromisoformat(f"{numero[:4]}-{numero[4:6]}-{numero[6:8]}")
    except ValueError as exc:
        raise ValueError(f"{field_name} must start with a valid AAAAMMDD date") from exc
