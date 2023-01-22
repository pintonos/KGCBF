import sys

import yaml
from rdflib import Graph

from corruption.logger import Logger
from utils.evaluation_utils import matching_graph_count, matching_regex_count, fill_approach_dictionary_placeholders


class Report:
    def __init__(self, validator_name: str, error_log: Logger, approach_dictionary: dict, output_file: str) -> None:
        """
        This class generates a report for a given validator and error log.
        @param validator_name: The name of the validator.
        @param error_log: The error log of the validator.
        @param approach_dictionary: The approach dictionary of the validator.
        @param output_file: The output file of the validator.
        """
        self.error_log = error_log.log_dict
        self.validator_name = validator_name
        self.approach_dictionary = approach_dictionary
        self.output_file = output_file
        # setup basic report structure
        self.detected_errors = []
        self.undetected_errors = []
        categories = set([error["category"] for error_type in self.error_log for error in self.error_log[error_type]])
        self.categories = {category: {"detected": 0, "total": 0} for category in categories}
        self.matching = 0
        # number of errors reported by the validation approach that are related to an introduced corruption.
        self.explained = 0
        # number of errors reported by the validation approach
        self.detected = 0
        self.introduced = 0
        # On average, how many errors (in the validation approach) does one corruption cause.
        self.errors_per_corruption = 0
        # From the average errors per corruption, estimate how many "true" unexplained errors there are.
        self.estimated_unexplained_corruptions = 0
        # From the estimated number of unexplained errors, estimate precision (How many detected errors are corruptions)
        self.estimated_precision = 0
        # True recall (how many introduced corruptions can we detect).
        self.recall = 0
        # Estimated F1 based on true recall and estimated precision.
        self.estimated_f1 = 0

        # Calculate report measures.
        self.__generate_approach_report()

    def __generate_approach_report(self) -> None:
        """
        This method is called automatically by the constructor and generates KGCBF report information according to the
        parameters given to the constructor.
        """
        # get validation report source depending on type
        if "type" not in self.approach_dictionary:
            print(f"The provided validation dictionary for the validator {self.validator_name} does not contain a "
                  f"\"type\" property. Please provide one. (Valid: graph,regex)")
            sys.exit(1)
        if self.approach_dictionary["type"] == "graph":
            # if the output type is a graph, we parse the approach report to a rdflib graph.
            data_source = Graph()
            data_source = data_source.parse(self.output_file)
            # To find errors, we use "matching_graph_count" (SPARQL queries)
            query_function = matching_graph_count
        elif self.approach_dictionary["type"] == "regex":
            # if the output type is regex, we read the approach report as a file.
            with open(self.output_file, 'r') as f:
                data_source = f.read()
            # To find errors, we use "matching_regex_count" (regex queries)
            query_function = matching_regex_count
        else:
            # If the output type is not matching, we do not generate a KGCBF report.
            print(f"Skipping KGCBF report generation due to "
                  f"unknown parse type \"{self.approach_dictionary['type']}\" (Valid: graph,regex)")
            sys.exit(1)

        # get total number of detected errors, and total number of introduced errors
        # For this, we use a predefined pattern from the dictionary which appears once for every error.
        self.detected = query_function(data_source, self.approach_dictionary["total_errors"]["pattern"])
        self.introduced = len([err for cat in self.error_log for err in self.error_log[cat]])

        # Next, we iterate over the error log to find all explainable errors.
        for error_type in self.error_log:
            for error in self.error_log[error_type]:
                # Add the error we just iterated over.
                self.categories[error["category"]]["total"] += 1
                # Check if our approach dictionary has a pattern for this error type. If not, count it as not detected.
                if error_type not in self.approach_dictionary:
                    self.undetected_errors.append({error_type: error})
                else:
                    # For each error we can provide several patterns (e.g., if one corruption can cause several errors).
                    # We iterate over those patterns and find the total number of detected instances in the approach
                    # report.
                    error_sum = 0
                    for pattern in self.approach_dictionary[error_type]["patterns"]:
                        query = fill_approach_dictionary_placeholders(pattern, error,
                                                                      regex_escape=(self.approach_dictionary["type"] == "regex"))
                        error_sum += query_function(data_source, query)
                    # If we found at least one matching pattern, we count one instance of an error "matching" a
                    # corruption. Additionally, we can "explain" the corresponding number of errors.
                    # We also add a "detected" count to the category, and add the error instance to the detected errors.
                    if error_sum > 0:
                        self.matching += 1
                        self.explained += error_sum
                        self.categories[error["category"]]["detected"] += 1
                        self.detected_errors.append({error_type: error})
                    else:
                        # Otherwise we add the error instance to the undetected errors.
                        self.undetected_errors.append({error_type: error})

        # calculate metrics.
        self.errors_per_corruption = round(self.explained / self.matching if self.matching > 0 else 1, 2)
        self.estimated_unexplained_corruptions = round(
            (self.detected - self.explained) / self.errors_per_corruption, 2)
        self.estimated_precision = round(
            self.matching / (self.matching + self.estimated_unexplained_corruptions)
            if self.matching + self.estimated_unexplained_corruptions > 0 else 0, 2)
        self.recall = round(self.matching / self.introduced, 2)
        # Estimated F1 based on true recall and estimated precision.
        if self.estimated_precision + self.recall > 0:
            self.estimated_f1 = round(2 * self.estimated_precision * self.recall / (
                    self.estimated_precision + self.recall), 2)
        else:
            self.estimated_f1 = 0.0

    def store_report(self, report_file: str = "data/report.yaml") -> None:
        """
        This method stores the KGCBF report to a file.
        :param report_file: The path to the report file. (Default: data/report.yaml)
        """
        # Write to the report location, and also print the report to the console.
        with open(report_file, 'w') as outfile:
            yaml.dump({
                "_validator": self.validator_name,
                "_detected": self.detected,
                "_introduced": self.introduced,
                "_matching": self.matching,
                "_explained": self.explained,
                "_avg_errors_per_introduced_corruption": self.errors_per_corruption,
                "_estimated_unexplained_corruptions": self.estimated_unexplained_corruptions,
                "_estimated_precision": self.estimated_precision,
                "_recall": self.recall,
                "_estimated_f1": self.estimated_f1,
                "categories": self.categories,
                "detected_errors": self.detected_errors,
                "undetected_errors": self.undetected_errors
            }, outfile, default_flow_style=False)

    def __str__(self) -> str:
        base_str = f"==================KGCBF Report for {self.validator_name}==================\n" \
                   f"Introduced corruptions: {self.introduced} ({self.matching} detected)\n" \
                   f"{self.validator_name} detected {self.detected} errors ({self.explained} explained by introduced " \
                   f"corruptions)\n" \
                   f"Recall: {self.recall}\n" \
                   f"Estimated precision: {self.estimated_precision} (based on an estimated {self.errors_per_corruption} " \
                   f"errors per introduced corruption)\n" \
                   f"Estimated F1: {self.estimated_f1} (based on estimated precision and true recall)\n" \
                   f"Per-category error detection breakdown:\n"
        for category in self.categories:
            base_str += f"\t{category}: {self.categories[category]['detected']}/{self.categories[category]['total']} " \
                        f"detected\n"
        base_str += "For a more detailed breakdown of detected and undetected errors, please create and refer to the" \
                    " report file."
        return base_str
