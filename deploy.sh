#!/bin/bash

set -e

if [ ! -d "./devel/" ] || [ ! -d "./deployment/" ] ; then
    echo "E: please run this script from the root of the repository, we need devel/ and deployment/" >&2
    exit 1
fi

project=$(cat /etc/wmcs-project)
fqdn="jobs.svc.${project}.eqiad1.wikimedia.cloud"

# we need the wmcs-k8s-get-cert script. Are we in a local laptop or in tools/toolsbeta for real?
wmcs_k8s_get_cert=$(which wmcs-k8s-get-cert || echo "unknown")
if [ "${wmcs_k8s_get_cert}" == "unknown" ] ; then
    wmcs_k8s_get_cert="./devel/k8s-get-cert.sh"
fi

# namespace needs to exist for the certificate, but the yaml file requires the namespace
kubectl create namespace jobs-api || true

# TLS certificate for https requests
output=$(${wmcs_k8s_get_cert} ${fqdn})
certfile=$(head -1 <<< $output)
keyfile=$(tail -1 <<< $output)
kubectl -n jobs-api delete secret jobs-api-server-cert || true
kubectl -n jobs-api create secret tls jobs-api-server-cert --key $keyfile --cert $certfile

# load deployment
kubectl apply -f deployment/deployment.yaml
