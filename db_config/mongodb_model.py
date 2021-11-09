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
COLL_REFERENCE = 'reference'
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
            self.org: Optional[str] = org
            self.name: Optional[str] = name
            self.v_class: Optional[str] = v_class

    class Characterization:
        def __init__(self, org=None, changes=None):
            self.org: Optional[str] = org
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
        self.change_id: Optional[str] = change_id
        self.ref: Optional[str] = ref
        self.pos: Optional[int] = pos
        self.alt: Optional[str] = alt
        self.type: Optional[str] = _type
        self.length: Optional[int] = length
        self.is_optional: Optional[bool] = is_opt

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_NUC_CHANGE]


class AAChange:
    def __init__(self, change_id=None, protein=None, ref=None, pos=None, alt=None, _type=None, length=None, is_opt=None):
        self.change_id: Optional[str] = change_id
        self.protein: Optional[str] = protein
        self.ref: Optional[str] = ref
        self.pos: Optional[int] = pos
        self.alt: Optional[str] = alt
        self.type: Optional[str] = _type
        self.length: Optional[int] = length
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

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_REFERENCE]


class Structure:
    def __init__(self, annotation_id: str, start_on_ref: int = None, stop_on_ref: int = None,
                 protein_characterization=None):
        self.annotation_id: str = annotation_id
        self.start_on_ref: Optional[int] = start_on_ref
        self.stop_on_ref: Optional[int] = stop_on_ref
        self.protein_characterization: Optional[List[Structure.ProteinCharacterization]] = None

        self.set_protein_characterization(protein_characterization)

    class ProteinCharacterization:
        def __init__(self, protein_name: str, aa_length: int = None, aa_sequence: str = None):
            self.protein_name = protein_name
            self.aa_length: Optional[int] = aa_length
            self.aa_sequence: Optional[str] = aa_sequence

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
    def __init__(self, protein_name: str, start_on_prot: int, stop_on_prot: int, description: str = None, _type: str = None):
        self.protein_name: str = protein_name
        self.start_on_prot: int = start_on_prot
        self.stop_on_prot: int = stop_on_prot
        self.description: str = description
        self.type: str = _type

    @classmethod
    def db(cls):
        return connection.open_conn()[COLL_PROTEIN_REGION]


class AAResidue:
    def __init__(self, args):
        self.residue: str = args[0]
        self.molecular_weight: int = args[1]
        self.isoelectric_point: float = args[2]
        self.hydrophobicity: float = args[3]
        self.potential_side_chain_h_bonds: int = args[4]
        self.polarity: str = args[5]
        self.r_group_structure: str = args[6]
        self.charge: Optional[str] = args[7]
        self.essentiality: str = args[8]
        self.side_chain_flexibility: str = args[9]
        self.chemical_group_in_the_side_chain: str = args[10]
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

