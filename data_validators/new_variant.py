import re
from data_validators.vocabulary import Organization


class Commons:
    class AAChangeNoProt:
        regex = re.compile(r'([A-Z\-]+\d+[A-Z\-]+)|(\d+[A-Z\-]+)|([A-Z\-]+\d+)')


class PangoLineage:
    regex = re.compile(r'[A-Z]{1,2}(\.\d+)+')
    organization = Organization.PANGO
    tests_should_pass = [
        "B.1.1.7", "P.1", "B.1.617.1.2", "AV.1"
    ]
    tests_should_not_pass = []


class PangoLineageWithAlternativePangoLineage:
    regex = re.compile(r'[A-Z]{1,2}(\.\d+)*/[A-Z]{1,2}(\.\d+)*')
    organization = Organization.PANGO
    tests_should_pass = [
        "B.1.427/B.1.429"
    ]
    tests_should_not_pass = []


class GisaidClade:
    regex = re.compile(r'[A-Z]+(/\d+[A-Z\-]\.\w+)?')
    organization = Organization.GISAID
    tests_should_pass = [
        "GH/501Y.V2", "GRY"
    ]
    tests_should_not_pass = []


class PheNameNumericDate:
    regex = re.compile(r'(VOC|VUI)[\-\s]*(\d{4})(\d{2})/(\d{2})')
    organization = Organization.PHE
    tests_should_pass = [
        "VUI-202102/04", "VUI 202102/04", "VUI202102/04", "VUI - 202102/04"
    ]
    tests_should_not_pass = []


class PheNameTextualDate:
    regex = re.compile(r'(VOC|VUI)[\-\s]*(\d{2})([A-Z]{3})-(\d{2})')
    organization = Organization.PHE
    tests_should_pass = [
        "VUI-21MAR-02", "VUI 21MAR-02", "VUI-21MAR-02", "VUI - 21MAR-02"
    ]
    tests_should_not_pass = []


class WhoNames:
    regex = re.compile(r'([Α-Ωα-ω\*])|(Alpha|Beta|Gamma|Delta|Epsilon|Zeta|Eta|Theta|Iota|Kappa|Lambda|Mu|Nu|Xi'
                       r'|Omicron|Pi|Rho|Sigma|Tau|Upsilon|Phi|Chi|Psi|Omega)')
    organization = Organization.WHO
    tests_should_pass = ["Alpha"]
    tests_should_not_pass = []


class NextstrainNames:
    regex = re.compile(r'(2\d[A-Z])|(EU\d)')
    organization = Organization.COVARIANTS
    tests_should_pass = [
        "20A", "EU1", "21A"
    ]
    tests_should_not_pass = []


class NextstrainWithAlternativeNextstrainNames:
    regex = re.compile(r'((2\d[A-Z])|(EU\d))([\./]?[\W]*((2\d[A-Z])|(EU\d))[\W]*)')
    organization = Organization.COVARIANTS
    tests_should_pass = [
        "21A.21B", "21A/21B", "20A.EU1", "20E (EU1)"
    ]
    tests_should_not_pass = ["20A", "EU1", "21A"]


class NextstrainNamesWithChanges:
    regex = re.compile(r'(((2\d[A-Z])|(EU\d))[\./])?[A-Z][\.:]'
                       r'(' + Commons.AAChangeNoProt.regex.pattern + r')')
    organization = Organization.COVARIANTS
    tests_should_pass = [
        "20B/S:732A", "S.N439K", "S.H69-"
    ]
    tests_should_not_pass = ["20G/S:677H.Robin2", "S.Q677H.Robin1", "21A.Delta.S.K417", "21A.Delta", "20I.Alpha.V1",
                             "20I.Alpha.V1", "21A.Delta", "21A.Delta.S.K417"]


class NextstrainNamesWithChangesAndNameAfter:
    # replace original regex with one using Commons.AAChangeNoProt
    # regex = re.compile(r'(((2\d[A-Z])|(EU\d))[\./])?[A-Z][\.:][A-Z\-]*\d+[A-Z\-]*\.\w+')
    regex = re.compile(r'(((2\d[A-Z])|(EU\d))[\./])?[A-Z][\.:]'
                       r'(' + Commons.AAChangeNoProt.regex.pattern + r')'
                       r'\.\w+')
    organization = Organization.COVARIANTS
    tests_should_pass = [
        "S.Q677H.Robin1", "20G/S:677H.Robin2"
    ]
    tests_should_not_pass = ["20B/S:732A", "S.N439K", "S.H69-"]


class NextstrainNamesWithChangesAndWhoNameInBetween:
    # replace original regex with one using Commons.AAChangeNoProt
    # regex = re.compile(
    #     r'(((2\d[A-Z])|(EU\d))[\./])?' + r'(' + WhoNames.regex.pattern + r')' + r'\.[A-Z][\.:][A-Z\-]*\d+[A-Z\-]*')
    regex = re.compile(r'(((2\d[A-Z])|(EU\d))[\./])?'
                       r'(' + WhoNames.regex.pattern + r')'
                       r'\.[A-Z][\.:]'
                       r'(' + Commons.AAChangeNoProt.regex.pattern + r')')
    organization = Organization.COVARIANTS
    tests_should_pass = [
        "21A.Delta.S.K417"
    ]
    tests_should_not_pass = ["20B.S.732A"]


