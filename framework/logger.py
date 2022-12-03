import yaml


class Logger():
    def __init__(self):
        self.id = None
        self.name = None
        self.log_dict = {}

    def log_error(self, error_type, subject, original_val, corrupted_val, error_category):
        if error_type not in self.log_dict:
            self.log_dict[error_type] = []
        self.log_dict[error_type].append({"subject": subject, "original": original_val, "corrupted": corrupted_val,
                                          "category": error_category})

    def save_to_file(self, filepath='data/error_log.yaml'):
        with open(filepath, 'w', encoding='utf8') as outfile:
            yaml.dump(self.log_dict, outfile, default_flow_style=False, allow_unicode=True)

    def __str__(self):
        return (
            yaml.dump(self.log_dict, allow_unicode=True, default_flow_style=False)
        )
