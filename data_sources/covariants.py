import itertools
from utils import download_file
import warnings
from os.path import sep
from loguru import logger
import sys
import json
from typing import List, Set, Tuple
from data_validators.change import AAChange, Change as NUCChange
from data_validators.new_variant import recognize_organization
import db_config.mongodb_model as db_schema
import db_config.connection as connection
from data_validators.vocabulary import Organization

URL = "https://raw.githubusercontent.com/hodcroftlab/covariants/master/web/data/clusters.json"
LOCAL_PATH = "./generated/covariants/clusters.json" .replace("/", sep)


class SourceVariant:

    FIRST_LEVEL_INPUT_FIELDS = {
        "display_name"     # NAME
        , "build_name", "nextstrain_name", "display_name",  "build_name"     # ALIAS STRINGS
        , "alt_display_name", "alternative_names", "old_build_names", "build_name", "who_name"  # ALIAS ARRAYS
        , "pango_lineage", "pango_lineages"   # ALIAS OBJECTS
        , "cluster_data", "col", "graphing", "important", "nextstrain_build"    # OTHERS
        , "nextstrain_url", "snps", "type", "country_info"  # OTHERS
        , "mutations"   # MUTATIONS
    }

    def __init__(self, cluster_dict: dict):
        self.data = cluster_dict
        # check that this class is still compliant with the source data
        # type = variant and all properties are known
        assert self.data["type"] == "variant", f"cluster {self.id()} is not a variant"
        assert set(self.data.keys()).issubset(SourceVariant.FIRST_LEVEL_INPUT_FIELDS), \
            f"cluster {self.id()} includes unknown fields " \
            f"{set(self.data.keys()) - SourceVariant.FIRST_LEVEL_INPUT_FIELDS}"

    def id(self):
        return self.data["display_name"]

    def aliases(self):
        names = set()
        for key in ("build_name", "nextstrain_name", "display_name"):    # strings
            try:
                names.add(self.data[key])
            except KeyError:
                pass
        for key in ("alt_display_name", "alternative_names", "old_build_names", "who_name"):  # array
            try:
                names.update(self.data[key])
            except KeyError:
                pass
        for key in ("pango_lineage", "pango_lineages"):     # objects
            try:
                for obj in self.data[key]:
                    try:
                        names.add(obj["name"])
                    except KeyError:
                        pass
            except KeyError:
                pass
        # remove empty strings
        names = {n.strip() for n in names if n.strip()}
        return list(names)

    def aa_changes(self) -> List[AAChange]:
        non_syn_muts = []
        try:
            for mut in self.data["mutations"]["nonsynonymous"]:
                for aa_change in AAChange.from_parts(
                        mut["gene"].strip(),  # <- protein
                        mut["left"].strip(),
                        mut["pos"],
                        mut["right"].strip()):
                    non_syn_muts.append(aa_change)
        except KeyError:
            pass
        return non_syn_muts

    def nuc_changes(self) -> List[NUCChange]:
        syn_muts = []
        try:
            for mut in self.data["mutations"]["synonymous"]:
                for nuc_change in NUCChange.from_parts(
                        mut["left"].strip(),
                        mut["pos"],
                        mut["right"].strip()):
                    syn_muts.append(nuc_change)
        except KeyError:
            pass
        return syn_muts


def download_source_file() -> None:
    try:
        download_file(URL, LOCAL_PATH)
    except:
        logger.exception("Download failed. Aborting...")
        sys.exit(1)


def read_input_file() -> List[SourceVariant]:
    with open(LOCAL_PATH, mode='r') as input_file:
        try:
            source_variants: dict = json.load(input_file)
        except json.JSONDecodeError:
            logger.exception(f"Can't decode JSON {LOCAL_PATH}")
            sys.exit(1)

    # unnest
    source_variants: list = source_variants["clusters"]
    # filter
    parsed_variants = []
    for x in source_variants:
        if x["type"] != "variant":
            logger.info(f"variant {x['display_name']} of type {x['type']} skipped.")
            continue
        y = SourceVariant(x)
        parsed_variants.append(y)
    return parsed_variants


def transform(parsed_variants: List[SourceVariant]) -> Tuple[List, Set, Set]:
    # transform
    variants: List[db_schema.Variant] = []
    aa_changes: Set[db_schema.AAChange] = set()
    nuc_changes: Set[db_schema.NUCChange] = set()
    for variant_in in parsed_variants:
        aliases = [db_schema.Variant.Name(recognize_organization(name, Organization.COVARIANTS), name, None)
                   for name in variant_in.aliases()]
        aa_v_characterization = db_schema.Variant.Characterization(
            Organization.COVARIANTS,
            [change.get_encoded_string() for change in variant_in.aa_changes()]
        )
        nuc_v_characterization = db_schema.Variant.Characterization(
            Organization.COVARIANTS,
            [change.get_encoded_string() for change in variant_in.nuc_changes()]
        )
        # append to returned db objects
        variants.append(db_schema.Variant(aliases, [aa_v_characterization], [nuc_v_characterization]))
        aa_changes.update([change.to_db_obj() for change in variant_in.aa_changes()])
        nuc_changes.update([change.to_db_obj() for change in variant_in.nuc_changes()])
    return variants, aa_changes, nuc_changes


def load(variants: List[db_schema.Variant], aa_changes: Set[db_schema.AAChange], nuc_changes: Set[db_schema.NUCChange]):
    db_schema.Variant.db().insert_many(map(vars, variants))
    db_schema.AAChange.db().insert_many(map(vars, aa_changes))
    db_schema.NUCChange.db().insert_many(map(vars, nuc_changes))


if __name__ == "__main__":
    LOCAL_PATH = "." + LOCAL_PATH
    try:
        # EXTRACT
        # download_source_file()
        source_variants = read_input_file()

        # for var in source_variants:
        #     # DESCRIBE VARIANTS
        #     # logger.info(f"\n"
        #     #             f"name: {var.name()}\n"
        #     #             f"aliases: {var.aliases()}\n"
        #     #             f"aa_changes: {var.aa_changes()}\n"
        #     #             f"nuc_changes: {var.nuc_changes()}")
        #
        #     #DESCRIBE ALIASES
        #     names = var.aliases()
        #     names.append(var.id())
        #     names = list(set(names))
        #     organizations = list(map(lambda n: (n, '->', recognize_organization(n, Organization.COVARIANTS)), names))
        #     organizations.sort(key=lambda x: x[2])
        #     logger.info(f"\n"
        #                 f"IN CLUSTER {var.id()}:\n"
        #                 f"{organizations}")

        # TRANSFORM
        variants, aa_changes, nuc_changes = transform(source_variants)

        # number_gen = itertools.count()
        # for var in variants:
        #     print(f'{next(number_gen)} CLUSTER:')
        #     sorted_aliases = sorted(var.aliases, key=lambda x: x.org)
        #     print([vars(x) for x in sorted_aliases])

        #LOAD
        try:
            # load method requests a DB connection
            load(variants, aa_changes, nuc_changes)
        finally:
            connection.close_conn()


    except:
        logger.exception("")
