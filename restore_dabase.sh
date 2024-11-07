#!/bin/bash

# Usage: ./restore_db.sh --path-to-dump /path/to/your/dump_file.sql [--user db_user]

# Default PostgreSQL user
PG_USER=$(whoami)

# Initialize variables
BACKUP_FILE=""

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --path-to-dump)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --user)
            PG_USER="$2"
            shift 2
            ;;
        *)
            echo "Invalid option: $1"
            echo "Usage: $0 --path-to-dump <path-to-sql-dump-file> [--user db_user]"
            exit 1
            ;;
    esac
done

# Check if the backup file path is provided
if [[ -z "$BACKUP_FILE" ]]; then
    echo "Usage: $0 --path-to-dump <path-to-sql-dump-file> [--user db_user]"
    exit 1
fi

TMP_BACKUP="/tmp/$(basename "$BACKUP_FILE")"

# Database settings
DB_NAME="odoo"
DB_USER="odoo"
DB_PASS="odoo"

# Stop on the first error
set -e

# Copy the backup file to the temp location
echo "Copying backup file to temporary location..."
cp "$BACKUP_FILE" "$TMP_BACKUP"

# Change to a neutral directory with broad access permissions
cd /tmp

# Drop the existing database and role if they exist
echo "Dropping existing database and role..."
sudo -u "$PG_USER" psql -c "DROP DATABASE IF EXISTS $DB_NAME;"
sudo -u "$PG_USER" psql -c "DROP ROLE IF EXISTS $DB_USER;"

# Create a new database and role
echo "Creating new database and role..."
sudo -u "$PG_USER" psql -c "CREATE DATABASE $DB_NAME;"
sudo -u "$PG_USER" psql -c "CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASS';"
sudo -u "$PG_USER" psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Restore the database from the backup file, suppressing output
echo "Restoring the database from the backup file..."
sudo -u "$PG_USER" psql -d $DB_NAME -U postgres -f "$TMP_BACKUP" >/dev/null 2>&1

# Remove the backup file from the temp location
echo "Cleaning up the temporary backup file..."
rm "$TMP_BACKUP"

echo "Database restoration complete."

echo "Changing web.base.url 'http://localhost:8069'"
sudo -u "$PG_USER" psql -d $DB_NAME -c "update ir_config_parameter set value = 'http://localhost:8069' where key = 'web.base.url'"
echo "Setting up outgoing mailserver configuration localhost:1025 for mailhog"
sudo -u "$PG_USER" psql -d $DB_NAME -c "insert into public.ir_mail_server (id, smtp_port, sequence, create_uid, write_uid, name, from_filter, smtp_host, smtp_authentication, smtp_user, smtp_pass, smtp_encryption, smtp_debug, active, create_date, write_date, smtp_ssl_certificate, smtp_ssl_private_key) values (1, 1025, 10, 7, 7, 'Mailhog', null, 'localhost', 'login', null, null, 'none', false, true, '2024-07-11 08:06:45.160085', '2024-07-11 08:06:45.160085', null, null);"

echo "Done"

