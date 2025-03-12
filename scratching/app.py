import logging
import sys
import os

# Configure custom logging
LOG_FILE = "odoo_cli.log"
logger = logging.getLogger("odoo_cli")

if not logger.handlers:
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")

    # File Handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Attach handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent duplicate logs
    logger.propagate = False

# 🔹 Suppress Odoo's built-in logging
odoo_logger = logging.getLogger("odoo")
odoo_logger.propagate = False

# 🔹 Clear all root loggers before Odoo initializes
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# 🔹 Override Odoo’s logging system by setting a null handler
logging.basicConfig(level=logging.CRITICAL)  # Blocks all Odoo logs
logging.getLogger().setLevel(logging.CRITICAL)

# Now import Odoo AFTER disabling its logging
import odoo
from odoo.tools import config
from odoo.api import Environment

# Now import Odoo after logging is set up
import odoo
from odoo.tools import config
from odoo.api import Environment

def run(execute, path_to_config="..", commit_changes=False, **kw):
    """Executes a function inside the Odoo environment with logging."""
    current_folder = os.getcwd()
    config_file = f"{path_to_config}/odoo.conf"

    logger.info(f"📂 Current folder: '{current_folder}', using config file: '{config_file}'")

    sys.argv = [sys.argv[0], f'--config={config_file}']

    try:
        # Load Odoo configuration
        config.parse_config(sys.argv[1:])
        odoo.service.server.load_server_wide_modules()

        # Initialize the Odoo registry
        db_name = config['db_name']
        with odoo.registry(db_name).cursor() as cr:
            env = Environment(cr, odoo.SUPERUSER_ID, {})
            logger.info("🔄 Odoo environment initialized")

            logger.debug(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            execute(env, **kw)

            if commit_changes:
                logger.info(f"✅ Database changes committed: commit_changes={commit_changes}")
                env.cr.commit()
            else:
                logger.warning(f"⚠️ No database changes committed: commit_changes={commit_changes}")
            logger.debug("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    except Exception as e:
        logger.critical(f"❌ An error occurred: {e}", exc_info=True)
        sys.exit(1)

    logger.info("🚀 Execution completed successfully.")
    sys.exit(0)
