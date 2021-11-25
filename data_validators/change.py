import re
import warnings
from data_validators.vocabulary import ChangeType
import db_config.mongodb_model as db_schema
from typing import Iterable, Union

capital_letters = re.compile(r'[A-Z]*')


class Change:
    """
    Container class for fields: ref, pos, alt. Makes ref and alt both uppercase and changes 'DEL' to symbol '-'.
    """
    def __init__(self, ref: str, pos: int, alt: str):
        self.ref: str = ref
        self.pos: int = pos
        self.alt: str = alt
        self.optional: bool = False
        self.uniform()
        self.length = max(len(self.alt), len(self.ref))
        if '-' in self.alt or len(self.ref) > len(self.alt):
            self._type = ChangeType.DEL
        elif '' == self.ref or len(self.ref) < len(self.alt):
            self._type = ChangeType.INS
        else:
            self._type = ChangeType.SUB

    # shared objects
    ref_regex = re.compile(r'[a-zA-Z\-\*]*')
    alt_regex = re.compile(r'[a-zA-Z\-\*]+')
    pos_regex = re.compile(r'[\d/]+')
    ref_pos_alt_regex = re.compile(r'([a-zA-Z\-\*]*)([\d/]+)([a-zA-Z\-\*]+)')

    @staticmethod
    def from_parts(ref: str, pos: Union[int, str], alt: str) -> Iterable:
        """
        Checks that ref, pos and alt represent a change (syntactic checks) and returns one or more corresponding
        Change objects.
        """
        ref = ref.strip()
        try:
            pos.strip()
        except AttributeError:
            pos = str(pos)
        alt = alt.strip()
        match = Change.ref_regex.fullmatch(ref)
        if not match:
            raise ValueError(
                f"Reference string of change {ref}{pos}{alt} is not recognized as a valid input. Recognized inputs "
                f"match with the regex {str(Change.ref_regex.pattern)}")
        match = Change.pos_regex.fullmatch(pos)
        if not match:
            raise ValueError(
                f"Position of change {ref}{pos}{alt} is not recognized as a valid input. Recognized inputs "
                f"match with the regex {str(Change.pos_regex.pattern)}")
        match = Change.alt_regex.fullmatch(alt)
        if not match:
            raise ValueError(
                f"Alternative string of change {ref}{pos}{alt} is not recognized as a valid input. Recognized inputs "
                f"match with the regex {str(Change.alt_regex.pattern)}")
        if '/' in pos:  # split concatenated mutations (usually they are close by changes, e.g. AT69/70- ==> AT69-)
            pos, _ = pos.split('/')
        yield Change(ref, int(pos), alt)

    @staticmethod
    def from_string(input_string: str) -> Iterable:
        """
        Parses the change encoded as input_string and returns one or more corresponding Change objects.
        """
        # the regex matches strings like <ref><pos><alt> where
        # <ref> can be none or a combination of letters and "-"
        # <pos> can be one or more numbers separated by a forward slash
        # <alt> can be a combination of letters and "-"

        # split string into ref - pos - alt
        match = Change.ref_pos_alt_regex.fullmatch(input_string)
        if not match:
            raise ValueError(
                f"Input change {input_string} is not recognized as a valid change. Recognized NUC/AA changes "
                f"match the regex {str(Change.ref_pos_alt_regex.pattern)}")
        ref, pos, alt = match.group(1, 2, 3)

        if '/' in pos:  # split concatenated mutations (usually they are close by changes, e.g. AT69/70- ==> AT69-)
            pos, _ = pos.split('/')
        yield Change(ref, int(pos), alt)

    def uniform(self):
        self.ref = self.ref.upper()
        # e.g. -10T (insertion of T) ==> 10T
        if self.ref == '-':
            self.ref = ''
        self.alt = self.alt.upper()
        # e.g. A11DEL (deletion of A) ==> A11-
        if self.alt == 'DEL':
            self.alt = '-'

    def set_optional(self):
        self.optional = True

    def get_encoded_string(self):
        return self.ref + str(self.pos) + self.alt

    def to_db_obj(self) -> db_schema.NUCChange:
        return db_schema.NUCChange(
            self.get_encoded_string(),
            self.ref,
            self.pos,
            self.alt,
            self._type,
            self.length,
            is_opt=self.optional
        )


