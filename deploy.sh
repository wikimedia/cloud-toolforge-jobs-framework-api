#!/bin/bash

set -eu

BASE_DIR=$(dirname $(realpath -s $0))
HELMCHART=${BASE_DIR}/helmchart
deploy_environment=${1:-}
project=$(cat /etc/wmcs-project 2>/dev/null || echo "local")
fqdn="jobs.svc.${project}.eqiad1.wikimedia.cloud"

if [ -z "${deploy_environment}" ] ; then
    deploy_environment=$project
fi

# we need the wmcs-k8s-get-cert script. Are we in a local laptop or in tools/toolsbeta for real?
wmcs_k8s_get_cert=$(which wmcs-k8s-get-cert || echo "unknown")
if [ "${wmcs_k8s_get_cert}" == "unknown" ] ; then
    wmcs_k8s_get_cert="${BASE_DIR}/utils/k8s-get-cert.sh"
fi

# namespace needs to exist for the certificate, but helm would require the certificate.
# to avoid such chicken-egg problem, just create the namespace now.
# this is a NOOP if already present anyway, and helm below wont complain either
kubectl create namespace jobs-api --dry-run=client -o yaml | kubectl apply -f -

# TLS certificate for https requests
output=$(${wmcs_k8s_get_cert} ${fqdn})
certfile=$(head -1 <<< $output)
keyfile=$(tail -1 <<< $output)
kubectl -n jobs-api delete secret jobs-api-server-cert || true
kubectl -n jobs-api create secret tls jobs-api-server-cert --key $keyfile --cert $certfile

maybe_values_file=${HELMCHART}/values-${deploy_environment}.yaml
if [ -r $maybe_values_file ] ; then
    values_file="-f $maybe_values_file"
else
    values_file=""
fi

helm upgrade --install -n jobs-api --force jobs-api ${HELMCHART} ${values_file}
