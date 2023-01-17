import subprocess
import sys

from evaluation.validators.AbstractValidator import AbstractValidator
from framework.logger import Logger
from framework.utils import read_config
from utils.evaluation_utils import generate_approach_report


class RdfDoctorValidator(AbstractValidator):
    """
    Use the RDF-Doctor .jar file for benchmarking purposes.
    This requires: A running java installation on your system.
    This implementation uses the bin/RDFDoctor.jar file to detect errors.
    See: https://github.com/ahemaid/RDF-Doctor
    """

    name = "RDF-Doctor Validator"
    approach_dictionary = "evaluation/validators/dictionaries/rdf-doctor.yaml"
    # RDF-Doctor will always generate this file, no matter what is specified with -o.
    output_file = "data/output.error"

    def __init__(self, input_graph: str, error_log: Logger) -> None:
        super().__init__(input_graph, error_log)

    def validate_file(self):
        # We run the jar file while assuming an existing java implementation.
        subprocess.run(
            f"java -jar {sys.path[0]}/bin/RDFDoctor.jar -i {sys.path[0]}/{self.input_graph}",
            shell=True, cwd=f"{sys.path[0]}/data")

    def evaluate_errors(self, report_location: str = "data/report.yaml") -> None:
        self.validate_file()
        generate_approach_report(self.name, self.error_log, read_config(self.approach_dictionary), self.output_file,
                                 kgcbf_report_location=report_location)
