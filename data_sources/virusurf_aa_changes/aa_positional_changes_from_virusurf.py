from os import chdir
from os.path import sep
from data_validators.change import AAChange
from typing import Generator
import db_config.mongodb_model as kb_model
from db_config.connection import close_conn
from loguru import logger

SOURCE_FILE_PATH = "data_sources/virusurf_aa_changes/distinct_aa_changes_vcm_du_21_11_30.csv".replace('/', sep)


def extract_transform() -> Generator[AAChange, None, None]:
    with open(SOURCE_FILE_PATH, "r") as source_file:
        source_file.readline()  # skip header
        for line in source_file:
            virusurf_proitein, ref, pos, alt, _type, length = line.rstrip('\n').split(',')
            for change_4_kb in AAChange.from_parts(virusurf_proitein, ref, pos, alt):
                yield change_4_kb.to_db_obj()


def load(generator_of_aa_changes):
    db = kb_model.AAChange.db()
    try:
        db.insert_many(list(map(vars, generator_of_aa_changes)))
    except:
        logger.exception("")
    finally:
        close_conn()


def run():
    load(extract_transform())


if __name__ == '__main__':
    chdir(f'..{sep}..{sep}')
    run()
