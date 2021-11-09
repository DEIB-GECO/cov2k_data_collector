from pymongo.cursor import Cursor
import re

class VariantAlt:

    def __init__(self):
        self.pangolin_ids = None
        self.gisaid_clades = None
        self.nesxstrain_ids = None
        self.who_names = None
        self.who_class = None
        self.ecdc_names = None
        self.ecdc_class = None
        self.cdc_class = None
        self.phe_names = None
        self.phe_class = None
        self.changes = None


def insert_variant_alt(db, variant: VariantAlt):
    # obj_to_find = dict()
    # # TODO
    # db.variants.find_one(obj_to_find)
    db.variants.insert_one({
        "pangolin_id": variant.pangolin_ids,
        "gisaid_clade": variant.gisaid_clades,
        "nexstrain_id": variant.nesxstrain_ids,
        "who_name": variant.who_names,
        "who_class": variant.who_class,
        "ecdc_name": variant.ecdc_names,
        "ecdc_class": variant.ecdc_class,
        "cdc_class": variant.cdc_class,
        "phe_name": variant.phe_names,
        "phe_class": variant.phe_class
    })


r_pango_lineages = re.compile(r'[A-Z](\.\d+)*')                         # e.g. B.1.1.7 or P or A.1.1.6.5
r_gisaid_clades = re.compile(r'[A-Z]+(/\d+[A-Z\-]\.\w+)?')              # e.g. GH/501Y.V2 or GRY
r_phe_name_1 = re.compile(r'(VOC|VUI)[\-\s]?(\d{4})(\d{2})/(\d{2})')    # e.g. VUI-202102/04 with dash/space or nothing
r_phe_name_2 = re.compile(r'(VOC|VUI)[\-\s]?(\d{2})([A-Z]{3})-(\d{2})')       # e.g. VUI-21MAR-02 with dash/space or nothing
r_who_name = re.compile(r'([Α-Ωα-ω\*])|(Alpha|Beta|Gamma|Delta|Epsilon|Zeta|Eta|Theta|Iota|Kappa|Lambda|Mu|Nu|Xi'
                        r'|Omicron|Pi|Rho|Sigma|Tau|Upsilon|Phi|Chi|Psi|Omega)')    # e.g. Ε or ε or Epsilon but not accented characters
r_nextstrain_name_old_build = re.compile(r'(\w+\.)?\w\.[A-Z]?\d+[A-Z]?(\.\w+)?')
r_nextstrain_name_build = re.compile(r'([A-Z]|\d+[A-Z])(\.[\w-]+)*')   # e.g. 20I.Alpha.V1 or 21A.21B or 21A.Delta or 21A.Delta.S.K417 or 21H or 20B.S.732A or 20A.EU1 or S.N439K or S.Q677H.Robin1 or S.H69-
r_nextstrain_name_with_alternative_nextstrain_names = re.compile(r'((2\d[A-Z])|(EU\d))([\./]?[\W]*((2\d[A-Z])|(EU\d))[\W]*)*')   # matches 20A or EU1 or 21A.21B or 21A/21B or 20A.EU1 or 20E (EU1)



class Variant:

    def __init__(self):
        self.name = None
        self.alias_group = None
        self.changes = None

    def to_dict(self):
        return {
            "name": self.name,
            "alias_group": self.alias_group,
            "changes": self.changes
        }


def insert_variant(db, variant: Variant):
    query = {
        "name": variant.name
    }
    assert db.variants.count_documents(query) <= 1, f"multiple variants exist with name {variant.name}"
    obj = db.variants.find_one(query)
    if not obj:
        db.variants.insert_one(variant.to_dict())
    else:
        # update aliases
        aliases = obj["alias_group"]
        # TODO find or create alias group

        # update changes
        if variant.changes:
            # without duplicates
            obj["changes"] = list(set(variant.changes + obj["changes"]))
            db.variants.update(
                query,
                obj
            )
