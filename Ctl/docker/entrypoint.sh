#!/bin/sh

function migrate_all() {
  echo applying all migrations
  manage migrate
}


cd $SERVICE_HOME
case "$@" in
  "uwsgi" )
    echo starting uwsgi
    if [[ -z "$NO_MIGRATE" ]]; then
      migrate_all
    fi
    exec venv/bin/uwsgi --ini etc/django-uwsgi.ini
    ;;
	# good to keep it as a separate arg incase we end up with multi stage migrations tho
  "migrate_all" )
    migrate_all
    ;;
  "run_tests" )
    source venv/bin/activate
    cd main
    export DJANGO_SETTINGS_MODULE=account_service.settings
    pytest tests/ -vv --cov-report=term-missing --cov-report=xml --cov=account --cov=billing --cov=common --cov=applications 
    ;;
  "test_mode" )
    source venv/bin/activate
    cd main
    export DJANGO_SETTINGS_MODULE=account_service.settings
    echo dropping to shell
    exec "/bin/sh"
    ;;
  "pdb_sync" )
    peeringdb -C etc/peeringdb/ sync
    ;;
  "/bin/sh" )
    echo dropping to shell "$1" - "$@"
    exec $@
    ;;
  * )
    if [[ -z "$NO_MIGRATE" ]]; then
      migrate_all
    fi
    exec manage $@
    ;;
esac
