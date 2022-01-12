import re
from typing import Optional

from loguru import logger

vcm_syntax_2_short_protein_name = {
    "NSP11": "NSP11",
    "NSP13 (helicase)": "NSP13",
    "NSP5 (3C-like proteinase)": "NSP5",
    "NSP12 (RNA-dependent RNA polymerase)": "NSP12",
    "ORF1ab polyprotein": "ORF1AB",
    "NS7b (ORF7b)": "NS7B",
    "N (nucleocapsid phosphoprotein)": "N",
    "ORF1a polyprotein": "ORF1A",
    "NSP10": "NSP10",
    "NSP16 (2'-O-ribose methyltransferase)": "NSP16",
    "NSP14 (3'-to-5' exonuclease)": "NSP14",
    "NSP1 (leader protein)": "NSP1",
    "NSP7": "NSP7",
    "NSP3": "NSP3",
    "NS7a (ORF7a protein)": "NS7A",
    "NSP2": "NSP2",
    "NSP9": "NSP9",
    "NSP6": "NSP6",
    "NSP4": "NSP4",
    "NSP8": "NSP8",
    "NS8 (ORF8 protein)": "NS8",
    "NS6 (ORF6 protein)": "NS6",
    "ORF10 protein": "NS10",
    "NSP15 (endoRNAse)": "NSP15",
    "Spike (surface glycoprotein)": "S",
    "NS3 (ORF3a protein)": "NS3",
    "M (membrane glycoprotein)": "M",
    "E (envelope protein)": "E"
}
protein_name_replacements = {
    'GLYCOPROTEIN': '',
    'PHOSPHOPROTEIN': '',
    'PROTEIN': '',
    'SURFACE': 'S',
    'ENVELOPE': 'E',
    'NUCLEOCAPSID': 'N',
    'MEMBRANE': 'M'
}
regex_orf_non_polyprot = re.compile(r'(ORF|NS)((1\d)|([2-9]+))(\w?)')


