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
        # extract logged dictionary
        log_data = self.error_log.log_dict
        # get total number of detected errors, and total number of introduced errors
        detected = int(next(iter(g.query("""SELECT ?o 
                                WHERE { 
                                :errorCount :count ?o . 
                                }""")))["o"])

        introduced = len([err for subject in log_data for err in log_data[subject]])
        matching = 0
        # write report
        report = {
            'errors_detected': [],
            'errors_not_detected': []
        }

        for subject in log_data:
            for error_type in log_data[subject]:
                if error_type not in self.dictionary:
                    print(f"Undefined error type: {error_type}")
                    report["errors_not_detected"] += [f"{subject} {error_type} (Missing Definition)"]
                else:
                    query = self.dictionary[error_type]["pattern"] \
                        .replace("$o$", f"<{subject}>") \
                        .replace("$old$", f"<{log_data[subject][error_type][0]}>")
                    if len(g.query(query)) > 0:
                        matching += 1
                        report["errors_detected"] += [f"{subject} {error_type}"]
                    else:
                        report["errors_not_detected"] += [f"{subject} {error_type}"]
        report["precision"] = matching / detected if detected > 0 else 0
        report["recall"] = matching / introduced
        if report["precision"] + report["recall"] > 0:
            report["f1"] = 2 * report["precision"] * report["recall"] / (report["precision"] + report["recall"])
        else:
            report["f1"] = 0.0
        with open("report.yaml", 'w') as outfile:
            yaml.dump(report, outfile, default_flow_style=False)
        print(yaml.dump(report, allow_unicode=True, default_flow_style=False))
