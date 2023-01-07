import subprocess
import sys
import re

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
        generate_approach_report(self.name, self.error_log, self.dictionary, "data/validated.ttl")


class RdfDoctorValidator:
    def __init__(self, error_log):
        super().__init__()
        self.name = "RDF-Doctor Validator"
        self.error_log = error_log
        self.dictionary = read_config("./framework/languages/rdfdoctor.yaml")

    def validate_file(self, input_graph: str):
        subprocess.run(
            f"java -jar {sys.path[0]}/bin/RDFDoctor.jar -i {sys.path[0]}/{input_graph}",
            shell=True, cwd=f"{sys.path[0]}/data")

    def validate_errors(self):
        generate_approach_report(self.name, self.error_log, self.dictionary, "data/output.error")


def generate_approach_report(validator_name, error_log, validation_dict, validation_report_location: str):
    # extract error dictionary from error log
    logged_errors = error_log.log_dict
    # set up basic report structure
    report = {
        'errors_detected': [],
        'errors_not_detected': [],
        'categories': {}
    }
    # get validation report source depending on type
    if validation_dict["type"] == "graph":
        data_source = Graph()
        data_source = data_source.parse(validation_report_location)
        query_function = matching_graph_count
    elif validation_dict["type"] == "regex":
        with open(validation_report_location, 'r') as f:
            data_source = f.read()
        query_function = matching_regex_count
    else:
        print("Skipping approach report generation due to unknown parse type (Valid: graph/regex)")
        return

    # get total number of detected errors, and total number of introduced errors
    total_error_pattern = validation_dict["total_errors"]["pattern"]
    detected = query_function(data_source, total_error_pattern)
    introduced = len([err for cat in logged_errors for err in logged_errors[cat]])
    matching = 0
    explained = 0

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
                error_sum = 0
                for pattern in validation_dict[error_type]["patterns"]:
                    query = prepare_query_statement(pattern, error,
                                                    regex_escape=(validation_dict["type"] == "regex"))
                    error_sum += query_function(data_source, query)

                if error_sum > 0:
                    matching += 1
                    explained += error_sum
                    report["categories"][error["category"]]["detected"] += 1
                    report["errors_detected"].append({error_type: error})
                else:
                    report["errors_not_detected"].append({error_type: error})
    report["_validator_errors"] = detected
    report["_validator"] = validator_name
    report["_explained_errors"] = explained
    report["_avg_errors_per_introduced_corruption"] = round(explained / matching if matching > 0 else 1, 2)
    report["_estimated_unexplained_errors"] = round((detected - explained) / report["_avg_errors_per_introduced_corruption"], 2)
    report["_estimated_precision"] = round(matching / (matching + report["_estimated_unexplained_errors"]) if matching + report["_estimated_unexplained_errors"] > 0 else 0, 2)
    report["_recall"] = round(matching / introduced, 2)
    if report["_estimated_precision"] + report["_recall"] > 0:
        report["_estimated_f1"] = round(2 * report["_estimated_precision"] * report["_recall"] / (report["_estimated_precision"] + report["_recall"]), 2)
    else:
        report["_estimated_f1"] = 0.0
    with open("data/report.yaml", 'w') as outfile:
        yaml.dump(report, outfile, default_flow_style=False)
    print(yaml.dump(report, allow_unicode=True, default_flow_style=False))


def matching_regex_count(content: str, query: str) -> int:
    return len(re.findall(query, content))


def matching_graph_count(graph: Graph, query: str) -> int:
    return len(graph.query(query))


ValidationMethodsDict = {
    "validatrr": ValidatrrValidator,
    "rdfdoctor": RdfDoctorValidator
}


def prepare_query_statement(query: str, error: dict, regex_escape: bool) -> str:
    query = query.replace("$original.subject$", encode_uri(error['original']['s'], regex_escape))
    query = query.replace("$original.property$", encode_uri(error['original']['p'], regex_escape))
    query = query.replace("$original.object$", encode_uri(error['original']['o'], regex_escape))
    query = query.replace("$corrupt.subject$", encode_uri(error['corrupted']['s'], regex_escape))
    query = query.replace("$corrupt.property$", encode_uri(error['corrupted']['p'], regex_escape))
    query = query.replace("$corrupt.object$", encode_uri(error['corrupted']['o'], regex_escape))
    return query


def encode_uri(uri: str, regex_escape: bool):
    return f"<{uri}>" if not regex_escape else re.escape(f"<{uri}>")
