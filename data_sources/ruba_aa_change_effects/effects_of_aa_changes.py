from typing import Tuple, List, Iterable

from loguru import logger
from os.path import sep
from os import chdir
from data_validators.change import AAChange
import db_config.mongodb_model as db_model
import db_config.connection as connection

FILE_PATH_EFFECT_SINGLE_AA_CHANGE = "data_sources/ruba_aa_change_effects/a_change_effect.csv".replace("/", sep)
FILE_PATH_EFFECT_MULTIPLE_AA_CHANGES = "data_sources/ruba_aa_change_effects/group_of_changes_effects.csv".replace("/", sep)


def extract(file_path: str):
    with open(file_path, mode='r') as f:
        f.readline()    # skip header
        line_idx = 1
        error = False
        for l in f.readlines():
            line_idx += 1
            l = l.rstrip()
            products, aa_change_types, aa_refs, aa_pos, aa_alts, effect_type, eff_level, eff_method, evidence_uri, \
            evidence_citation, evidence_type, evidence_publisher = \
                (x if x and x != 'null' else None for x in l.split(";"))
            # remove escape formulae symbols used in execl
            aa_alts = aa_alts.lstrip("`")
            aa_refs = aa_refs.lstrip("`")
            products = products.split("/")
            aa_change_types = aa_change_types.split("/")
            aa_refs = aa_refs.split("/")
            aa_pos = aa_pos.split("/")
            aa_alts = aa_alts.split("/")
            if len(products) + len(aa_change_types) + len(aa_refs) + len(aa_pos) + len(aa_alts) != len(products) * 5 or \
                    len(products) * len(aa_change_types) * len(aa_refs) * len(aa_pos) * len(aa_alts) != pow(len(products), 5):
                logger.error(f"The line {line_idx}:{l} in file {file_path} does not have constant number of "
                             f"aa_change descriptors")
                error = True
                logger.debug(f"{len(products)} {len(aa_change_types)}  {len(aa_refs)}  {len(aa_pos)}  {len(aa_alts)}")
                logger.debug(f"{len(products) * 5}")
                # break
            aa_changes = []
            for aa_change_idx in range(len(products)):
                aa_changes.append((products[aa_change_idx],
                                   aa_refs[aa_change_idx],
                                   aa_pos[aa_change_idx],
                                   aa_alts[aa_change_idx]))
            yield aa_changes, \
                  (effect_type, eff_level, eff_method), \
                  (evidence_citation, evidence_type, evidence_uri, evidence_publisher)
    if error:
        raise ValueError("the input file contains errors.")


def transform_tuple(t: Tuple[List[Tuple], Tuple, Tuple]) -> Tuple[List[db_model.AAChange], db_model.Effect, db_model.Reference]:
    aa_changes, effect, evidence = t

    # tramsform aa change
    aa_changes_temp: List[Iterable[AAChange]] = [AAChange.from_parts(x[0], x[1], x[2], x[3]) for x in aa_changes]
    # unnest result from AAChange.from_parts
    aa_changes_temp: List[AAChange] = [y for x in aa_changes_temp for y in x]
    assert len(aa_changes) == len(aa_changes_temp)

    # transform effect and evidence
    effect = (x.strip() if x else None for x in effect)
    effect = list(x if x else None for x in effect)
    evidence = (x.strip() if x else None for x in evidence)
    evidence = list(x if x else None for x in evidence)

    parsed_aa_changes = [x.to_db_obj() for x in aa_changes_temp]
    effect = db_model.Effect(effect[0], effect[1], effect[2], [x.get_encoded_string() for x in aa_changes_temp])
    evidence = db_model.Reference(None, evidence[0], evidence[1], evidence[2], evidence[3])

    return parsed_aa_changes, effect, evidence


def load(tuples):
    for t in tuples:
        aa_changes, effect, evidence = t
        # insert aa_changes
        db_model.AAChange.db().insert_many(map(vars, aa_changes))
        # insert effects
        insert_result = db_model.Effect.db().insert_one(vars(effect))
        effect_id = insert_result.inserted_id
        # insert evidence
        evidence.effect_ids = [effect_id]
        db_model.Reference.db().insert_one(vars(evidence))


def run():
    try:
        extracted = list(extract(FILE_PATH_EFFECT_SINGLE_AA_CHANGE))
        transformed = [transform_tuple(e) for e in extracted]
        try:
            load(transformed)
        finally:
            connection.close_conn()
    except:
        logger.exception("")

    try:
        extracted = list(extract(FILE_PATH_EFFECT_MULTIPLE_AA_CHANGES))
        transformed = [transform_tuple(e) for e in extracted]
        try:
            load(transformed)
        finally:
            connection.close_conn()
    except:
        logger.exception("")


if __name__ == '__main__':
    chdir(f"..{sep}..{sep}")
    run()

