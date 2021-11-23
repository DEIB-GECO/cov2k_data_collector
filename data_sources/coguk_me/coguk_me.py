import os.path
import re
from os import chdir
from os.path import sep
import json
from pprint import pprint
from loguru import logger
from typing import Collection, Tuple, Iterable, Generator
import db_config.connection as connection
import db_config.mongodb_model as db_schema
from data_validators.change import AAChange

coguk_me_input_path = "data_sources/coguk_me/output_2021-08-24-21:52:16.json"


def transform() -> Iterable[Tuple[Tuple[db_schema.Effect], Tuple[db_schema.Reference], Tuple[db_schema.AAChange]]]:
    with open(coguk_me_input_path, "r", encoding="utf-8") as input_file:
        content: Collection[dict] = json.load(input_file)

    # regular expressions to recognize if the effect type
    re_mab = re.compile(r"^mab(?!\w+).*")
    re_plasma = re.compile(r"^plasma(?!\w+).*")
    re_vaccine = re.compile(r"^vaccine sera(?!\w+).*")

    for change_w_effects in content:
        method = None
        lv = "lower"
        aa_change_objects = list(AAChange.from_string("S:" + change_w_effects["change"]))
        aa_change_string = [x.get_encoded_string() for x in aa_change_objects]
        input_effects = {name.strip().lower() for name in change_w_effects["escape_mut_details"].split(",")}
        output_effects = set()
        for eff in input_effects:
            if re.fullmatch(re_mab, eff):
                output_effects.add("sensitivity to neutralizing mAbs")
            elif re.fullmatch(re_plasma, eff):
                output_effects.add("sensitivity to convalescent sera")
            elif re.fullmatch(re_vaccine, eff):
                output_effects.add("sensitivity to vaccine sera")
            else:
                logger.warning(f"new effect of type {eff} not recognized")

        # "tuple" below specifies to create a tuple, otherwise a generators is created instead
        effects = tuple(db_schema.Effect(eff_type, lv, method, aa_change_string) for eff_type in output_effects)
        references = tuple(db_schema.Reference(citation=ref["author"], uri=ref["doi"]) for ref in change_w_effects["references"])
        changes = tuple(x.to_db_obj() for x in aa_change_objects)
        yield effects, references, changes


def load(effects_w_references: Iterable[Tuple[Iterable[db_schema.Effect], Iterable[db_schema.Reference], Iterable[db_schema.AAChange]]]):
    for effects, their_references, aa_changes in effects_w_references:
        # insert changes
        db_schema.AAChange.db().insert_many(map(vars, aa_changes), ordered=False)
        # insert effect
        insert_result = db_schema.Effect.db().insert_many(map(vars, effects), ordered=False)
        # bind references to the effects they are supporting
        for reference in their_references:
            reference.effect_ids = insert_result.inserted_ids
        # insert references
        db_schema.Reference.db().insert_many(map(vars, their_references), ordered=False)


if __name__ == '__main__':
    chdir(f"..{sep}..")
    print(f"current work dir {os.path.abspath('.')}")

    # TODO si può arricchire il record di un reference con l'API https://api.crossref.org/swagger-ui/index.html
    #  o il suo port per python
    try:
        db_compatible_effects_and_references = transform()
        try:
            load(db_compatible_effects_and_references)
            # remove duplicate references (from aggregators/reference_rem_duplicates.js)
            db_schema.Reference.db().aggregate([
                    {
                        '$unwind': '$effect_ids'
                    }, {
                    '$group': {
                        '_id': {
                            'uri': '$uri',
                            'citation': '$citation',
                            'type': '$type',
                            'publisher': '$publisher'
                        },
                        'effect_ids': {
                            '$addToSet': '$effect_ids'
                        }
                    }
                    }, {
                        '$project': {
                            '_id': False,
                            'effect_ids': True,
                            'citation': '$_id.citation',
                            'type': '$_id.type',
                            'uri': '$_id.uri',
                            'publisher': '$_id.publisher'
                        }
                    }, {
                        '$out': 'evidence'
                    }
            ])
        finally:
            connection.close_conn()
    except:
        logger.exception("")