def convert_protein(name: str, start_pos: Optional[int] = None, stop_pos: Optional[int] = None):
    new_name = name.upper()
    new_start_pos = start_pos
    new_stop_pos = stop_pos

    # substitution based on equivalence test
    if name in vcm_syntax_2_short_protein_name.keys():
        new_name = vcm_syntax_2_short_protein_name[name]
    # substitution based on string inclusion (entailment)
    elif 'SPIKE' in new_name:
        new_name = 'S'
    elif 'NSP16' in new_name:
        new_name = 'NSP16'
    elif 'NSP15' in new_name:
        new_name = 'NSP15'
    elif 'NSP14' in new_name:
        new_name = 'NSP14'
    elif 'NSP13' in new_name:
        new_name = 'NSP13'
    elif 'NSP12' in new_name:
        new_name = 'NSP12'
    elif 'NSP11' in new_name:
        new_name = 'NSP11'
    elif 'NSP10' in new_name:
        new_name = 'NSP10'
    elif 'NSP9' in new_name:
        new_name = 'NSP9'
    elif 'NSP8' in new_name:
        new_name = 'NSP8'
    elif 'NSP7' in new_name:
        new_name = 'NSP7'
    elif 'NSP6' in new_name:
        new_name = 'NSP6'
    elif 'NSP5' in new_name:
        new_name = 'NSP5'
    elif 'NSP4' in new_name:
        new_name = 'NSP4'
    elif 'NSP3' in new_name:
        new_name = 'NSP3'
    elif 'NSP2' in new_name:
        new_name = 'NSP2'
    elif 'NSP1' in new_name:
        new_name = 'NSP1'
    elif 'NUCLEOCAPSID' in new_name:
        new_name = 'N'
    elif 'ENVELOPE' in new_name:
        new_name = 'E'
    else:
        regex_match = re.match(regex_orf_non_polyprot, new_name)
        if regex_match:
            # replace ORF[2-10]<number><letter> with NS[2-10]<number><letter> in proteins exce
            number, letter = regex_match.groups()[1::3]
            new_name = 'NS' + number + letter
        else:
            # replace substrings in protein name
            for old, new in protein_name_replacements.items():
                new_name = new_name.replace(old, new)
            new_name = new_name.strip()

    # check if standardization has succeeded
    if new_name.startswith('NSP') \
            or new_name.startswith('NS')\
            or new_name in ('S', 'N', 'M', 'E'):
        pass
    elif new_name.startswith('ORF1A') \
            or new_name.startswith('ORF1AB') \
            or new_name.startswith('ORF1B'):

        if start_pos is not None:
            if new_name == 'ORF1AB' or new_name == 'ORF1A':
                if 1 <= start_pos <= 180:
                    new_name = "NSP1"
                elif 181 <= start_pos <= 818:
                    new_start_pos = new_start_pos - 181 + 1
                    new_stop_pos = new_stop_pos - 181 + 1 if new_stop_pos is not None else None
                    new_name = "NSP2"
                elif 819 <= start_pos <= 2763:
                    new_start_pos = new_start_pos - 819 + 1
                    new_stop_pos = new_stop_pos - 819 + 1 if new_stop_pos is not None else None
                    new_name = "NSP3"
                elif 2764 <= start_pos <= 3263:
                    new_start_pos = new_start_pos - 2764 + 1
                    new_stop_pos = new_stop_pos - 2764 + 1 if new_stop_pos is not None else None
                    new_name = "NSP4"
                elif 3264 <= start_pos <= 3569:
                    new_start_pos = new_start_pos - 3264 + 1
                    new_stop_pos = new_stop_pos - 3264 + 1 if new_stop_pos is not None else None
                    new_name = "NSP5"
                elif 3570 <= start_pos <= 3859:
                    new_start_pos = new_start_pos - 3570 + 1
                    new_stop_pos = new_stop_pos - 3570 + 1 if new_stop_pos is not None else None
                    new_name = "NSP6"
                elif 3860 <= start_pos <= 3942:
                    new_start_pos = new_start_pos - 3860 + 1
                    new_stop_pos = new_stop_pos - 3860 + 1 if new_stop_pos is not None else None
                    new_name = "NSP7"
                elif 3943 <= start_pos <= 4140:
                    new_start_pos = new_start_pos - 3943 + 1
                    new_stop_pos = new_stop_pos - 3943 + 1 if new_stop_pos is not None else None
                    new_name = "NSP8"
                elif 4141 <= start_pos <= 4253:
                    new_start_pos = new_start_pos - 4141 + 1
                    new_stop_pos = new_stop_pos - 4141 + 1 if new_stop_pos is not None else None
                    new_name = "NSP9"
                elif 4254 <= start_pos <= 4392:
                    new_start_pos = new_start_pos - 4254 + 1
                    new_stop_pos = new_stop_pos - 4254 + 1 if new_stop_pos is not None else None
                    new_name = "NSP10"
                elif 4393 <= start_pos <= 5324:
                    new_start_pos = new_start_pos - 4393 + 1
                    new_stop_pos = new_stop_pos - 4393 + 1 if new_stop_pos is not None else None
                    new_name = "NSP12"
                elif 5325 <= start_pos <= 5925:
                    new_start_pos = new_start_pos - 5325 + 1
                    new_stop_pos = new_stop_pos - 5325 + 1 if new_stop_pos is not None else None
                    new_name = "NSP13"
                elif 5926 <= start_pos <= 6452:
                    new_start_pos = new_start_pos - 5926 + 1
                    new_stop_pos = new_stop_pos - 5926 + 1 if new_stop_pos is not None else None
                    new_name = "NSP14"
                elif 6453 <= start_pos <= 6798:
                    new_start_pos = new_start_pos - 6453 + 1
                    new_stop_pos = new_stop_pos - 6453 + 1 if new_stop_pos is not None else None
                    new_name = "NSP15"
                elif 6799 <= start_pos <= 7096:
                    new_start_pos = new_start_pos - 6799 + 1
                    new_stop_pos = new_stop_pos - 6799 + 1 if new_stop_pos is not None else None
                    new_name = "NSP16"
                else:
                    logger.warning(
                        f"Attempt to convert protein name {name} to NSPxx failed because the start_pos {start_pos} "
                        f"doesn't resolve to any NSP")
            elif new_name == 'ORF1B':
                if 1 <= start_pos <= 923:  # 1 -> 923
                    new_start_pos = new_start_pos + 9
                    new_stop_pos = new_stop_pos + 9 if new_stop_pos is not None else None
                    new_name = "NSP12"
                elif 924 <= start_pos <= 1524:  # 924 -> 1524
                    new_start_pos = new_start_pos - 924 + 1
                    new_stop_pos = new_stop_pos - 924 + 1 if new_stop_pos is not None else None
                    new_name = "NSP13"
                elif 1525 <= start_pos <= 2051:  # 1525 -> 2051
                    new_start_pos = new_start_pos - 1525 + 1
                    new_stop_pos = new_stop_pos - 1525 + 1 if new_stop_pos is not None else None
                    new_name = "NSP14"
                elif 2052 <= start_pos <= 2397:  # 2052 ->2397
                    new_start_pos = new_start_pos - 2052 + 1
                    new_stop_pos = new_stop_pos - 2052 + 1 if new_stop_pos is not None else None
                    new_name = "NSP15"
                elif 2398 <= start_pos <= 2695:  # 2398 -> 2695
                    new_start_pos = new_start_pos - 2398 + 1
                    new_stop_pos = new_stop_pos - 2398 + 1 if new_stop_pos is not None else None
                    new_name = "NSP16"
                else:
                    logger.warning(
                        f"Attempt to convert protein name {name} to NSPxx failed because the start_pos {start_pos} "
                        f"doesn't resolve to any NSP")
        else:
            logger.error(f"Cannot convert ORF1a/b protein {name} to NSP without at least the starting position of the "
                         "change or annotation")
    else:
        raise ValueError(f"Can't properly treat the protein named {name}.")

    return new_name, new_start_pos, new_stop_pos
    

    
