#!/usr/bin/env bash

set -eu

verify_args() {
    if [[ "$#" != 2 ]]; then
        echo "Usage: $0 <notebook> <output name>" >&2
        exit 1
    fi
}

main() {
    verify_args "$@"
    local readonly fname="$1"
    local readonly outname="$2"
    echo "Rendering notebook ${fname} to ${outname}"
    
    jupyter nbconvert --execute --allow-errors "${fname}" --to html --stdout > "${outname}"
}

main "$@"