class NextstrainNamesWithWhoNamesNoChanges:
    regex = re.compile(r'((2\d[A-Z])|(EU\d))[\./]'
                       r'(' + WhoNames.regex.pattern + r')'
                       r'(\.\w+)?')
    organization = Organization.COVARIANTS
    tests_should_pass = [
        "20I.Alpha.V1", "21A.Delta"
    ]
    tests_should_not_pass = ["21A.Delta.S.K417", "20I (Alpha, V1)", "21A (Delta)"]


class NextstrainNamesWithWhoNamesNoChangesParenthesized:
    regex = re.compile(r'((2\d[A-Z])|(EU\d))[\s\(]+'
                       r'(' + WhoNames.regex.pattern + r')'
                       r'[\s\),\w]+')
    organization = Organization.COVARIANTS
    tests_should_pass = [
        "20I (Alpha, V1)", "21A (Delta)"
    ]
    tests_should_not_pass = ["20I.Alpha.V1", "21A.Delta"]


class NexstrainNameStartingWithWhoNamePlusChange:
    # regex = re.compile(r'(' + WhoNames.regex.pattern + r')'
    #                    r'[\s\+]+[A-Z][\.:][A-Z\-]*\d+[A-Z\-]*')
    regex = re.compile(r'(' + WhoNames.regex.pattern + r')'
                       r'[\s\+]+[A-Z][\.:]'
                       r'(' + Commons.AAChangeNoProt.regex.pattern + r')')
    organization = Organization.COVARIANTS
    tests_should_pass = [
        "Delta + S:K417"
    ]
    tests_should_not_pass = []


VARIANT_NAME_REGULAR_EXPRESSIONS = [NextstrainNames,
                                    NextstrainWithAlternativeNextstrainNames,
                                    NextstrainNamesWithChanges,
                                    NextstrainNamesWithChangesAndNameAfter,
                                    NextstrainNamesWithChangesAndWhoNameInBetween,
                                    NextstrainNamesWithWhoNamesNoChanges,
                                    NextstrainNamesWithWhoNamesNoChangesParenthesized,
                                    NexstrainNameStartingWithWhoNamePlusChange,
                                    PangoLineage,
                                    PangoLineageWithAlternativePangoLineage,
                                    GisaidClade,
                                    PheNameNumericDate,
                                    PheNameTextualDate,
                                    WhoNames]


def test_regex_of_variant_names():
    experiments = VARIANT_NAME_REGULAR_EXPRESSIONS
    experiments_with_errors = set()
    for i in range(len(experiments)):
        experiment = experiments[i]
        tests_should_pass = experiment.tests_should_pass
        tests_should_not_pass = experiment.tests_should_not_pass
        # generalize tests that should not pass by adding all the should_pass tests of other experiments
        for j in range(len(experiments)):
            if j != i:
                tests_should_not_pass += experiments[j].tests_should_pass
        tests_should_not_pass = sorted(list(set(tests_should_not_pass)))
        regex = experiment.regex
        should_pass_n_passed = []
        should_pass_n_not_passed = []
        should_not_pass_passed = []
        should_not_pass_not_passed = []
        print(f"TESTING: {experiment.__name__} with regex {experiment.regex.pattern}")
        for test in tests_should_pass:
            match = re.fullmatch(regex, test)
            if match:
                should_pass_n_passed.append(test)
            else:
                should_pass_n_not_passed.append(test)
        if tests_should_pass:
            print("tests that should be passed:")
        if should_pass_n_passed:
            print(f"\tpassed {len(should_pass_n_passed)}/{len(tests_should_pass)} {should_pass_n_passed}")
        if should_pass_n_not_passed:
            print(f"\tnot passed {len(should_pass_n_not_passed)}/{len(tests_should_pass)} {should_pass_n_not_passed}")
            experiments_with_errors.add(experiment.__name__)

        for test in tests_should_not_pass:
            match = re.fullmatch(regex, test)
            if match:
                should_not_pass_passed.append(test)
            else:
                should_not_pass_not_passed.append(test)
        if tests_should_not_pass:
            print("tests that should NOT be passed:")
        if should_not_pass_passed:
            print(
                f"\tmistakenly passed {len(should_not_pass_passed)}/{len(tests_should_not_pass)} {should_not_pass_passed}")
            experiments_with_errors.add(experiment.__name__)
        if should_not_pass_not_passed:
            print(
                f"\tcorrectly rejected {len(should_not_pass_not_passed)}/{len(tests_should_not_pass)} {should_not_pass_not_passed}")

    # SUMMARY
    experiment_tests = set()
    for e in experiments:
        experiment_tests.update(e.tests_should_pass)
    print(f"COMPREHENSIVELY TESTED THE REGEXs FOR CASES:\n"
          f"{sorted(list(experiment_tests))}")
    if experiments_with_errors:
        print(f"EXPERIMENTS WITH ERRORS: {sorted(experiments_with_errors)}")
    else:
        print(f"ALL EXPERIMENTS HAD SUCCESS")

    # try this single example
    # matches = re.fullmatch(re.compile(r'[A-Z][\.:][A-Z\-]*\d+[A-Z\-]*'), 'S.K417')
    # print(f"matches {matches is not None}")


def recognize_organization(variant_name_string, fallback: str = None) -> str:
    for test_class in VARIANT_NAME_REGULAR_EXPRESSIONS:
        match = re.fullmatch(test_class.regex, variant_name_string)
        if match:
            return test_class.organization
    if fallback:
        return fallback


if __name__ == '__main__':
    test_regex_of_variant_names()
