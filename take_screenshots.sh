#!/usr/bin/env sh

set -eu

start_server() {
    bash ./run_from_anywhere.sh data/20150911-ng2000-802-custom-flat-high-quality.fits -b 100 -p 5000 >/dev/null
}

finish() {
    echo "Killing pid ${PID}"
    kill -9 ${PID}
}
trap finish EXIT

main() {
    echo 'Starting server'
    start_server &
    PID=$!
    sleep 5
    echo 'Taking screenshots'
    phantomjs scripts/screenshot.js
}

main
