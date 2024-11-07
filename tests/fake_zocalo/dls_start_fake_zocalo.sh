#!/bin/bash
function cleanup()
{
    pkill -f rabbitmq
    rm -rf /home/$USER/.zocalo/*
    echo "May take some seconds for zocalo to die, do not immediately try and restart"
}

trap cleanup EXIT

if [[ -n "$VIRTUAL_ENV" ]]; then
    deactivate
fi

# Create .zocalo if it doesn't exist
ZOCALO_DIR=/home/$USER/.zocalo/
if [[ ! -d "$ZOCALO_DIR" ]]; then
    echo "Creating directory $ZOCALO_DIR"
    mkdir -p "$ZOCALO_DIR"
fi

# kills the gda dummy activemq, that takes the port for rabbitmq
module load dasctools
activemq-for-dummy stop

# starts the rabbitmq server and generates some credentials in ~/.fake_zocalo
module load rabbitmq/dev

# allows the `dev_bluesky` zocalo environment to be used
module load dials/latest

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
python $SCRIPT_DIR/__main__.py
