# Jobs Framework API

This is the source code of the Toolforge Jobs Framework API.

The TJF creates an abstraction layer over kubernetes Jobs, CronJobs and Deployments to allow
operating a Kubernetes installation as if it were a Grid (like GridEngine).

This was created for [Wikimedia Toolforge](https://toolforge.org).

## Installation

Run `./deploy.sh`.

## Development

You need a local kubernetes cluster with a fake Toolforge installed to it. There are several ways
of doing that. The author of this README recommends the lima-kilo project.

 0) Get the lima-kilo setup on your laptop:

  Follow docs at https://gitlab.wikimedia.org/repos/cloud/toolforge/lima-kilo

 1) Build the jobs-framework-api docker image

```
$ docker build --tag jobs-api .
```

 2) Load the docker image into kind (or minikube)

  This way the docker image can be used in k8s deployments and such. Like having the image on a
  docker registry.

```
$ kind load docker-image jobs-api:latest -n toolforge
```

 3) Deploy the component into your local kubernetes:

```
$ ./deploy.sh local
```

 4) At this point, hopefully, it should work:

```
$ curl https://jobs.svc.toolsbeta.eqiad1.wikimedia.cloud:30001/api/v1/images/ \
  -H "Host:jobs.svc.toolsbeta.eqiad1.wikimedia.cloud" \
  --cert /data/project/tf-test/.toolskube/client.crt \
  --key /data/project/tf-test/.toolskube/client.key \
  --resolve jobs.svc.toolsbeta.eqiad1.wikimedia.cloud:30001:127.0.0.1
```

 5) Development iteration:

 Make code changes, and follow from step 1 onwards. Probably something like this:

```
$ docker build --tag jobs-api . ; kind load docker-image jobs-api:latest -n toolforge ; kubectl -n jobs-api rollout restart deployment/jobs-api
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[AGPLv3](https://choosealicense.com/licenses/agpl-3.0/)
