#!/bin/bash
# Furkan Gümüser
# Datenbank anonymisieren
#sudo -u postgres ./ano.sh erfolg_1 5432 14
port=5432
version=10
help()
{
    echo "-h help, this message"
    echo "-v version, odoo version to check if the unaccent shema is needed. everything above 14 needs to add the shema [default: 10]"
    echo "               Needs to be executed with 'sudo -u postgres'"
    echo "-d db name, name of the "
    echo "-p port, port of db [default: 5432]"
    echo "-n project name, name of the project for the sql file."
    echo "               It loads the ano.sql file in ~/gitrepos/PROJECT/setup for additional, project specific, ano commands"
    echo "-s script path, if the ano script is not in the default. Absolut Path to the file"
    exit
}
while getopts hn:v:p:d:s: flag
do
    case $flag in
        h)help;;
        v)version=$OPTARG;;
        p)port=$OPTARG;;
        d)db=$OPTARG;;
        n)project=$OPTARG;;
        s)file=$OPTARG;;
        \?) echo "ERROR, non existent flag" exit;;
    esac
done
echo "Version: $version"
echo "DB:      $db"
echo "Port:    $port"
echo "Project: $project"
echo "File:    $file"
if [ -z "$db" ]; then
        echo ""
        echo 'Missing -d. Cant connect to a db without a name.'
        echo "Exiting"
        exit 1
fi
echo --
# execute with sudo -u postgres
if [ $version -ge "14" ]
then
    echo -- Creating unaccent
    psql -d $db -p $port -U postgres -c "CREATE EXTENSION IF NOT EXISTS unaccent schema pg_catalog;"
    psql -d $db -p $port -U postgres -c "CREATE SCHEMA IF NOT EXISTS unaccent_schema;"
fi
echo -- Disable schedulers
psql -d $db -p $port -c "UPDATE ir_cron SET active = FALSE where id > 4 or id = 3;"
echo -- Corrupt E-Mail addresses
psql -d $db -p $port -c "UPDATE res_partner SET email = replace(email, '@', '#');"
echo -- Deactivate all mail servers
psql -d $db -p $port -c "UPDATE ir_mail_server SET active = FALSE;"
psql -d $db -p $port -c "UPDATE fetchmail_server SET active = FALSE;"
echo -- For all users: Set password to x
password='$pbkdf2-sha512$25000$.r93rhUipFQKIYSQci6FcA$hesuvDYTEwTkjUYm/LSt6CH0B/oEMN3JUkpbL1K9gU3vnM3EEdojChU4cjSs21nCIjx88aoVJZ12PBahjM/0Yw'
psql -d $db -p $port -c "UPDATE res_users SET password = '$password';"
echo -- Admin-Login
psql -d $db -p $port -c "UPDATE res_users SET login = 'admin' where id = 2;"
echo -- delete 2FA Secrets
psql -d $db -p $port -c "UPDATE res_users SET totp_secret = null;"
if [[ -n $project ]]
then
    echo project test
    echo $project
    path=~/gitrepos/${project}/setup/ano.sql
fi
if [[ -n $file ]]
then
    echo $file
    echo file test
    path=${file}
fi
if [[ -n $path ]]
then
    echo -- Executing custom ano script
    echo $path
    psql -d $db -p $port < $path
fi
exit
