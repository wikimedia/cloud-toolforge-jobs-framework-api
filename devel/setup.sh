#!/bin/bash

set -e

if [ ! -d "./devel/" ] ; then
    echo "E: please run this script from the root of the repository" >&2
    exit 1
fi

USER="test"

sudo sh -c "echo 'toolsbeta' > /etc/wmcs-project"

sudo mkdir -p /var/lib/sss/pipes/

sudo mkdir -p /data/project/
sudo chmod -R a+wx /data/project/

# to hold .kube/config
mkdir -p /data/project/${USER}/.kube/

# to hold user certificates
mkdir -p /data/project/${USER}/.toolskube/

# generate user certificates and put them in the right place
GET_CERT_SCRIPT="./devel/k8s-get-cert.sh"
OUTPUT=$(${GET_CERT_SCRIPT} "test")
CERT_FILE="$(head -1 <<< $OUTPUT)"
KEY_FILE="$(tail -1 <<< $OUTPUT)"
mv $CERT_FILE /data/project/${USER}/.toolskube/client.crt
mv $KEY_FILE /data/project/${USER}/.toolskube/client.key

# generate kubeconfig file
K8S_CA=$(kubectl config view --raw -o json | jq -r '.clusters[0].cluster."certificate-authority-data"' | tr -d '"' | base64 --decode | base64 -w0)

cat <<EOF > /data/project/${USER}/.kube/config
---
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: ${K8S_CA}
    server: https://kind-control-plane:6443
  name: kind-kind
contexts:
- context:
    cluster: kind-kind
    user: tf-test
    namespace: tool-test
  name: kind-kind
current-context: kind-kind
kind: Config
preferences: {}
users:
- name: tf-test
  user:
    client-certificate: /data/project/test/.toolskube/client.crt
    client-key: /data/project/test/.toolskube/client.key
EOF

# generate user stuff
kubectl create namespace "tool-test"

# generate fake toolforge config
kubectl apply -f ./devel/faketoolforge.yaml
