#!/bin/bash
function cleanup()
{
    pkill -f rabbitmq
    rm -rf /home/$USER/.zocalo/*
    echo "May take some seconds for zocalo to die, do not immediately try and restart"
}

trap cleanup EXIT

# kills the gda dummy activemq, that takes the port for rabbitmq
module load dasctools
activemq-for-dummy stop

# starts the rabbitmq server and generates some credentials in ~/.fake_zocalo
module load rabbitmq/dev

# allows the `dev_artemis` zocalo environment to be used
module load dials/latest

source ../hyperion/.venv/bin/activate
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
python $SCRIPT_DIR/__main__.py
