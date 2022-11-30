import subprocess
import sys

import yaml
from rdflib import Graph

from framework.utils import read_config


class AbstractValidator:
    def __init__(self):
        self.name = None
        self.error_log = None
        self.dictionary = None

    def validate_file(self, input_graph: str, output_graph: str):
        raise NotImplementedError()

    def validate_errors(self):
        raise NotImplementedError()


class ValidatrrValidator:
    def __init__(self, error_log):
        super().__init__()
        self.name = "Validatrr Validator"
        self.error_log = error_log
        self.dictionary = read_config("./framework/languages/rdfcv.yaml")

    def validate_file(self, input_graph: str):
        subprocess.run(
            f"docker run -v {sys.path[0]}:/data n3unit -i /data/{input_graph} -o /data/data/validated.ttl -s foaf",
            shell=True)

    def validate_errors(self):
        # load validated graph
        g = Graph()
        g = g.parse("data/validated.ttl")
        # generate report
        generate_report(self.error_log, self.dictionary, g)


def generate_report(error_log, validation_dict, graph):
    """
    Generates a validation report given the error log, dictionary, and validation graph
    """
    # extract logged dictionary
    logged_errors = error_log.log_dict
    # get total number of detected errors, and total number of introduced errors
    total_error_pattern = validation_dict["total_errors"]["pattern"]
    detected = int(next(iter(graph.query(total_error_pattern)))["count"])
    introduced = len([err for cat in logged_errors for err in logged_errors[cat]])
    matching = 0
    # basic report structure
    report = {
        'errors_detected': [],
        'errors_not_detected': [],
        'categories': {}
    }
    for error_type in logged_errors:
        for error in logged_errors[error_type]:
            if error["category"] not in report["categories"]:
                report["categories"][error["category"]] = {"detected": 0, "total": 1}
            else:
                report["categories"][error["category"]]["total"] += 1
            if error_type not in validation_dict:
                print(f"Undefined error type: {error_type}")
                report["errors_not_detected"].append({error_type: error})
            else:
                query = validation_dict[error_type]["pattern"] \
                    .replace("$subject$", f"<{error['subject']}>") \
                    .replace("$original$", f"<{error['original']}>")
                if len(graph.query(query)) > 0:
                    matching += 1
                    report["categories"][error["category"]]["detected"] += 1
                    report["errors_detected"].append({error_type: error})
                else:
                    report["errors_not_detected"].append({error_type: error})
    report["precision"] = round(matching / detected if detected > 0 else 0, 2)
    report["recall"] = round(matching / introduced, 2)
    if report["precision"] + report["recall"] > 0:
        report["f1"] = round(2 * report["precision"] * report["recall"] / (report["precision"] + report["recall"]), 2)
    else:
        report["f1"] = 0.0
    with open("data/report.yaml", 'w') as outfile:
        yaml.dump(report, outfile, default_flow_style=False)
    print(yaml.dump(report, allow_unicode=True, default_flow_style=False))
