#!/usr/bin/env python

__import__('os').environ['TZ'] = 'UTC'

import os
import odoo
import sys
from pathlib import Path

environment = 'staging'
custom_addons_path="libs/addons/custom-addons"
addons_path = os.path.join(os.getcwd(), custom_addons_path)

os.environ['ODOO_STAGE'] = environment
print("environment ODOO_STAGE:", environment)

assert Path(addons_path).exists()

modules = [os.path.basename(item) for item in Path(addons_path).iterdir() if item.is_dir()]

install_modules = ",".join(modules)
test_modules = "/" + ",/".join(modules)

sys.argv = [sys.argv[0], f'--config=odoo.conf', f'-i {install_modules}', f'-u {test_modules}', '--stop-after-init']

odoo.cli.main()