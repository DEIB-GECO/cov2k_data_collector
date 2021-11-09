import re
import zipfile
from loguru import logger
import sys
import glob
import yaml
from os.path import sep
from os import chdir, getcwd

import data_validators.new_variant
from utils import download_file, download_dir_for
from typing import Collection, List, Set, Tuple
from data_validators.change import AAChange, Change as NUCChange
from data_validators.vocabulary import Organization
from data_validators.new_variant import recognize_organization
import db_config.mongodb_model as db_schema
import db_config.connection as connection


# files to download from directory:
# https://github.com/phe-genomics/variant_definitions/tree/main/variant_yaml
# the following URL is to download the repo with wget, curl, etc...
URL = "https://api.github.com/repos/phe-genomics/variant_definitions/zipball/"
LOCAL_PATH = download_dir_for("phe") + "git_repo.zip"


def download_source_files() -> None:
    """
    :return: a list of relative file paths.
    For example ./generated/phe/git_repo/phe-genomics-variant_definitions-1612814/variant_yaml/cheesy-styling.yml
    """
    try:
        download_file(URL, LOCAL_PATH)
    except:
        logger.exception("Download failed. Aborting...")
        sys.exit(1)
    with zipfile.ZipFile(LOCAL_PATH, 'r') as zip_file:
        zip_file.extractall(LOCAL_PATH.rstrip(".zip"))


def find_source_files() -> Collection[str]:
    pathstring_4_glob = \
        LOCAL_PATH.rstrip(".zip") \
        + f"{sep}**{sep}" \
        + "*.yml"
    # /**/ includes files in any subdirectory when recursive=True
    source_files = glob.glob(pathstring_4_glob, recursive=True)
    if len(source_files) == 0:
        logger.error(f"No .yml file (PHE variant definition) found in repo: {URL}\n"
                     f"Aborting...")
        sys.exit(1)
    return source_files


