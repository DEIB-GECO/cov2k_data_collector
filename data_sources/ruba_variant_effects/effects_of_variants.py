from os.path import sep
from os import chdir
from typing import Tuple

import data_validators.new_variant
from db_config.mongodb_model import *
from loguru import logger
import db_config.connection as connection


FILE_PATH_EFFECTS_OF_VARIANTS = "data_sources/ruba_variant_effects/variants_effects.csv".replace("/", sep)


def extract():
    with open(FILE_PATH_EFFECTS_OF_VARIANTS, mode="r") as f:
        f.readline() # skip header
        line_idx = 1
        errors_found = False
        for l in f.readlines():
            line_idx += 1
            try:
                _, pango_id, \
                effect_type, eff_level, eff_method, \
                evidence_citation, evidence_publisher, evidence_type, evidence_uri, _ = l.rstrip().split(";")
                for single_pango_id in pango_id.split("/"):
                    yield single_pango_id, (effect_type, eff_level, eff_method), (evidence_citation, evidence_type,
                                                                           evidence_uri, evidence_publisher)
            except ValueError:
                logger.exception(f"Error in line {line_idx}: {l}")
                errors_found = True
                break
    if errors_found:
        raise ValueError("Errors found")


def transform(one_effect: Tuple[str, Tuple[str, str, str], Tuple[str, str, str, str]]):
    pango_id, (effect_type, eff_level, eff_method), (evidence_citation, evidence_type,
                                                     evidence_uri, evidence_publisher) = one_effect
    strings = (pango_id, effect_type, eff_level, eff_method, evidence_citation, evidence_type, evidence_uri, evidence_publisher)
    strings = list(x if x and x != "null" else None for x in strings)
    return strings[0], strings[1:4], strings[4:]


def load(row: Tuple[str, Tuple[Tuple[str]], Tuple[Tuple[str]]]):
    pango_id, (effect_type, eff_level, eff_method), (evidence_citation, evidence_type,
                                                     evidence_uri, evidence_publisher) = row
    variant_org = data_validators.new_variant.recognize_organization(pango_id)
    try:
        variant = Variant(
            aliases=[Variant.Name(org=variant_org, name=pango_id, v_class=None)]
        )
        effect = Effect(effect_type, eff_level, eff_method)
        evidence = Reference(citation=evidence_citation
                                           , _type=evidence_type
                                           , uri=evidence_uri
                                           , publisher=evidence_publisher)


        id_inserted_effect = Effect.db().insert_one(vars(effect)).inserted_id
        # id is of type ObjectID
        variant.set_effects([id_inserted_effect])
        evidence.effect_ids = [id_inserted_effect]

        Variant.db().insert_one(vars(variant))
        Reference.db().insert_one(vars(evidence))
    except:
        logger.exception("")
        raise


def run():
    try:
        for item in extract():
            item = transform(item)
            load(item)
    finally:
        connection.close_conn()


if __name__ == '__main__':
    chdir(f"..{sep}..{sep}")
    run()