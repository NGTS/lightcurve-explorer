#!/usr/bin/env sh

set -eu

main() {
    BASEDIR="$(readlink -f $(dirname $0))"
    echo "Running from ${BASEDIR}"

    ${BASEDIR}/venv/bin/python ${BASEDIR}/app.py "$@"
}

main "$@"
