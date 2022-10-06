#!/bin/bash


COMPOSE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# count number of arguments in the format `-arg value`
n=1
while [ $n -le $# ]
do
    if [ ${!n:0:1} == "-" ]; then
        n=$((n + 2))
    else
        break
    fi
done

# put args in format `-arg value` before service args
docker-compose -f $COMPOSE_DIR/docker-compose.yml run ${@:1:$n-1} account_django ${@:$n:$#}
