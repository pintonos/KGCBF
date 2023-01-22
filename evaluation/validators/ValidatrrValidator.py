import subprocess
import sys

from evaluation.report import Report
from evaluation.validators.AbstractValidator import AbstractValidator
from corruption.logger import Logger
from utils.rdf_utils import read_config


class ValidatrrValidator(AbstractValidator):
    """
    Use Validatrr in a Docker container for benchmarking purposes.
    This requires: Validatrr available in a Docker image called n3unit.
    See: https://github.com/IDLabResearch/validatrr
    """

    name = "Validatrr Validator"
    approach_dictionary = "evaluation/validators/dictionaries/rdfcv.yaml"
    output_file = "data/approach_report.ttl"

    def __init__(self, input_graph: str, error_log: Logger) -> None:
        super().__init__(input_graph, error_log)

    def validate_file(self):
        # We run the docker container and virtualize our working directory to /data on the VM
        # This way we can pass the input/output files as if we were running Validatrr on our own system.
        subprocess.run(
            f"docker run -v {sys.path[0]}:/data n3unit -i /data/{self.input_graph} -o /data/{self.output_file}",
            shell=True)

    def evaluate_errors(self, report_location: str = "data/report.yaml") -> Report:
        self.validate_file()
        # generate a report
        report = Report(self.name, self.error_log, read_config(self.approach_dictionary), self.output_file)
        report.store_report(report_location)
        return report
