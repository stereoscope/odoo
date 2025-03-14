#!/usr/bin/env python3
import argparse
import shutil
from scratching.app import run

import logging
import sys
import os
from tabulate import tabulate

# Configure logging
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


# Modify ModuleManager to handle multiple modules
class ModuleManager:
    def __init__(self, env):
        self.env = env

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
        table_headers = ["Name", "Description", "State", "Version", "Author", "Installed Version", "Latest Version", "Published Version"]

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
                    module.published_version if module.published_version else "N/A",
                ]
            )

        print(tabulate(module_data, headers=table_headers, tablefmt="fancy_grid"))
        print("""
        installed_version refers the latest version (the one on disk)
        latest_version refers the installed version (the one in database)
        published_version refers the version available on the repository
        """)

    def show_module(self, module_name):
        """Show an Odoo module."""
        logger.info(f"🚀 Showing module: {module_name}")
        modules = self.env['ir.module.module'].search([
            ('name', '=', module_name)
        ])

        if not modules:
            logger.error(f"❌ Module '{module_name}' not found or already installed.")
            return False

        self.print_module_data(modules)

        logger.info(f"✅ Module '{module_name}' successfully installed.")
        return True


def modify_user(env, args):
    """Modify user password and optionally disable 2FA."""
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


# Modify execute_command to handle multiple modules
def execute_command(args):
    def wrapper(env):
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
            module_manager.show_module(args.module_names[0])  # Single module only
        elif args.command == "modify-user":
            modify_user(env, args)

    run(wrapper, path_to_config='.', commit_changes=False)

# Modify CLI argument parsing
def main():
    parser = argparse.ArgumentParser(description="CLI for Odoo management tasks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Install Module
    install_parser = subparsers.add_parser("install-module", help="Install one or more Odoo modules")
    install_parser.add_argument("module_names", nargs='+', help="Names of the modules to install")
    install_parser.set_defaults(func=execute_command)

    # Update Module
    update_parser = subparsers.add_parser("update-module", help="Update one or more Odoo modules")
    update_parser.add_argument("module_names", nargs='+', help="Names of the modules to update")
    update_parser.set_defaults(func=execute_command)

    # Uninstall Module
    uninstall_parser = subparsers.add_parser("uninstall-module", help="Uninstall one or more Odoo modules")
    uninstall_parser.add_argument("module_names", nargs='+', help="Names of the modules to uninstall")
    uninstall_parser.set_defaults(func=execute_command)

    # List Modules
    list_parser = subparsers.add_parser("list-modules", help="List Odoo modules")
    list_parser.set_defaults(func=execute_command)

    # Show Module
    show_parser = subparsers.add_parser("show-module", help="Show information about an Odoo module")
    show_parser.add_argument("module_names", nargs=1, help="Name of the module to show")  # Single module only
    show_parser.set_defaults(func=execute_command)

    # Modify User
    modify_parser = subparsers.add_parser("modify-user", help="Modify an Odoo user (reset password, disable 2FA)")
    modify_parser.add_argument("-u", "--username", required=True, help="User login (email)")
    modify_parser.add_argument("-p", "--password", required=True, help="New password for the user")
    modify_parser.add_argument("--disable-2fa", action="store_true", help="Disable 2FA for the user")
    modify_parser.set_defaults(func=execute_command)

    args = parser.parse_args()
    args.func(args)


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


if __name__ == "__main__":
    main()