class SourceVariant:

    FIRST_LEVEL_INPUT_FIELDS = {
        "unique-id"
        , "phe-label"  # NAME
        , "who-label"       # ALIAS STRING
        , "alternate-names", "belongs-to-lineage"     # ALIAS ARRAY
        , "description", "information-sources"         # OTHERS
        , "variants", "additional-mutations"  # CHANGES ARRAY
        , "calling-definition", "acknowledgements", "acknowledgments", "curators"  # OTHERS
    }

    CHANGE_LEVEL_INPUT_FIELDS = {
        "codon-change"     # CODON CHANGE
        , "gene", "one-based-reference-position"    # POSITION OF CODON
        , "snp-codon-position"              # POSITION OF NUC CHANGE INSIDE CODON
        , "predicted-effect"     # SYNONYMOUS OR NON-SYNONYMOUS
        , "reference-base", "type", "variant-base"  # NUC REF TYPE ALT
        , "protein", "protein-codon-position"       # CORRESPONDING PROTEIN POSITION
        , "amino-acid-change"                       # AA CHANGE (FULLY DESCRIBED) (PRESENT IF NON-SYNONYMOUS)
    }

    re_aa_change = re.compile("([A-Z-\*]*)(\d+)([A-Z-\*]*)")

    def __init__(self, yaml_parsed_dict: dict):
        self.data = yaml_parsed_dict
        # check that all properties are known
        assert set(self.data.keys()).issubset(SourceVariant.FIRST_LEVEL_INPUT_FIELDS), \
            f"variant {self.id()} includes unknown fields: " \
            f"{set(self.data.keys()) - SourceVariant.FIRST_LEVEL_INPUT_FIELDS}"
        for change_definition in self.data["variants"]:
            assert set(change_definition.keys()).issubset(SourceVariant.CHANGE_LEVEL_INPUT_FIELDS), \
                f"variant {self.id()} includes change definition(s) with unknown fields: " \
                f"{set(change_definition.keys()) - SourceVariant.CHANGE_LEVEL_INPUT_FIELDS}"
            if change_definition.get("predicted-effect"):
                assert change_definition["predicted-effect"] in {"synonymous", "non-synonymous", "no-effect"}, \
                    f"variant {self.id()} includes a unrecognized variant type: " \
                    f"{change_definition['predicted-effect']}"

        for (k, v) in self.data.items():
            if isinstance(v, list):
                self.data[k] = [_ for _ in v if _]  # removes Nones from lists
        # remove empty lists, none values
        self.data = {key: value for (key, value) in self.data.items() if value}


    def id(self):
        return self.data["unique-id"]

    def aliases(self) -> Collection[str]:
        names: Set[str] = set()
        for key in ("phe-label", "who-label"):      # strings
            try:
                if self.data[key]:
                    names.add(self.data[key])
            except KeyError:
                pass
        for key in ("alternate-names",):   # arrays
            try:
                if self.data[key]:
                    names.update(self.data[key])
            except KeyError:
                pass
            # except Exception as e:
            #     logger.error(f"variant id {self.id()} ")
            #     raise e
        for key in ("belongs-to-lineage",):  # arrays of objects
            try:
                for obj in self.data[key]:
                    if obj.values():
                        names.update(obj.values())
            except KeyError:
                pass
        #   CHECK IF "description" contains a change related to a lineage of those in "belongs-to-lineage"
        if self.data.get("description") and self.data.get("belongs-to-lineage"):
            names_in_belong_to_lineage = []
            # unnest belongs-to-lineage
            try:
                for obj in self.data["belongs-to-lineage"]:
                    names_in_belong_to_lineage += obj.values()
            except KeyError:
                pass
            if names_in_belong_to_lineage:
                names_in_belong_to_lineage = set(names_in_belong_to_lineage)
                words_in_description = set(self.data['description'].split(' '))
                described_lineages = names_in_belong_to_lineage & words_in_description
                if described_lineages:
                    regex = data_validators.new_variant.Commons.AAChangeNoProt.regex
                    for word in words_in_description:
                        if regex.match(word):
                            logger.warning(f"Found that word {word} describes lineage(s) {described_lineages}. "
                                           f"It is gonna be removed from set of aliases.")
                            assert len(described_lineages) == 1, "Special case not handled yet:" \
                                                                 " Description says something about 1+ variant names." \
                                                                 " Unable to choose which variant to remove between " \
                                                                 f"{described_lineages} - (modifying word {word})."
                            names.remove(described_lineages.pop())

        names -= {None}  # sometimes None is in names
        names -= {str(None)}
        names = {x.strip() for x in names if x.strip()}
        return list(names)

    def aa_changes(self) -> Collection[AAChange]:
        non_syn_muts = []

        def read_change(mut: dict, container: List[AAChange]) -> None:
            _type = mut.get("predicted-effect")
            if _type and _type == "non-synonymous":
                for aa_change in AAChange.from_string(
                        mut["protein"]+":"+mut["amino-acid-change"]):
                    container.append(aa_change)

        try:
            for mut in self.data["variants"]:
                read_change(mut, non_syn_muts)
            if self.data.get("additional-mutations"):
                additional_changes: List[AAChange] = []
                for mut in self.data["additional-mutations"]:
                    read_change(mut, additional_changes)
                for x in additional_changes:
                    x.set_optional()
                non_syn_muts += additional_changes
        except KeyError:
            logger.exception("")
        return non_syn_muts

    def nuc_changes(self) -> Collection[NUCChange]:
        syn_muts = []

        def read_change(mut: dict, container: List[NUCChange]) -> None:
            _type = mut.get("predicted-effect")
            if not _type or _type == "synonymous" or _type == "no-effect":
                for nuc_change in NUCChange.from_parts(
                        mut["reference-base"].strip(),
                        mut["one-based-reference-position"],
                        mut["variant-base"].strip()):
                    container.append(nuc_change)

        try:
            for mut in self.data["variants"]:
                read_change(mut, syn_muts)
            if self.data.get("additional-mutations"):
                additional_changes: List[NUCChange] = []
                for mut in self.data["additional-mutations"]:
                    read_change(mut, additional_changes)
                for x in additional_changes:
                    x.set_optional()
                syn_muts += additional_changes
        except KeyError:
            logger.exception("")
        return syn_muts


def read_input_files(file_paths: Collection[str]) -> Collection[SourceVariant]:
    parsed_files = []
    for file_path in file_paths:
        with open(file_path, mode='r') as file:
            file_content = yaml.safe_load(file)
            parsed_files.append(SourceVariant(file_content))

    # for var in parsed_files:
    #     try:
    #         logger.info(f"\n"
    #                     f"name: {var.id()}\n"
    #                     f"aliases: {var.aliases()}\n"
    #                     f"aa_changes: {[x.get_encoded_string()+':'+str(x.optional) for x in var.aa_changes()]}\n"
    #                     f"nuc_changes: {[x.get_encoded_string()+':'+str(x.optional) for x in var.nuc_changes()]}")
    #     except:
    #         logger.exception(f"Exception in var {var.id()}")
    #         break

    return parsed_files


