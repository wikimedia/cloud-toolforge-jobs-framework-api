# toolforge jobs framework

This is the source code of the toolforge jobs framework.

## Installation

```console
toolsbeta.test@toolsbeta-sgebastion-04:~/jobs-framework-api$ python3 api.py
[..]
```

## Usage

```console
aborrero@toolsbeta-sgebastion-04:~ $ curl localhost:5000/api/v1/run/ -d "name=test4" -d "type=t" -d "cmd=true" -X POST
"job.batch/test4 created\n"
aborrero@toolsbeta-sgebastion-04:~ $ curl localhost:5000/api/v1/list/
[
    {
        "cmd": "true",
        "name": "test",
        "namespace": "tool-test",
        "status": "unknown",
        "type": "docker-registry.tools.wmflabs.org/toolforge-buster-sssd:latest",
        "user": "test"
    },
    {
        "cmd": "true",
        "name": "test2",
        "namespace": "tool-test",
        "status": "unknown",
        "type": "docker-registry.tools.wmflabs.org/toolforge-buster-sssd:latest",
        "user": "test"
    },
    {
        "cmd": "true",
        "name": "test3",
        "namespace": "tool-test",
        "status": "unknown",
        "type": "docker-registry.tools.wmflabs.org/toolforge-buster-sssd:latest",
        "user": "test"
    },
    {
        "cmd": "true",
        "name": "test4",
        "namespace": "tool-test",
        "status": "unknown",
        "type": "docker-registry.tools.wmflabs.org/toolforge-buster-sssd:latest",
        "user": "test"
    }
]
aborrero@toolsbeta-sgebastion-04:~ $ curl localhost:5000/api/v1/flush/ -X DELETE
null
aborrero@toolsbeta-sgebastion-04:~ 3s $ curl localhost:5000/api/v1/list/
[]
aborrero@toolsbeta-sgebastion-04:~ $ curl localhost:5000/api/v1/run/ -d "name=test" -d "type=t" -d "cmd=true" -X POST
"job.batch/test created\n"
aborrero@toolsbeta-sgebastion-04:~ 6s $ curl localhost:5000/api/v1/show/test
{
    "cmd": "true",
    "name": "test",
    "namespace": "tool-test",
    "status": "unknown",
    "type": "docker-registry.tools.wmflabs.org/toolforge-buster-sssd:latest",
    "user": "test"
}
aborrero@toolsbeta-sgebastion-04:~ $ curl localhost:5000/api/v1/delete/test -X DELETE
"job.batch \"test\" deleted\n"
aborrero@toolsbeta-sgebastion-04:~ $ curl localhost:5000/api/v1/list/
[]
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[AGPLv3](https://choosealicense.com/licenses/agpl-3.0/)
