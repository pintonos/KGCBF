import subprocess

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
        subprocess.run("docker run -v \"%cd%\":/data n3unit" + f" -i /data/{input_graph} -o /data/validated.ttl -s foaf",
                       shell=True)

    def validate_errors(self):
        # load validated graph
        g = Graph()
        g = g.parse("validated.ttl")
        log_data = self.error_log.log_dict
        for subject in log_data:
            for error_type in log_data[subject]:
                if error_type not in self.dictionary:
                    print(f"Unknown error type: {error_type}")
                else:
                    query = self.dictionary[error_type]["pattern"]\
                        .replace("$o$", f"<{subject}>")\
                        .replace("$old$", f"<{log_data[subject][error_type][0]}>")
                    if len(g.query(query)) > 0:
                        print(f"Error detected: {error_type} {subject}")
                    else:
                        print(f"Error not detected: {error_type} {subject}")