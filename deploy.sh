#!/bin/bash

set -eu

BASE_DIR=$(dirname $(realpath -s $0))
HELMCHART=${BASE_DIR}/helmchart
deploy_environment=${1:-}

if [ -z "${deploy_environment}" ] ; then
    project=$(cat /etc/wmcs-project 2>/dev/null || echo "local")
    deploy_environment=$project
fi

maybe_values_file=${HELMCHART}/values-${deploy_environment}.yaml
if [ -r $maybe_values_file ] ; then
    values_file="-f $maybe_values_file"
else
    values_file=""
fi

helm upgrade --install -n jobs-api --create-namespace --force jobs-api ${HELMCHART} ${values_file}
