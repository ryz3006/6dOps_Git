from configparser import ConfigParser
import os
from custom_logger import setup_logger

# Set up logger for your script
logger = setup_logger(__name__)

def read_config():
    config_file_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'config.txt')
    
    parser = ConfigParser()
    parser.read(config_file_path)

    config_dict = {}
    for section in parser.sections():
        for key, value in parser.items(section):
            # Store the keys in lowercase
            config_dict[key.lower()] = value

    return config_dict