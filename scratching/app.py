import os
import sys

import odoo
from odoo.api import Environment
from odoo.tools import config


def run(execute, path_to_config="..", commit_changes=False, **kw):
    # Ensure you specify the correct path to your Odoo configuration file
    current_folder = os.getcwd()
    config_file = f"{path_to_config}/odoo.conf"

    print(f"current folder '{current_folder}': config is at '{config_file}'")

    sys.argv = [sys.argv[0], f'--config={config_file}']

    # Load Odoo configuration
    config.parse_config(sys.argv[1:])
    odoo.service.server.load_server_wide_modules()

    # Initialize the Odoo registry
    db_name = config['db_name']
    with odoo.registry(db_name).cursor() as cr:
        env = Environment(cr, odoo.SUPERUSER_ID, {})
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        execute(env, **kw)
        if commit_changes:
            print(f"Es werden Anpassungen an der Datenbank vorgenommen: commit_changes {commit_changes}")
            env.cr.commit()
        else:
            print(f"\n\n\nEs wurden keine Anpassungen an der Datenbank vorgenommen: commit_changes {commit_changes}")
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    sys.exit(0)
