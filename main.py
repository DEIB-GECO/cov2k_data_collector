from time import sleep
from data_sources.aa_residues import aa_residues
from data_sources.coguk_me import coguk_me
from data_sources.our_sequence_annotations import our_sequence_annotations
from data_sources.ruba_aa_change_effects import effects_of_aa_changes
from data_sources.ruba_variant_effects import effects_of_variants
from data_sources import covariants
from data_sources import phe_variants
from data_sources import uniprot

if __name__ == '__main__':
    covariants.run()
    sleep(3)
    phe_variants.run()
    sleep(3)
    coguk_me.run()
    sleep(3)
    our_sequence_annotations.run()
    sleep(3)
    uniprot.run()
    sleep(3)
    aa_residues.run()
    sleep(3)
    effects_of_aa_changes.run()
    sleep(3)
    effects_of_variants.run()
