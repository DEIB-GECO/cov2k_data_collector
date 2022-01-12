from typing import Optional, Collection, List, Tuple, Dict, Union
from pymongo.database import Database
from pymongo.collection import Collection as DBCCollection
import db_config.connection as connection

# COLLECTION NAMES
COLL_VARIANT = 'variant'
COLL_AA_CHANGE = 'aa_change'
COLL_NUC_CHANGE = 'nuc_change'
COLL_ORG = 'organization'
COLL_EFFECT = 'effect'
COLL_REFERENCE = 'evidence'
COLL_STRUCTURE = 'structure'
COLL_PROTEIN_REGION = 'protein_region'
COLL_AA_RESIDUE = "aa_residue"

# These are document schemas for a mongoDB database
# 1st level classes map to database collections
# 2nd level classes are schemas of objects nested inside the upper level document
# USE:
# use these objects as data containers
# then, you can get a mongoDB-ready representation by transforming these into dictionaries with vars(<object>).
# Careful though, vars(<obj>) works out-of-the-box for objects without nested objects,
# otherwise you need to override the attribute __dict__ (which is invoked by vars())


class Variant:
    def __init__(self, aliases=None, org_2_aa_changes=None, org_2_nuc_changes=None, effects=None):
        self.aliases: Optional[Collection[Variant.Name]] = None
        self.org_2_aa_changes: Optional[Collection[Variant.Characterization]] = None
        self.org_2_nuc_changes: Optional[Collection[Variant.Characterization]] = None
        self.effects: Optional[Collection[int]] = None

        self.set_aliases(aliases)
        self.set_org_2_aa_changes(org_2_aa_changes)
        self.set_org_2_nuc_changes(org_2_nuc_changes)
        self.set_effects(effects)

    class Name:
        def __init__(self, org=None, name=None, v_class=None):
            self.org: Optional[str] = org.upper() if org else None
            self.name: Optional[str] = name.upper() if name else None
            self.v_class: Optional[str] = v_class.upper() if v_class else None

    class Characterization:
        def __init__(self, org=None, changes=None):
            self.org: Optional[str] = org.upper() if org else None
            self.changes: Optional[Collection[str]] = changes

    def set_aliases(self, coll: Collection[Name]):
        self.aliases = coll if coll else []

    def set_org_2_nuc_changes(self, coll: Collection[Characterization]):
        if coll:
            coll = [x for x in coll if x.changes]   # removes empty characterizations
        self.org_2_nuc_changes = coll if coll else []

    def set_org_2_aa_changes(self, coll: Collection[Characterization]):
        if coll:
            coll = [x for x in coll if x.changes]   # removes empty characterizations
        self.org_2_aa_changes = coll if coll else []

    def set_effects(self, coll: Collection[int]):
        self.effects = coll if coll else []

    @property
    def __dict__(self):
        return {
            'aliases': [vars(x) for x in self.aliases],
            'org_2_aa_changes': [vars(x) for x in self.org_2_aa_changes],
            'org_2_nuc_changes': [vars(x) for x in self.org_2_nuc_changes],
            'effects': self.effects
        }

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_VARIANT]


class Organization:
    def __init__(self, name=None, reference_url=None, rule_description=None, threshold=None):
        self.name: Optional[str] = name
        self.reference_url: Optional[str] = reference_url
        self.rule_description: Optional[str] = rule_description
        self.threshold: Optional[str] = threshold

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_ORG]


class NUCChange:
    def __init__(self, change_id=None, ref=None, pos=None, alt=None, _type=None, length=None, is_opt=None):
        self.change_id: Optional[str] = change_id.upper()
        self.ref: Optional[str] = ref.upper()
        self.pos: Optional[int] = int(pos)
        self.alt: Optional[str] = alt.upper()
        self.type: Optional[str] = _type.upper()
        self.length: Optional[int] = int(length)
        self.is_optional: Optional[bool] = is_opt

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_NUC_CHANGE]


class AAChange:
    def __init__(self, change_id=None, protein=None, ref=None, pos=None, alt=None, _type=None, length=None, is_opt=None):
        self.change_id: Optional[str] = change_id.upper()
        self.protein: Optional[str] = protein.upper()
        self.ref: Optional[str] = ref.upper()
        self.pos: Optional[int] = int(pos)
        self.alt: Optional[str] = alt.upper()
        self.type: Optional[str] = _type.upper()
        self.length: Optional[int] = int(length)
        self.is_optional: Optional[bool] = is_opt

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_AA_CHANGE]


