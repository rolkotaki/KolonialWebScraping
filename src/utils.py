import yaml

from src.settings import CONFIG_FILE


def load_config(config_param):
    """To load a config parameter from the config file.
    Returns a single value or a dictionary.
    """
    with open(CONFIG_FILE) as config_file:
        config = yaml.safe_load(config_file)
    return config[config_param]
