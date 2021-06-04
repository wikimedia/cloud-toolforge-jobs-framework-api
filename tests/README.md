# DISCLAIMER

The author doesn't know yet (didn't invest time) into doing this in a more pythonic way. The goal
was to just have a way to run a bunch of commands and check the output.

We can create a proper pytest testsuite later once we have time for it.

Even better: we can work on triggering these tests from our jekins CI pipeline.
There are several complexities in doing that, such as setting the environment: remember, we need a
Kubernetes API, directories, etc.

# How to use it

The `cmd-checklist.yaml` file should be equivalent of manually running a bunch of curl commands.

If you are running the jobs-api server in k8s (see devel/README.md) then:

```
$ tests/cmd-checklist-runner.py --config-file tests/cmd-checklist.yaml
```
If you are running the server locally (see instructions in devel/README.md) then you will need
to override the env, something like this:

```
$ sed -i s@https://kind-control-plane:6443@https://127.0.0.1:43629@g /data/project/test/.kube/config
$ python3 api.py
$ CURL_HDR="ssl-client-subject-dn: CN=test" CURL_URL="http://localhost:8080/api/v1" CURL_ARGS="" tests/cmd-checklist-runner.py --config-file tests/cmd-checklist.yaml
```


