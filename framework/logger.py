import yaml


class Logger():
    def __init__(self):
        self.id = None
        self.name = None
        self.log_dict = {}

    def log_error(self, error_type, subject, original_val, corrupted_val):
        self.log_dict[subject] = {error_type: [original_val, corrupted_val]}

    def save_to_file(self, filepath='data/error_log.yaml'):
        with open(filepath, 'w') as outfile:
            yaml.dump(self.log_dict, outfile, default_flow_style=False)

    def __str__(self):
        return (
            yaml.dump(self.log_dict, allow_unicode=True, default_flow_style=False)
        )
