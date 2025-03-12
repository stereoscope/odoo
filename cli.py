#!/usr/bin/env python3
import argparse
import shutil
from scratching.app import run

import logging
import sys
import os
import subprocess

# Configure logging (Ensure console and file logging work properly)
LOG_FILE = "odoo_cli.log"
logger = logging.getLogger("odoo_cli")

if not logger.handlers:
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")

    # File handler (Logs everything)
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler (Shows INFO+ messages in CLI)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Ensure INFO messages show in CLI
    console_handler.setFormatter(formatter)

    # Attach handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent duplicate logs
    logger.propagate = False

logger.info("✅ Logging system initialized. Logs will be shown in CLI and stored in 'odoo_cli.log'.")


class DatabaseRestorer:
    def __init__(self, dump_file, pg_user=None, db_name="odoo", db_user="odoo", db_pass="odoo"):
        self.dump_file = dump_file
        self.pg_user = pg_user or os.getlogin()
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
        """Execute a shell command and handle errors, suppressing stdout/stderr if needed."""
        try:
            logger.debug(f"Executing: {command}")

            # Open /dev/null to suppress stdout/stderr if suppress_output is True
            stdout_dest = subprocess.PIPE if capture_output else (open(os.devnull, "w") if suppress_output else sys.stdout)
            stderr_dest = subprocess.PIPE if capture_output else (open(os.devnull, "w") if suppress_output else sys.stderr)

            result = subprocess.run(
                command, shell=True, check=True, text=True,
                stdout=stdout_dest, stderr=stderr_dest
            )

            # Return output if capture_output=True
            return result.stdout if capture_output else None

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error executing command: {command}")
            logger.error(f"🔻 Error details: {e.stderr if e.stderr else str(e)}")
            sys.exit(1)

    def restore(self):
        """Restore the database from a backup file."""
        self.check_psql_installed()

        logger.info("📂 Copying backup file to temporary location...")
        shutil.copy(self.dump_file, self.tmp_backup)

        logger.info("💣 Dropping existing database and role...")
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
        self.run_command(f"psql -U {self.pg_user} -d {self.db_name} -c \"UPDATE ir_config_parameter SET value = 'http://localhost:8069' WHERE key = 'web.base.url'\"")

        logger.info("📧 Setting up outgoing mailserver configuration for Mailhog...")
        mailhog_sql = """
        INSERT INTO public.ir_mail_server 
        (id, smtp_port, sequence, create_uid, write_uid, name, from_filter, smtp_host, smtp_authentication, smtp_user, smtp_pass, smtp_encryption, smtp_debug, active, create_date, write_date, smtp_ssl_certificate, smtp_ssl_private_key) 
        VALUES (1, 1025, 10, 7, 7, 'Mailhog', NULL, 'localhost', 'login', NULL, NULL, 'none', false, true, '2024-07-11 08:06:45.160085', '2024-07-11 08:06:45.160085', NULL, NULL) 
        ON CONFLICT (id) DO NOTHING;
        """
        self.run_command(f"psql -U {self.pg_user} -d {self.db_name} -c \"{mailhog_sql}\"")

        logger.info("✅ Database restoration complete.")

def modify_user(env, args):
    """Modify user password and optionally disable 2FA."""
    logger.info(f"🔍 Searching for user matching '{args.username}'...")
    users = env["res.users"].search([("login", "ilike", args.username)])
    if not users:
        logger.error(f"❌ No user found with email matching '{args.username}'")
        sys.exit(1)

    for user in users:
        logger.info(f"🔑 Changing password for user: {user.login} (ID: {user.id})")
        user._change_password(args.password)

        if args.disable_2fa:
            user.totp_secret = None  # Disable 2FA
            logger.info(f"🔒 Disabled 2FA for {user.login}")

        logger.info("✅ Password updated successfully.")

def execute_command(args):
    """Ensure that database restoration runs first if requested."""
    if args.restore_db:
        logger.info(f"🛠️ Restoring database from: {args.restore_db}")
        restorer = DatabaseRestorer(dump_file=args.restore_db, pg_user=args.db_user)
        restorer.restore()
        logger.info("✅ Database restoration complete.")

    args.func(args)  # Execute primary command

def main():
    """CLI entry point with subcommands."""
    parser = argparse.ArgumentParser(description="CLI for Odoo management tasks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Global restore option for all commands
    parser.add_argument("--restore-db", metavar="PATH", help="Restore database from a dump file before executing command")
    parser.add_argument("--db-user", help="PostgreSQL user for database restoration")

    # Restore DB subcommand
    restore_parser = subparsers.add_parser("restore", help="Restore the Odoo database")
    restore_parser.add_argument("--path-to-dump", required=True, help="Path to the SQL dump file")
    restore_parser.add_argument("--db-user", help="PostgreSQL user for database restoration")
    restore_parser.set_defaults(func=lambda args: DatabaseRestorer(args.path_to_dump, args.db_user).restore())

    # Modify User subcommand
    modify_parser = subparsers.add_parser("modify-user", help="Modify an Odoo user (reset password, disable 2FA)")
    modify_parser.add_argument("-u", "--username", required=True, help="Email (or partial match) of the user")
    modify_parser.add_argument("-p", "--password", required=True, help="New password for the user")
    modify_parser.add_argument("--disable-2fa", action="store_true", help="Disable 2FA for the user")
    modify_parser.set_defaults(func=lambda args: run(lambda env: modify_user(env, args), path_to_config='.', commit_changes=True))

    # Parse arguments and execute with restore logic first
    args = parser.parse_args()
    execute_command(args)

if __name__ == "__main__":
    main()
