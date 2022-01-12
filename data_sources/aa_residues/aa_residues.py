from os.path import sep
from os import chdir
from pprint import pprint
from typing import Iterable, Tuple, Generator, Dict

import numpy

from db_config.mongodb_model import AAResidue
from db_config.connection import close_conn

file_path_amino_acid_chemical_prop = f"data_sources{sep}aa_residues{sep}Amino_acids_properities.csv"
file_path_grantham_dist = f"data_sources{sep}aa_residues{sep}Grantham_distance.csv"


def transform_grantham_dist() -> Dict:
    with open(file_path_grantham_dist, "r") as granth_dist_file:
        aa_residue_table_coordinates = dict()
        table_horizontal_header = granth_dist_file.readline().rstrip().split(";")[:19]
        X_coord = iter(range(0, len(table_horizontal_header)))
        for aa_residue in table_horizontal_header:
            aa_residue_table_coordinates[aa_residue] = {
                "X": next(X_coord)
            }
        table_vertical_header = []

        Y_coord = iter(range(0, len(table_horizontal_header)))
        for line in granth_dist_file.readlines():
            _, aa_residue = line.rstrip().rsplit(";", maxsplit=1)
            table_vertical_header.append(aa_residue)
            coord_obj = aa_residue_table_coordinates.get(aa_residue)
            if not coord_obj:
                aa_residue_table_coordinates[aa_residue] = {
                    "Y": next(Y_coord)
                }
            else:
                coord_obj["Y"] = next(Y_coord)

    # make table of distances
    matrix = []
    with open(file_path_grantham_dist, "r") as granth_dist_file:
        granth_dist_file.readline()
        for line in granth_dist_file.readlines():
            elements = line.split(";")[:19]
            elements = [e if e != "" else None for e in elements]
            matrix.append(elements)

    def list_grantham_distance_from_residue(aa_res: str):
        distances = dict()
        coordinates_of_ = aa_residue_table_coordinates[aa_res]
        X_1 = coordinates_of_.get("X", None)
        Y_1 = coordinates_of_.get("Y", None)
        if X_1 is not None and Y_1 is not None:
            # descend line on X axis number X_1
            for idx, row in enumerate(matrix):
                if idx < Y_1:
                    distances[table_vertical_header[idx]] = row[X_1]
            # traverse line on Y axis number Y_1
            row = matrix[Y_1]
            for idx in range(X_1 + 1, len(row)):
                distances[table_horizontal_header[idx]] = row[idx]
        elif X_1 is not None:
            # traverse line on X axis number X_1
            for idx, row in enumerate(matrix):
                distances[table_vertical_header[idx]] = row[X_1]
        elif Y_1 is not None:
            # traverse line on Y axis number Y_1
            row = matrix[Y_1]
            for idx, col in enumerate(table_horizontal_header):
                distances[col] = row[idx]
        return distances


    all_residues = set(table_vertical_header) | set(table_horizontal_header)
    return {r: list_grantham_distance_from_residue(r) for r in all_residues}


def transform() -> Generator[Tuple, None, None]:
    with open(file_path_amino_acid_chemical_prop, "r") as file:
        file.readline()
        for line in file.readlines():
            residue, mol_weight, isoelectric_p, hydrophob, side_chain_h_bonds, polarity, r_group_struct, charge, \
            essentiality, side_chain_flexibility, side_chain_chem_group, _ = line.rstrip().split(";", maxsplit=11)
            # correct types and NULLs
            if charge == "":
                charge = None
            mol_weight = int(mol_weight)
            isoelectric_p = float(isoelectric_p.replace(",", "."))
            hydrophob = float(hydrophob.replace(",", "."))
            side_chain_h_bonds = int(side_chain_h_bonds)
            # return
            # print(residue, mol_weight, isoelectric_p, hydrophob, side_chain_h_bonds, polarity, r_group_struct, charge,
            # essentiality, side_chain_flexibility, side_chain_chem_group)
            yield residue, mol_weight, isoelectric_p, hydrophob, side_chain_h_bonds, polarity, r_group_struct, charge,\
                  essentiality, side_chain_flexibility, side_chain_chem_group


def load(aa_residues: Iterable[Tuple]):
    db_objects = []
    for description in aa_residues:
        db_objects.append(AAResidue(description))
    AAResidue.db().insert_many(map(vars, db_objects))


def run():
    aa_residues = list(transform())
    grantham_dist_for_residues = transform_grantham_dist()
    aa_residues = [(*aa_prop, grantham_dist_for_residues[aa_prop[0]]) for aa_prop in aa_residues]

    try:
        load(aa_residues)
    finally:
        close_conn()

if __name__ == "__main__":
    chdir(f"..{sep}..{sep}")
    run()