def transform(parsed_variants: Collection[SourceVariant]) -> Tuple[List, Set, Set]:
    # transform
    variants: List[db_schema.Variant] = []
    aa_changes: Set[db_schema.AAChange] = set()
    nuc_changes: Set[db_schema.NUCChange] = set()
    logger.warning("PHE modules ignores distinction between optional changes and normal ones")
    for variant_in in parsed_variants:
        # find aliases
        aliases = [db_schema.Variant.Name(recognize_organization(name, None), name, None)
                   for name in variant_in.aliases()]
        # clean ignored names
        aliases = [x for x in aliases if x.org is not None]
        if not aliases:
            logger.warning(f"variant {variant_in.id()} skipped because it has no valid names")
            continue
        # assign VOC/VUI
        for x in aliases:
            if x.org == Organization.PHE:
                if x.name.startswith("VUI"):
                    x.v_class = "VUI"
                elif x.name.startswith("VOC"):
                    x.v_class = "VOC"
                else:
                    raise AssertionError(f"Cannot assign variant calss to phe variant {x.name}")
        # create AA characterization
        aa_v_characterization = db_schema.Variant.Characterization(
            Organization.PHE,
            [change.get_encoded_string() for change in variant_in.aa_changes()]
        )
        # create NUC characterization
        nuc_v_characterization = db_schema.Variant.Characterization(
            Organization.PHE,
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


if __name__ == '__main__':
    chdir(f"..{sep}")
    try:
        # example_file_url = "https://raw.githubusercontent.com/phe-genomics/variant_definitions/main/variant_yaml/animating-thermos.yml"
        # example_file = download_dir_for("phe") + "animating-thermos.yml"

        # with open(example_file, 'r') as stream:
        #     parsed_file: dict = yaml.safe_load(stream)
        #     for (k, v) in parsed_file.items():
        #         if isinstance(v, list):
        #             parsed_file[k] = [_ for _ in v if _]  # removes Nones from lists
        #     # remove empty lists, none values
        #     parsed_file = {key: value for (key, value) in parsed_file.items() if value}
        #
        #     # PRINT AS DICT
        #     for key, value in parsed_file.items():
        #         print(key + " : " + str(value))
        #     print("\n")

            # for key in ("belongs-to-lineage",):  # arrays of objects
            #     try:
            #         for obj in parsed_file[key]:
            #             print(obj.values())
            #     except KeyError:
            #         pass

            # # PARSE
            # var = SourceVariant(parsed_file)
            # # DESCRIBE VARIANTS
            # logger.info(f"\n"
            #             f"name: {var.id()}\n"
            #             f"aliases: {var.aliases()}\n"
            #             f"aa_changes: {[x.get_encoded_string() for x in var.aa_changes()]}\n"
            #             f"nuc_changes: {[x.get_encoded_string() for x in var.nuc_changes()]}")



        # download_source_files()
        source_files = find_source_files()
        parsed_variants = read_input_files(source_files)

        # for variant_in in parsed_variants:
        #     # aliases = [db_schema.Variant.Name(recognize_organization(name, Organization.PHE), name, None)
        #     #            for name in variant_in.aliases()]
        #     aliases = [db_schema.Variant.Name(recognize_organization(name, None), name, None)
        #                for name in variant_in.aliases()]
        #     names_with_org = [(x.name, '->', x.org) for x in aliases]
        #     print("\n"
        #           f"id {variant_in.id()}\n"
        #           f"{len(aliases)} aliases: {names_with_org}")
        #     aliases = [x for x in aliases if x.org is not None]
        #     names_with_org = [(x.name, '->', x.org) for x in aliases]
        #     print(f"{len(aliases)} aliases after cleaning")


        variants, aa_changes, nuc_changes = transform(parsed_variants)

        for v in variants:
            try:
                print(vars(v))
            except:
                logger.exception(f"exception with variant:\n"
                                 f"{v.aliases}\n"
                                 f"{v.org_2_aa_changes}\n"
                                 f"{v.org_2_nuc_changes}\n")

        # LOAD
        try:
            # load method requests a DB connection
            load(variants, aa_changes, nuc_changes)
        finally:
            connection.close_conn()

    except:
        logger.exception("")