class AAChange:
    """
    Extends curation of container class "Change" by
    - saving also protein name (and making it uppercase).
    - translating AA residue names to single-letter codes;
    - translating STOP to symbol '*'
    - translating ORF1a/b proteins and change position with respect to included non-structural proteins.
    """
    def __init__(self, protein: str, change: Change):
        self.protein: str = protein
        self.ref: str = change.ref
        self.pos: int = change.pos
        self.alt: str = change.alt
        self.optional: bool = change.optional
        self.uniform()
        self.length = max(len(self.alt), len(self.ref))
        if '-' in self.alt or len(self.ref) > len(self.alt):
            self._type = ChangeType.DEL
        elif '' == self.ref or len(self.ref) < len(self.alt):
            self._type = ChangeType.INS
        else:
            self._type = ChangeType.SUB

    # map for translating AA residue names and special values (e.g. 'STOP') to single letter codes or symbols.
    # noinspection SpellCheckingInspection
    long_residues_map = {
        'ALANINE': 'A',
        'ARGININE': 'R',
        'ASPARGINE': 'N',
        'ASPARTIC': 'D',
        'CYSTEINE': 'C',
        'GLUTAMINE': 'Q',
        'GLUTAMIC': 'E',
        'GLYCINE': 'G',
        'HISTIDINE': 'H',
        'ISOLEUCINE': 'I',
        'LEUCINE': 'L',
        'LYSINE': 'K',
        'METHIONINE': 'M',
        'PHENYLALANINE': 'F',
        'PROLINE': 'P',
        'SERINE': 'S',
        'THREONINE': 'T',
        'TRYPTOPHAN': 'W',
        'TYROSINE': 'Y',
        'VALINE': 'V',
        'UNSPECIFIED': 'X',
        'UNKNOWN': 'X'
    }
    short_residues_map = {
        'ALA': 'A',
        'ARG': 'R',
        'ASN': 'N',
        'ASP': 'D',
        'CYS': 'C',
        'GLN': 'Q',
        'GLU': 'E',
        'GLY': 'G',
        'HIS': 'H',
        'ILE': 'I',
        'LEU': 'L',
        'LYS': 'K',
        'MET': 'M',
        'PHE': 'F',
        'PRO': 'P',
        'SER': 'S',
        'THR': 'T',
        'TRP': 'W',
        'TYR': 'Y',
        'VAL': 'V',
        'XAA': 'X'
    }
    special_residues_map = {
        'STOP': '*'
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
    @staticmethod
    def entail_short_protein_name(name: str):
        if 'SPIKE' in name:
            return 'S'
        elif 'NSP12' in name:
            return 'NSP12'
        elif 'NUCLEOCAPSID' in name:
            return 'N'
        elif 'NS3' in name:
            return 'NS3'
        elif 'NS8' in name:
            return 'NS8'
        elif 'ENVELOPE' in name:
            return 'E'
        else:
            raise KeyError

    @staticmethod
    def from_parts(protein: str, ref: str, pos: Union[int, str], alt: str) -> Iterable:
        """
        Checks that ref, pos and alt represent a change (syntactic checks) and returns one or more corresponding
        AAChange objects.
        """
        for change in Change.from_parts(ref, pos, alt):
            yield AAChange(protein, change)

    @staticmethod
    def from_string(input_string: str) -> Iterable:
        """
        Parses the change encoded as input_string and returns one or more corresponding AAChange objects.
        """
        protein, changes_str = input_string.split(":")
        for change in Change.from_string(changes_str):
            yield AAChange(protein, change)

    def uniform(self):
        self.protein = self.protein.upper()
        # convert protein names
        try:
            self.protein = self.entail_short_protein_name(self.protein)
        except KeyError:
            for old, new in AAChange.protein_name_replacements.items():
                self.protein = self.protein.replace(old, new)
            self.protein = self.protein.strip()

        # map ORF1A/B to sub-proteins
        if self.protein == 'ORF1AB' or self.protein == 'ORF1A':
            if 1 <= self.pos <= 180:
                self.protein = "NSP1"
            elif 181 <= self.pos <= 818:
                self.pos = self.pos - 181 + 1
                self.protein = "NSP2"
            elif 819 <= self.pos <= 2763:
                self.pos = self.pos - 819 + 1
                self.protein = "NSP3"
            elif 2764 <= self.pos <= 3263:
                self.pos = self.pos - 2764 + 1
                self.protein = "NSP4"
            elif 3264 <= self.pos <= 3569:
                self.pos = self.pos - 3264 + 1
                self.protein = "NSP5"
            elif 3570 <= self.pos <= 3859:
                self.pos = self.pos - 3570 + 1
                self.protein = "NSP6"
            elif 3860 <= self.pos <= 3942:
                self.pos = self.pos - 3860 + 1
                self.protein = "NSP7"
            elif 3943 <= self.pos <= 4140:
                self.pos = self.pos - 3943 + 1
                self.protein = "NSP8"
            elif 4141 <= self.pos <= 4253:
                self.pos = self.pos - 4141 + 1
                self.protein = "NSP9"
            elif 4254 <= self.pos <= 4392:
                self.pos = self.pos - 4254 + 1
                self.protein = "NSP10"
            elif 4393 <= self.pos <= 5324:
                self.pos = self.pos - 4393 + 1
                self.protein = "NSP12"
            elif 5325 <= self.pos <= 5925:
                self.pos = self.pos - 5325 + 1
                self.protein = "NSP13"
            elif 5926 <= self.pos <= 6452:
                self.pos = self.pos - 5926 + 1
                self.protein = "NSP14"
            elif 6453 <= self.pos <= 6798:
                self.pos = self.pos - 6453 + 1
                self.protein = "NSP15"
            elif 6799 <= self.pos <= 7096:
                self.pos = self.pos - 6799 + 1
                self.protein = "NSP16"
            else:
                warnings.warn(f"AA change with protein {self.protein} and pos {self.pos} doesn't resolve to any NSP")
        elif self.protein == 'ORF1B':
            if 1 <= self.pos <= 923:  # 1 -> 923
                self.pos = self.pos + 9
                self.protein = "NSP12"
            elif 924 <= self.pos <= 1524:  # 924 -> 1524
                self.pos = self.pos - 924 + 1
                self.protein = "NSP13"
            elif 1525 <= self.pos <= 2051:  # 1525 -> 2051
                self.pos = self.pos - 1525 + 1
                self.protein = "NSP14"
            elif 2052 <= self.pos <= 2397:  # 2052 ->2397
                self.pos = self.pos - 2052 + 1
                self.protein = "NSP15"
            elif 2398 <= self.pos <= 2695:  # 2398 -> 2695
                self.pos = self.pos - 2398 + 1
                self.protein = "NSP16"
            else:
                warnings.warn(f"AA change with protein {self.protein} and pos {self.pos} doesn't resolve to any NSP")

        # substitute special characters in residues' names (e.g. STOP => '*')
        for old, new in self.long_residues_map.items():
            self.ref = self.ref.replace(old, new)
            self.alt = self.alt.replace(old, new)

        # substitute all occurrences of long residues' names
        # BEWARE to do this before replacing short names or the translation might be wrong!
        original_len = len(self.ref) + len(self.alt)
        for old, new in self.long_residues_map.items():
            self.ref = self.ref.replace(old, new)
            self.alt = self.alt.replace(old, new)

        # substitute all occurrences of short residues' names
        # BEWARE to do this only if there are not long residues names or the translation might be wrong!
        if not len(self.ref) + len(self.alt) < original_len:
            for old, new in self.short_residues_map.items():
                self.ref = self.ref.replace(old, new)
                self.alt = self.alt.replace(old, new)

    def set_optional(self):
        self.optional = True

    def get_encoded_string(self):
        return self.protein + ":" + self.ref + str(self.pos) + self.alt

    def to_db_obj(self) -> db_schema.AAChange:
        return db_schema.AAChange(
            self.get_encoded_string(),
            self.protein,
            self.ref,
            self.pos,
            self.alt,
            self._type,
            self.length,
            is_opt=self.optional
        )
