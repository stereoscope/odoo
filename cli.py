#!/usr/bin/env python3
import argparse
import shutil
from scratching.app import run

import logging
import sys
import os
import subprocess

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


class ModuleManager:
    def __init__(self, env):
        self.env = env

    def uninstall_module(self, module_name):
        """Uninstall an Odoo module."""
        logger.info(f"🚀 Uninstalling module: {module_name}")
        mod_ids = self.env['ir.module.module'].search([
            ('name', '=', module_name), ('state', '=', 'installed')
        ])
        if not mod_ids:
            logger.error(f"❌ Module '{module_name}' not found or not installed.")
            return False

        mod_ids.button_uninstall()
        self.env.cr.commit()
        logger.info(f"✅ Module '{module_name}' successfully uninstalled.")
        return True

    def install_modules(self, module_name):
        """Install an Odoo module."""
        logger.info(f"🚀 Installing module: {module_name}")
        mod_ids = self.env['ir.module.module'].search([
            ('name', '=', module_name), ('state', '!=', 'installed')
        ])
        if not mod_ids:
            logger.error(f"❌ Module '{module_name}' not found or already installed.")
            return False

        mod_ids.button_immediate_install()
        self.env.cr.commit()
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


def execute_command(args):
    """Execute CLI commands."""

    def wrapper(env):
        module_manager = ModuleManager(env)

        if args.command == "install-module":
            module_manager.install_modules(args.module_name)
        elif args.command == "uninstall-module":
            module_manager.uninstall_module(args.module_name)
        elif args.command == "modify-user":
            modify_user(env, args)

    run(wrapper, path_to_config='.', commit_changes=True)


def main():
    """CLI entry point with subcommands."""
    parser = argparse.ArgumentParser(description="CLI for Odoo management tasks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Install Module Subcommand
    install_parser = subparsers.add_parser("install-module", help="Install an Odoo module")
    install_parser.add_argument("module_name", help="Name of the module to install")
    install_parser.set_defaults(func=execute_command)

    # Uninstall Module Subcommand
    uninstall_parser = subparsers.add_parser("uninstall-module", help="Uninstall an Odoo module")
    uninstall_parser.add_argument("module_name", help="Name of the module to uninstall")
    uninstall_parser.set_defaults(func=execute_command)

    # Modify User Subcommand
    modify_parser = subparsers.add_parser("modify-user", help="Modify an Odoo user (reset password, disable 2FA)")
    modify_parser.add_argument("-u", "--username", required=True, help="User login (email)")
    modify_parser.add_argument("-p", "--password", required=True, help="New password for the user")
    modify_parser.add_argument("--disable-2fa", action="store_true", help="Disable 2FA for the user")
    modify_parser.set_defaults(func=execute_command)

    # Parse arguments
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
