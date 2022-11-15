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
featureGates:
  "TTLAfterFinished": true
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
$ kind create cluster --config ~/kind.yaml --image kindest/node:v1.18.19@sha256:xxxxxxxx
```

  Make sure kubectl works as expected, next steps require it.

  The --image switch lets you select a particular k8s version. The SHA can be obtained from:
  https://github.com/kubernetes-sigs/kind/releases
  Make sure you deploy the same k8s version that tools/toolsbeta use.

 4) Deploy jobs-api

  From the top level directory of this repository, run:

```
$ ./deploy.sh
```
  Now you need to override the imagepull policy for the jobs-api deployment:

```
$ kubectl apply -f devel/kind-deployment-overrides.yaml
```

 5) Setup fake user `test`, and the rest of the environment.

  In Toolforge kubernetes proper, this would be done by maintain-kubeusers.

```
$ devel/setup.sh
```

 6) Build the jobs-framework-api docker image

```
$ docker build --tag jobs-api .
```

 7) Load the docker image into kind

  This way the docker image can be used in k8s deployments and such. Like having the image on a
  docker registry.

```
$ kind load docker-image jobs-api:latest
```

 8) At this point, hopefully, it should work:

```
$ curl https://jobs.svc.toolsbeta.eqiad1.wikimedia.cloud:30001/api/v1/images/ \
  -H "Host:jobs.svc.toolsbeta.eqiad1.wikimedia.cloud" \
  --cert /data/project/test/.toolskube/client.crt \
  --key /data/project/test/.toolskube/client.key \
  --resolve jobs.svc.toolsbeta.eqiad1.wikimedia.cloud:30001:127.0.0.1
```

 9) Development iteration:

 Make code changes, and follow from step 6 onwards. Probably something like this:

```
$ docker build --tag jobs-api . ; kind load docker-image jobs-api:latest ; kubectl -n jobs-api rollout restart deployment/jobs-api
```
