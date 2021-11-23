from os.path import sep
from os import chdir
from pprint import pprint
import db_config.mongodb_model as db_schema
from db_config.mongodb_model import Structure
import db_config.connection as connection

file_path = f".{sep}data_sources{sep}our_sequence_annotations{sep}sars_cov_2.tsv"


def translate_protein_name(name: str):
    dictionary = {
        "ORF1ab polyprotein": "ORF1AB",
        "ORF1a polyprotein": "ORF1A",
        "Spike (surface glycoprotein)": "S",
        "NS3 (ORF3a protein)": "NS3",
        "E (envelope protein)": "E",
        "M (membrane glycoprotein)": "M",
        "NS6 (ORF6 protein)": "NS6",
        "NS7a (ORF7a protein)": "NS7A",
        "NS7b (ORF7b)": "NS7B",
        "NS8 (ORF8 protein)": "NS8",
        "N (nucleocapsid phosphoprotein)": "N",
        "ORF10 protein": "ORF10",
        "NSP12 (RNA-dependent RNA polymerase)": "NSP12",
        "NSP13 (helicase)": "NSP13",
        "NSP14 (3'-to-5' exonuclease)": "NSP14",
        "NSP15 (endoRNAse)": "NSP15",
        "NSP16 (2'-O-ribose methyltransferase)": "NSP16",
        "NSP1 (leader protein)": "NSP1",
        "NSP2": "NSP2",
        "NSP3": "NSP3",
        "NSP4": "NSP4",
        "NSP5 (3C-like proteinase)": "NSP5",
        "NSP6": "NSP6",
        "NSP7": "NSP7",
        "NSP8": "NSP8",
        "NSP9": "NSP9",
        "NSP10": "NSP10",
        "NSP11": "NSP11",
    }
    try:
        return dictionary[name]
    except KeyError:
        raise AssertionError("Translation dictionary incomplete")


def transform():
    with open(file_path, mode="r") as file:
        rows = dict()
        for line in file.readlines():
            _, _, ann_type, begin_end, gene, protein, _, aa_sequence = line.rstrip().split("\t")
            if ann_type in ("mature_protein_region", "CDS", "gene"):
                annotation_id = gene
            else:
                annotation_id = ann_type
            # find or create new nuc_annotation
            nuc_annotation = rows.get(annotation_id)
            if not nuc_annotation:
                nuc_annotation = Structure(annotation_id)
                rows[annotation_id] = nuc_annotation
            # compute data
            begin = int(begin_end[:begin_end.index(",")])
            end = int(begin_end[begin_end.rindex(",") + 1:])
            # pour data
            if ann_type in ("mature_protein_region", "CDS"):
                length = end - begin
                length += 1 if ";" not in begin_end else 2
                assert length % 3 == 0, "Protein length not multiple of 3!"
                protein_characterization = Structure.ProteinCharacterization(
                    protein_name=translate_protein_name(protein),
                    aa_length=int(length/3),
                    aa_sequence=aa_sequence
                )
                # find or create protein_characterization
                if not nuc_annotation.protein_characterization:
                    nuc_annotation.protein_characterization = [protein_characterization]
                else:
                    nuc_annotation.protein_characterization.append(protein_characterization)
            else:
                nuc_annotation.start_on_ref = begin
                nuc_annotation.stop_on_ref = end
    return rows


def load(transformed_nuc_annotations: dict):
    for _, nuc_annotation in transformed_nuc_annotations.items():
        Structure.db().insert_one(vars(nuc_annotation))


if __name__ == '__main__':
    chdir(f"..{sep}..{sep}")
    transformed_annotations = transform()
    try:
        load(transformed_annotations)
    finally:
        connection.close_conn()