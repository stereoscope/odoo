#!/usr/bin/env python3
import argparse
import shutil

import logging
import sys
import subprocess
import os
from getpass import getpass

# Ensure dependencies are installed
REQUIRED_PACKAGES = ["tabulate"]

def ensure_dependencies():
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            print(f"⚠️ Missing package '{pkg}', installing it now...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

ensure_dependencies()
from tabulate import tabulate

# ------------------------------------------------------------------------------
# Suppress Odoo's built-in logging
# ------------------------------------------------------------------------------
odoo_logger = logging.getLogger("odoo")
odoo_logger.propagate = False

# Clear all root loggers before Odoo initializes
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Override Odoo’s logging system by setting a null handler
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)

# Now import Odoo AFTER disabling its logging
import odoo
from odoo.tools import config
from odoo.api import Environment

# ------------------------------------------------------------------------------
# Configure CLI logging
# ------------------------------------------------------------------------------
LOG_FILE = "odoo_cli.log"
logger = logging.getLogger("odoo_cli")

if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

logger.info("✅ Logging system initialized.")

# ------------------------------------------------------------------------------
# Database Restorer
# ------------------------------------------------------------------------------
class DatabaseRestorer:
    def __init__(self, dump_file, pg_user=None, db_name="odoo", db_user="odoo", db_pass="odoo"):
        self.dump_file = dump_file
        self.pg_user = pg_user or os.getenv('PGUSER') or getpass.getuser()
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.tmp_backup = f"/tmp/{os.path.basename(dump_file)}"

    def check_psql_installed(self):
        """Check if PostgreSQL's psql command is available."""
        try:
            subprocess.run(["psql", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("✅ psql is installed.")
        except FileNotFoundError:
            logger.critical("❌ psql is not installed. Please install PostgreSQL and try again.")
            sys.exit(1)

    def run_command(self, command, capture_output=False, suppress_output=True):
        """
        Execute a shell command and handle errors, suppressing stdout/stderr if needed.
        Returns command stdout if capture_output=True, otherwise None.
        """
        try:
            logger.debug(f"Executing: {command}")

            stdout_dest = (
                subprocess.PIPE if capture_output
                else (open(os.devnull, "w") if suppress_output else sys.stdout)
            )
            stderr_dest = (
                subprocess.PIPE if capture_output
                else (open(os.devnull, "w") if suppress_output else sys.stderr)
            )

            result = subprocess.run(
                command, shell=True, check=True, text=True,
                stdout=stdout_dest, stderr=stderr_dest
            )

            return result.stdout if capture_output else None

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error executing command: {command}")
            logger.error(f"🔻 Error details: {e.stderr if e.stderr else str(e)}")
            sys.exit(1)

    def database_exists(self):
        """
        Checks if self.db_name exists in the PostgreSQL server under self.pg_user.
        Returns True if found, False otherwise.
        """
        query = f"SELECT 1 FROM pg_database WHERE datname = '{self.db_name}'"
        result = self.run_command(
            f"psql -U {self.pg_user} -tAc \"{query}\"",
            capture_output=True
        )
        return (result or "").strip() == "1"

    def restore(self):
        """
        Restore the database from the given dump file:
         - copy dump to /tmp
         - drop DB/role if exists
         - create DB/role
         - import
         - fix web.base.url
         - configure mailhog
        """
        self.check_psql_installed()
        logger.info(f"⚙️ Using database name: {self.db_name}")

        db_exists = self.database_exists()
        logger.info(f"🔎 Database '{self.db_name}' exists? {db_exists}")

        logger.info("📂 Copying backup file to temporary location...")
        shutil.copy(self.dump_file, self.tmp_backup)

        logger.info("💣 Dropping existing database and role (if any)...")
        self.run_command(f"psql -U {self.pg_user} -c 'DROP DATABASE IF EXISTS {self.db_name};'")
        self.run_command(f"psql -U {self.pg_user} -c 'DROP ROLE IF EXISTS {self.db_user};'")

        logger.info("🛠️ Creating new database and role...")
        self.run_command(f"psql -U {self.pg_user} -c 'CREATE DATABASE {self.db_name};'")
        self.run_command(f"psql -U {self.pg_user} -c \"CREATE ROLE {self.db_user} WITH LOGIN PASSWORD '{self.db_pass}';\"")
        self.run_command(f"psql -U {self.pg_user} -c 'GRANT ALL PRIVILEGES ON DATABASE {self.db_name} TO {self.db_user};'")

        logger.info("📥 Restoring the database from the backup file...")
        self.run_command(f"psql -U {self.pg_user} -d {self.db_name} -f {self.tmp_backup}")

        logger.info("🧹 Cleaning up the temporary backup file...")
        os.remove(self.tmp_backup)

        logger.info("🔗 Updating web.base.url to 'http://localhost:8069'...")
        self.run_command(
            f"psql -U {self.pg_user} -d {self.db_name} -c \"UPDATE ir_config_parameter SET value = 'http://localhost:8069' WHERE key = 'web.base.url'\""
        )

        logger.info("📧 Setting up outgoing mailserver configuration for Mailhog...")
        mailhog_sql = """
        INSERT INTO public.ir_mail_server 
        (id, smtp_port, sequence, create_uid, write_uid, name, from_filter, smtp_host, smtp_authentication, smtp_user, smtp_pass, smtp_encryption, smtp_debug, active, create_date, write_date, smtp_ssl_certificate, smtp_ssl_private_key) 
        VALUES (1, 1025, 10, 7, 7, 'Mailhog', NULL, 'localhost', 'login', NULL, NULL, 'none', false, true, '2024-07-11 08:06:45.160085', '2024-07-11 08:06:45.160085', NULL, NULL) 
        ON CONFLICT (id) DO NOTHING;
        """
        self.run_command(f"psql -U {self.pg_user} -d {self.db_name} -c \"{mailhog_sql}\"")

        def setup(env):
            payment_methods = env["pos.payment.method"].search([('six_terminal_ip', '!=', None)])
            pos_configs = env["pos.config"].search([])

            logger.info("🧹 Disabling up the pos payment methods...")
            for method in payment_methods:
                method.six_terminal_ip = "127.0.0.1"

            logger.info("🧹 Disabling the pos printers...")
            for pos_config in pos_configs:
                pos_config.epson_printer_ip = "127.0.0.1"
                pos_config.other_devices = False

        run(setup, path_to_config = ".", commit_changes=True)

        logger.info("✅ Database restoration complete.")


# ------------------------------------------------------------------------------
# Module Manager
# ------------------------------------------------------------------------------
class ModuleManager:
    """
    Manages Odoo modules (install, uninstall, update, list).
    """
    def __init__(self, env):
        self.env = env

    def update_modules(self, module_names):
        """Aktualisiere Modul"""

        mod_ids = []
        for module_name in module_names:
            mod_id = self.odoo.env['ir.module.module'].search([('name', '=', module_name), ('state', '=', 'installed')])
            if not mod_ids:
                logger.error(f"❌ Module '{module_name}' not found or not installed.")
                continue
            mod_ids += mod_id

        self.odoo.env['ir.module.module'].button_upgrade(mod_ids)
        self.odoo.env['base.module.upgrade'].upgrade_module([])
        return True

    def uninstall_modules(self, module_names):
        """Uninstall multiple Odoo modules."""
        for module_name in module_names:
            logger.info(f"🚀 Uninstalling module: {module_name}")
            mod_ids = self.env['ir.module.module'].search([
                ('name', '=', module_name), ('state', '=', 'installed')
            ])
            if not mod_ids:
                logger.error(f"❌ Module '{module_name}' not found or not installed.")
                continue

            mod_ids.button_uninstall()
            self.env.cr.commit()
            logger.info(f"✅ Module '{module_name}' successfully uninstalled.")

    def install_modules(self, module_names):
        """Install multiple Odoo modules."""
        for module_name in module_names:
            logger.info(f"🚀 Installing module: {module_name}")
            mod_ids = self.env['ir.module.module'].search([('name', '=', module_name)])
            if not mod_ids:
                logger.error(f"❌ Module '{module_name}' not found.")
                continue

            mod_ids.button_install()
            self.env.cr.commit()
            logger.info(f"✅ Module '{module_name}' successfully installed.")

    def update_modules(self, module_names):
        """Update multiple Odoo modules."""
        for module_name in module_names:
            logger.info(f"🚀 Updating module: {module_name}")
            mod_ids = self.env['ir.module.module'].search([
                ('name', '=', module_name), ('state', '=', 'installed')
            ])
            if not mod_ids:
                logger.error(f"❌ Module '{module_name}' not found or not installed.")
                continue

            mod_ids.button_upgrade()
            self.env.cr.commit()
            logger.info(f"✅ Module '{module_name}' successfully updated.")

    def list_modules(self, installed_only=False):
        """List Odoo modules with details."""
        logger.info("📋 Fetching Odoo module list...")

        domain = [('state', '=', 'installed')] if installed_only else []
        modules = self.env['ir.module.module'].search(domain)

        if not modules:
            logger.warning("⚠️ No modules found.")
            return

        self.print_module_data(modules)

    def print_module_data(self, modules):
        table_headers = [
            "Name",
            "Description",
            "State",
            "Author",
            "Installed Version",
            "Latest Version",
            "Published Version"
        ]

        module_data = []
        for module in modules:
            module_data.append(
                [
                    module.name,
                    module.shortdesc,
                    module.state,
                    module.author,
                    module.installed_version,
                    module.latest_version,
                    module.published_version or "N/A",
                ]
            )

        print(tabulate(module_data, headers=table_headers, tablefmt="fancy_grid"))
        print("""
        installed_version -> The version in the database
        latest_version    -> The version on disk
        published_version -> The version on the repository
        """)

    def show_module(self, module_name):
        """Show information about a single Odoo module."""
        logger.info(f"🚀 Showing module: {module_name}")
        modules = self.env['ir.module.module'].search([('name', '=', module_name)])
        if not modules:
            logger.error(f"❌ Module '{module_name}' not found.")
            return False

        self.print_module_data(modules)
        logger.info(f"✅ Module '{module_name}' information displayed.")
        return True

# ------------------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------------------
def modify_user(env, args):
    """
    Modify user password and optionally disable 2FA.
    """
    logger.info(f"🔍 Searching for user matching '{args.username}'...")
    users = env['res.users'].search([('login', 'ilike', args.username)])
    if not users:
        logger.error(f"❌ No user found with email matching '{args.username}'")
        sys.exit(1)

    for user in users:
        logger.info(f"🔑 Changing password for user: {user.login} (ID: {user.id})")
        user._change_password(args.password)

        if args.disable_2fa:
            user.totp_secret = None
            logger.info(f"🔒 Disabled 2FA for {user.login}")

        logger.info("✅ Password updated successfully.")

# ------------------------------------------------------------------------------
# "run" function to create an Odoo environment - only if we want it
# ------------------------------------------------------------------------------
def run(execute, path_to_config=".", commit_changes=False):
    """
    Executes a function inside the Odoo environment with logging.
    Opens registry on the DB specified in the config file.
    """
    current_folder = os.getcwd()
    config_file = f"{path_to_config}/odoo.conf"

    logger.info(f"📂 Current folder: '{current_folder}', using config file: '{config_file}'")

    # Adjust sys.argv so Odoo picks up our config
    sys.argv = [sys.argv[0], f'--config={config_file}']

    try:
        config.parse_config(sys.argv[1:])
        odoo.service.server.load_server_wide_modules()

        db_name = config['db_name']
        with odoo.registry(db_name).cursor() as cr:
            env = Environment(cr, odoo.SUPERUSER_ID, {})
            logger.info("🔄 Odoo environment initialized")

            logger.debug(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            execute(env)
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

# ------------------------------------------------------------------------------
# Decide how we handle subcommands
# ------------------------------------------------------------------------------
def execute_command(args, config_params):
    """
    Decide which command to run, either with or without Odoo environment.
    """

    def run_commands_with_env(env):
        module_manager = ModuleManager(env)

        if args.command == "install-module":
            module_manager.install_modules(args.module_names)
        elif args.command == "update-module":
            module_manager.update_modules(args.module_names)
        elif args.command == "uninstall-module":
            module_manager.uninstall_modules(args.module_names)
        elif args.command == "list-modules":
            module_manager.list_modules()
        elif args.command == "show-module":
            module_manager.show_module(args.module_names[0])
        elif args.command == "modify-user":
            modify_user(env, args)

    # Commands that do not require an Odoo environment
    if args.command == "restore-db":
        # Use the db_name from config_params
        db_name = config_params["db_name"]

        restorer = DatabaseRestorer(
            dump_file=args.path_to_dump,
            pg_user=args.db_user,  # e.g. "postgres"
            db_name=db_name,       # from odoo.conf
            db_user="odoo",
            db_pass="odoo",
        )
        restorer.restore()
        # No environment needed, just restore and exit
        sys.exit(0)

    # Otherwise, run environment-based commands
    run(run_commands_with_env, path_to_config='.', commit_changes=True)

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


# ------------------------------------------------------------------------------
# Main: parse CLI args, read config, route subcommand
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="CLI for Odoo management tasks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # install-module
    install_parser = subparsers.add_parser("install-module", help="Install one or more Odoo modules")
    install_parser.add_argument("module_names", nargs='+', help="Names of the modules to install")

    # update-module
    update_parser = subparsers.add_parser("update-module", help="Update one or more Odoo modules")
    update_parser.add_argument("module_names", nargs='+', help="Names of the modules to update")

    # uninstall-module
    uninstall_parser = subparsers.add_parser("uninstall-module", help="Uninstall one or more Odoo modules")
    uninstall_parser.add_argument("module_names", nargs='+', help="Names of the modules to uninstall")

    # update-module
    uninstall_parser = subparsers.add_parser("update-module", help="update one or more Odoo modules")
    uninstall_parser.add_argument("module_names", nargs='+', help="Names of the modules to uninstall")

    # list-modules
    list_parser = subparsers.add_parser("list-modules", help="List Odoo modules")

    # show-module
    show_parser = subparsers.add_parser("show-module", help="Show information about an Odoo module")
    show_parser.add_argument("module_names", nargs=1, help="Name of the module to show")  # single module only

    # modify-user
    modify_parser = subparsers.add_parser("modify-user", help="Modify an Odoo user (reset password, disable 2FA)")
    modify_parser.add_argument("-u", "--username", required=True, help="User login (email)")
    modify_parser.add_argument("-p", "--password", required=True, help="New password for the user")
    modify_parser.add_argument("--disable-2fa", action="store_true", help="Disable 2FA for the user")

    # restore-db
    restore_parser = subparsers.add_parser("restore-db", help="Restore the Odoo database")
    restore_parser.add_argument("--path-to-dump", required=True, help="Path to the SQL dump file")
    restore_parser.add_argument("--db-user", help="PostgreSQL user for database restoration (e.g. 'postgres')")

    args = parser.parse_args()

    # 1) Parse Odoo config so we can read db_name from odoo.conf.
    sys.argv = [sys.argv[0], "--config=./odoo.conf"]  # Adjust as needed
    config.parse_config(sys.argv[1:])
    odoo.service.server.load_server_wide_modules()

    config_params = {
        "db_name": config['db_name'],
        # if you need more from config, add them here (db_host, db_port, etc.)
    }

    # 2) Execute the chosen command
    execute_command(args, config_params)

# ------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
