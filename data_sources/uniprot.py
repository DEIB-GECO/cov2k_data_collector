import requests as requests
import pandas as pd
from os.path import sep
from os import chdir
import db_config.mongodb_model as db_schema
from db_config.mongodb_model import ProteinRegion
import db_config.connection as connection

download_location = f".{sep}generated{sep}uniprot{sep}original_protein_annotations.csv"


def translate_protein(protein_code):
    if protein_code == 'NCAP_SARS2':
        protein_name = "N"
    elif protein_code == 'NS8_SARS2':
        protein_name = "NS8"
    elif protein_code == 'NS7A_SARS2':
        protein_name = "NS7A"
    elif protein_code == 'NS6_SARS2':
        protein_name = "NS6"
    elif protein_code == 'VME1_SARS2':
        protein_name = "M"
    elif protein_code == 'VEMP_SARS2':
        protein_name = "E"
    elif protein_code == 'AP3A_SARS2':
        protein_name = "NS3"
    elif protein_code == 'SPIKE_SARS2':
        protein_name = "S"
    elif protein_code == 'R1A_SARS2':
        protein_name = "ORF1A"
    elif protein_code == 'R1AB_SARS2':
        protein_name = "ORF1AB"
    elif protein_code == 'ORF3C_SARS2':
        protein_name = "ORF3c"
    elif protein_code == 'ORF3D_SARS2':
        protein_name = "ORF3D"
    elif protein_code == 'ORF3B_SARS2':
        protein_name = "ORF3B"
    elif protein_code == 'NS7B_SARS2':
        protein_name = "NS7B"
    elif protein_code == 'ORF9C_SARS2':
        protein_name = "ORF9C"
    elif protein_code == 'ORF9B_SARS2':
        protein_name = "ORF9B"
    else:
        protein_name = protein_code
    return protein_name


def download_annotation_file():

    all_protein_codes = [
        "P0DTG1", "P0DTG0", "P0DTF1", "P0DTD8", "P0DTD3", "P0DTD2", "P0DTD1", "P0DTC9", "P0DTC8", "P0DTC7", "P0DTC6",
        "P0DTC5", "P0DTC4", "P0DTC3", "P0DTC2", "P0DTC1"
    ]
    url = "https://www.ebi.ac.uk/proteins/api/features/"

    array_all = []
    for protein_code in all_protein_codes:
        full_url = url + protein_code
        response = requests.get(full_url)
        response = response.json()

        features = response['features']
        for single_feature in features:
            # 'accession': response.get('accession'),
            single_line = {}
            if 'entryName' in response:
                single_line['Protein'] = translate_protein(response['entryName']).split(' ')[0]
            else:
                single_line['Protein'] = None

            if 'type' in single_feature:
                single_line['Type'] = single_feature['type']
            else:
                single_line['Type'] = None

            if 'category' in single_feature:
                single_line['Category'] = single_feature['category']
            else:
                single_line['Category'] = None

            if 'description' in single_feature:
                description = single_feature['description'].strip()
                if description:
                    single_line = description
            else:
                single_line['Description'] = None

            if 'begin' in single_feature:
                single_line['Begin'] = single_feature['begin']
            else:
                single_line['Begin'] = None

            if 'end' in single_feature:
                single_line['End'] = single_feature['end']
            else:
                single_line['End'] = None

            if 'evidences' in single_feature:
                evidences = single_feature['evidences']
                array_url = []
                for evidence in evidences:
                    if 'source' in evidence:
                        array_url.append(evidence['source']['url'])
                single_line['EvidenceUrls'] = array_url
            else:
                single_line['EvidenceUrls'] = []
            array_all.append(single_line)

    table = pd.DataFrame(array_all)
    # noinspection PyTypeChecker
    table.to_csv(download_location, index=False, header=True, sep="\t")


def load():
    protein_regions = []
    with open(download_location, "r") as downloaded_file:
        downloaded_file.readline()  # skip header
        for line in downloaded_file.readlines():
            protein_name, _type, category, description, begin, end, _ = line[:line.rindex("[")].split("\t")
            description = description if description else None
            _type = _type if _type else None
            if _type in ["VARIANT", "MUTAGEN"]:
                continue
            protein_name = protein_name if protein_name else None
            assert protein_name != None, f"Protein name is NULL in {line}"
            protein_name = protein_name.upper()
            protein_regions.append(ProteinRegion(protein_name, begin, end, description, _type, category))
    for p in protein_regions:
        print(vars(p))
    ProteinRegion.db().insert_many(map(vars, protein_regions))


if __name__ == '__main__':
    chdir(f"..{sep}")   # move to root dir
    # download_annotation_file()
    try:
        load()
    finally:
        connection.close_conn()
