# README for local development

This file contains instruction on how to build a local development for this project.

Unfortunatelly, you need a kubernetes cluster. There are several ways of doing that. The author of
this README was only able to run kind (https://kind.sigs.k8s.io/) on the laptop so that's what this
uses.

 0) Get docker working on your laptop

  Follow upstream docs. The kind cluster is based on docker.

 1) Install kind (https://kind.sigs.k8s.io/)

  Just follow upstream docs, but don't create a cluster just yet.

 2) Configure kind and the environment

  The default kind install won't expose the ingress port in localhost. It also wont allow you
  to mount host files.

  You likely need a file like this one (~/kind.yaml):

```
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 30001
    hostPort: 30001
    protocol: TCP
  extraMounts:
  - hostPath: /data/project/
    containerPath: /data/project/
  - hostPath: /etc/wmcs-project
    containerPath: /etc/wmcs-project
  - hostPath: /var/lib/sss/pipes/
    containerPath: /var/lib/sss/pipes/
```

 3) Bootstrap kind cluster

```
$ kind create cluster --config ~/kind.yaml
```

  Make sure kubectl works as expected, next steps require it.

 4) Secret with the kubernetes CA:

  The string produced by the next command needs to be added to the `k8s-ca-secret` Secret in
  the `deployment/deployment-kind-local.yaml` file.

```
$ kubectl config view --raw -o json | jq -r '.clusters[0].cluster."certificate-authority-data"' | tr -d '"' | base64 --decode | base64 -w0
```

  If in a later stage, once the `jobs-api` namespace exists, you can get the k8s CA from the
  .kube/config file installed by kind, and load it directly in PEM format:
```
$ kubectl config view --raw -o json | jq -r '.clusters[0].cluster."certificate-authority-data"' | tr -d '"' | base64 --decode > ca.crt
$ kubectl -n jobs-api create secret generic k8s-ca-secret --from-file=ca.crt=ca.crt
```

 5) Generate server TLS certs.

  This is the TLS cert that will be used by nginx-ingress in front of the jobs-framework-api.

```
$ devel/k8s-get-cert.sh jobs.svc.toolsbeta.eqiad1.wikimedia.cloud
/tmp/tmp.HALKayZVhf/k8s-cert.pem
/tmp/tmp.HALKayZVhf/k8s-key.pem
```

  The string produced by the next command needs to be added to the `jobs-api-server-cert` Secret in
  the `deployment/deployment-kind-local.yaml` file.

```
$ echo -n "tls.crt: " ; base64 -w0 /tmp/tmp.HALKayZVhf/k8s-cert.pem ; echo
$ echo -n "tls.key: " ; base64 -w0 /tmp/tmp.HALKayZVhf/k8s-key.pem ; echo
```

  If in a later stage, once the `jobs-api` namespace exists, you can get this secret injected into
  kubrenetes with:

```
$ kubectl -n jobs-api create secret tls jobs-api-server-cert --key /tmp/xxx/k8s-key.pem --cert /tmp/xxx/k8s-cert.pem
```

 6) Setup fake user `test`, and the rest of the environment.

  In Toolforge kubernetes proper, this would be done by maintain-kubeusers.

```
$ devel/setup.sh
```

 7) Build jobs-framework-api docker image

```
$ docker build --tag jobs-api .
```

 8) Load the docker image into kind

  This way the docker image can be used in k8s deployments and such. Like having the image on a
  docker registry.

```
$ kind load docker-image jobs-api:latest
```

 9) Deploy the whole jobs-api setup into kubernetes

```
$ kubectl apply -f deployment/deployment-kind-local.yaml
```

 10) At this point, hopefully, it should work:

```
$ curl https://jobs.svc.toolsbeta.eqiad1.wikimedia.cloud:30001/api/v1/containers/ \
  -H "Host:jobs.svc.toolsbeta.eqiad1.wikimedia.cloud" \
  --cert /data/project/test/.toolskube/client.crt \
  --key /data/project/test/.toolskube/client.key \
  --resolve jobs.svc.toolsbeta.eqiad1.wikimedia.cloud:30001:127.0.0.1
```

 11) Development iteration:

 Make code changes, and follow from step 7 onwards.