class Effect:
    def __init__(self, _type: str = None, lv: str = None, method: str = None, aa_changes: Collection[str] = None):
        self.type: Optional[str] = _type
        self.lv: Optional[str] = lv
        self.method: Optional[str] = method
        self.aa_changes: Optional[Collection[str]] = aa_changes if aa_changes else []
        self.uniform()

    def uniform(self):
        self.type = self.type.lower().replace('_', ' ') if self.type else None
        self.lv = self.lv.lower().replace('_', ' ') if self.lv else None
        self.method = self.method.lower().replace('_', ' ') if self.method else None

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_EFFECT]


class Reference:
    def __init__(self, effect_ids: Collection[str] = None, citation: str = None, _type: str = None, uri: str = None, publisher: str = None):
        self.effect_ids: Optional[Collection[str]] = effect_ids if effect_ids else []
        self.citation: Optional[str] = citation
        self.type: Optional[str] = _type
        self.uri: Optional[str] = uri
        self.publisher: Optional[str] = publisher

    def uniform(self):
        self.citation = self.citation.lower() if self.citation else None
        self.type = self.type.lower() if self.type else None
        self.uri = self.uri if self.uri else None
        self.publisher = self.publisher.lower() if self.publisher else None

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_REFERENCE]


class Structure:
    def __init__(self, annotation_id: str, start_on_ref: int = None, stop_on_ref: int = None,
                 protein_characterization=None):
        self.annotation_id: str = annotation_id.upper() if annotation_id else None
        self.start_on_ref: Optional[int] = int(start_on_ref) if start_on_ref is not None else None
        self.stop_on_ref: Optional[int] = int(stop_on_ref) if stop_on_ref is not None else None
        self.protein_characterization: Optional[List[Structure.ProteinCharacterization]] = None

        self.set_protein_characterization(protein_characterization)

    class ProteinCharacterization:
        def __init__(self, protein_name: str, aa_length: int = None, aa_sequence: str = None):
            self.protein_name = protein_name.upper() if protein_name else None
            self.aa_length: Optional[int] = int(aa_length) if aa_length is not None else None
            self.aa_sequence: Optional[str] = aa_sequence.upper() if aa_sequence else None

    def set_protein_characterization(self, coll: Collection[ProteinCharacterization]):
        if coll:
            coll = [x for x in coll if x.protein_name]   # removes empty characterizations
        self.protein_characterization = coll if coll else []

    @property
    def __dict__(self):
        return {
            'annotation_id': self.annotation_id,
            'start_on_ref': self.start_on_ref,
            'stop_on_ref': self.stop_on_ref,
            'protein_characterization': [vars(x) for x in self.protein_characterization]
        }

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_STRUCTURE]


class ProteinRegion:
    def __init__(self, protein_name: str, start_on_prot: int, stop_on_prot: int, description: str = None
                 , _type: str = None, category: str = None):
        self.protein_name: str = protein_name.upper() if protein_name else None
        self.start_on_prot: int = int(start_on_prot) if start_on_prot is not None else None
        self.stop_on_prot: int = int(stop_on_prot) if stop_on_prot is not None else None
        self.description: str = description.lower() if description else None
        self.type: str = _type.lower() if _type else None
        self.category: str = category.lower() if category else None

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_PROTEIN_REGION]


class AAResidue:
    def __init__(self, args):
        self.residue: str = args[0].upper()
        self.molecular_weight: int = int(args[1]) if args[1] is not None else None
        self.isoelectric_point: float = float(args[2]) if args[2] is not None else None
        self.hydrophobicity: float = float(args[3]) if args[3] is not None else None
        self.potential_side_chain_h_bonds: int = int(args[4]) if args[4] is not None else None
        self.polarity: str = args[5].lower() if args[5] else None
        self.r_group_structure: str = args[6].lower() if args[6] else None
        self.charge: Optional[str] = args[7].lower() if args[7] else None
        self.essentiality: str = args[8].lower() if args[8] else None
        self.side_chain_flexibility: str = args[9].lower() if args[9] else None
        self.chemical_group_in_the_side_chain: str = args[10].lower() if args[10] else None
        self.grantham_distance: Dict = args[11]

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_AA_RESIDUE]


if __name__ == '__main__':
    v = Variant()
    v.aliases = Variant.Name()
    v.aliases.org = "covariants"
    v.aliases.name = "ciccio"
    variant_contex = Variant.Characterization()
    variant_contex.org = "covariants"
    variant_contex.changes = ["un change", "un altro change"]
    v.org_2_aa_changes = variant_contex

    mongo_repr = v.__dict__()
    print(mongo_repr, type(mongo_repr))

