import yaml


class Logger():
    def __init__(self):
        self.id = None
        self.name = None
        self.log_dict = {}

    def log_error(self, error_type, error_category, original_triple, corrupted_triple):
        if error_type not in self.log_dict:
            self.log_dict[error_type] = []
        self.log_dict[error_type].append({
            "category": error_category,
            "original": {
                "s": original_triple['s'],
                "p": original_triple['p'],
                "o": original_triple['o']
            }, 
            "corrupted": {
                "s": corrupted_triple['s'],
                "p": corrupted_triple['p'],
                "o": corrupted_triple['o']
            }})

    def save_to_file(self, filepath='data/error_log.yaml'):
        with open(filepath, 'w', encoding='utf8') as outfile:
            yaml.dump(self.log_dict, outfile, default_flow_style=False, allow_unicode=True)

    def __str__(self):
        return (
            yaml.dump(self.log_dict, allow_unicode=True, default_flow_style=False)
        )
