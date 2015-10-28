#!/usr/bin/env sh

set -ue

find_files() {
    dirname=/ngts/pipedev/ParanalOutput/nightly_data/
    find ${dirname} -name '*custom-flat-high-quality.fits'
    for night in 09 13 11 06 05; do
        for camera_id in 801 802 805 806; do
            find ${dirname} -name "201509${night}-ng200*-${camera_id}*.fits"
        done
    done
    find ${dirname} -name '20150909-ng2000-802*without*.fits'
}

main() {
    find_files | while read fname; do
        outname="exploration/renders/$(basename $fname | sed 's/\.fits/.html/')"
        if [[ -e ${outname} ]]; then
            echo "File ${outname} exists, skipping"
        else
            FILENAME=$fname bash ./run_notebook.sh exploration/position_dependency.ipynb ${outname}
        fi
    done
}

main
