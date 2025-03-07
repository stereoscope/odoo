import os
import sys

import odoo
from odoo.api import Environment
from odoo.tools import config


def start_odoo(path_to_config=".."):
    global env  # Keep the environment accessible for later cells

    # Ensure you specify the correct path to your Odoo configuration file
    current_folder = os.getcwd()
    config_file = f"{path_to_config}/odoo.conf"

    print(f"Current folder '{current_folder}': config is at '{config_file}'")

    sys.argv = [sys.argv[0], f'--config={config_file}']

    # Load Odoo configuration
    config.parse_config(sys.argv[1:])
    odoo.service.server.load_server_wide_modules()

    # Initialize the Odoo registry
    db_name = config['db_name']
    registry = odoo.registry(db_name)

    # Open a cursor and set up the environment
    cr = registry.cursor()
    env = Environment(cr, odoo.SUPERUSER_ID, {})

    print("Odoo environment initialized. You can now run queries in separate cells.")
    return env

def shutdown_odoo():
    sys.exit(0)