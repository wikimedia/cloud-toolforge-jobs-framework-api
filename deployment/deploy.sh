#!/bin/bash

set -e

if [ ! -d "./devel/" ] || [ ! -d "./deployment/" ] ; then
    echo "E: please run this script from the root of the repository, we need devel/ and deployment/" >&2
    exit 1
fi

project=$(cat /etc/wmcs-project)
fqdn="jobs.svc.${project}.eqiad1.wikimedia.cloud"

# load deployment
kubectl apply -f deployment/deployment.yaml
kubectl apply -f deployment/deployment-${project}.yaml

# k8s CA secret for nginx-ingress
kubectl -n jobs-api delete secret k8s-ca-secret || true
tempfile=$(mktemp)
kubectl config view --raw -o json | jq -r '.clusters[0].cluster."certificate-authority-data"' | tr -d '"' | base64 --decode > ${tempfile}
kubectl -n jobs-api create secret generic k8s-ca-secret --from-file=ca.crt=${tempfile}
rm -f ${tempfile}

# we need the wmcs-k8s-get-cert script. Are we in a local laptop or in tools/toolsbeta for real?
wmcs_k8s_get_cert=$(which wmcs-k8s-get-cert || echo "unknown")
if [ "${wmcs_k8s_get_cert}" == "unknown" ] ; then
    wmcs_k8s_get_cert="./devel/k8s-get-cert.sh"
fi

# nginx-ingress own TLS secret
output=$(${wmcs_k8s_get_cert} ${fqdn})
certfile=$(head -1 <<< $output)
keyfile=$(tail -1 <<< $output)
kubectl -n jobs-api delete secret jobs-api-server-cert || true
kubectl -n jobs-api create secret tls jobs-api-server-cert --key $keyfile --cert $certfile
