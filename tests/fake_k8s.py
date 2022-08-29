fake_images = [
    {
        "shortname": "tf-bullseye-std",
        "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-standalone:latest",
    },
    {
        "shortname": "tf-buster-std-DEPRECATED",
        "image": "docker-registry.tools.wmflabs.org/toolforge-buster-standalone:latest",
    },
    {
        "shortname": "tf-golang",
        "image": "docker-registry.tools.wmflabs.org/toolforge-golang-sssd-base:latest",
    },
    {
        "shortname": "tf-golang111",
        "image": "docker-registry.tools.wmflabs.org/toolforge-golang111-sssd-base:latest",
    },
]

JOB_CONT_NO_EMAILS_NO_FILELOG_OLD_ARRAY = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "annotations": {"deployment.kubernetes.io/revision": "1"},
        "labels": {
            "app.kubernetes.io/component": "deployments",
            "app.kubernetes.io/created-by": "test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "myjob",
            "app.kubernetes.io/version": "1",
            "jobs.toolforge.org/emails": "none",
            "toolforge": "tool",
        },
        "name": "myjob",
        "namespace": "test-tool",
    },
    "spec": {
        "selector": {
            "matchLabels": {
                "app.kubernetes.io/component": "deployments",
                "app.kubernetes.io/created-by": "test",
                "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                "app.kubernetes.io/name": "myjob",
                "app.kubernetes.io/version": "1",
                "jobs.toolforge.org/emails": "none",
                "toolforge": "tool",
            }
        },
        "template": {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/component": "deployments",
                    "app.kubernetes.io/created-by": "test",
                    "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                    "app.kubernetes.io/name": "myjob",
                    "app.kubernetes.io/version": "1",
                    "jobs.toolforge.org/emails": "none",
                    "toolforge": "tool",
                }
            },
            "spec": {
                "containers": [
                    {
                        "command": [
                            "/bin/sh",
                            "-c",
                            "--",
                            "./command-by-the-user.sh --with-args 1>>/dev/null 2>>/dev/null",
                        ],
                        "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd:latest",
                        "imagePullPolicy": "Always",
                        "name": "myjob",
                        "workingDir": "/data/project/test",
                    }
                ],
            },
        },
    },
}

JOB_CONT_NO_EMAILS_YES_FILELOG_OLD_ARRAY = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "annotations": {"deployment.kubernetes.io/revision": "1"},
        "labels": {
            "app.kubernetes.io/component": "deployments",
            "app.kubernetes.io/created-by": "test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "myjob",
            "app.kubernetes.io/version": "1",
            "jobs.toolforge.org/emails": "none",
            "jobs.toolforge.org/filelog": "yes",
            "toolforge": "tool",
        },
        "name": "myjob",
        "namespace": "test-tool",
    },
    "spec": {
        "selector": {
            "matchLabels": {
                "app.kubernetes.io/component": "deployments",
                "app.kubernetes.io/created-by": "test",
                "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                "app.kubernetes.io/name": "myjob",
                "app.kubernetes.io/version": "1",
                "jobs.toolforge.org/emails": "none",
                "jobs.toolforge.org/filelog": "yes",
                "toolforge": "tool",
            }
        },
        "template": {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/component": "deployments",
                    "app.kubernetes.io/created-by": "test",
                    "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                    "app.kubernetes.io/name": "myjob",
                    "app.kubernetes.io/version": "1",
                    "jobs.toolforge.org/emails": "none",
                    "jobs.toolforge.org/filelog": "yes",
                    "toolforge": "tool",
                }
            },
            "spec": {
                "containers": [
                    {
                        "command": [
                            "/bin/sh",
                            "-c",
                            "--",
                            "./command-by-the-user.sh --with-args 1>>myjob.out 2>>myjob.err",
                        ],
                        "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd:latest",
                        "imagePullPolicy": "Always",
                        "name": "myjob",
                        "workingDir": "/data/project/test",
                    }
                ],
            },
        },
    },
}

JOB_CONT_NO_EMAILS_NO_FILELOG_NEW_ARRAY = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "annotations": {"deployment.kubernetes.io/revision": "1"},
        "labels": {
            "app.kubernetes.io/component": "deployments",
            "app.kubernetes.io/created-by": "test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "myjob",
            "app.kubernetes.io/version": "1",
            "jobs.toolforge.org/emails": "none",
            "jobs.toolforge.org/command-new-format": "yes",
            "toolforge": "tool",
        },
        "name": "myjob",
        "namespace": "test-tool",
    },
    "spec": {
        "selector": {
            "matchLabels": {
                "app.kubernetes.io/component": "deployments",
                "app.kubernetes.io/created-by": "test",
                "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                "app.kubernetes.io/name": "myjob",
                "app.kubernetes.io/version": "1",
                "jobs.toolforge.org/emails": "none",
                "jobs.toolforge.org/command-new-format": "yes",
                "toolforge": "tool",
            }
        },
        "template": {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/component": "deployments",
                    "app.kubernetes.io/created-by": "test",
                    "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                    "app.kubernetes.io/name": "myjob",
                    "app.kubernetes.io/version": "1",
                    "jobs.toolforge.org/emails": "none",
                    "jobs.toolforge.org/command-new-format": "yes",
                    "toolforge": "tool",
                }
            },
            "spec": {
                "containers": [
                    {
                        "command": [
                            "/bin/sh",
                            "-c",
                            "--",
                            "exec 1>>/dev/null;exec 2>>/dev/null;./command-by-the-user.sh --with-args ; ./other-command.sh",  # noqa:E501
                        ],
                        "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd:latest",
                        "imagePullPolicy": "Always",
                        "name": "myjob",
                        "workingDir": "/data/project/test",
                    }
                ],
            },
        },
    },
}

JOB_CONT_NO_EMAILS_YES_FILELOG_NEW_ARRAY = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "annotations": {"deployment.kubernetes.io/revision": "1"},
        "labels": {
            "app.kubernetes.io/component": "deployments",
            "app.kubernetes.io/created-by": "test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "myjob",
            "app.kubernetes.io/version": "1",
            "jobs.toolforge.org/emails": "none",
            "jobs.toolforge.org/filelog": "yes",
            "jobs.toolforge.org/command-new-format": "yes",
            "toolforge": "tool",
        },
        "name": "myjob",
        "namespace": "test-tool",
    },
    "spec": {
        "selector": {
            "matchLabels": {
                "app.kubernetes.io/component": "deployments",
                "app.kubernetes.io/created-by": "test",
                "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                "app.kubernetes.io/name": "myjob",
                "app.kubernetes.io/version": "1",
                "jobs.toolforge.org/emails": "none",
                "jobs.toolforge.org/filelog": "yes",
                "jobs.toolforge.org/command-new-format": "yes",
                "toolforge": "tool",
            }
        },
        "template": {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/component": "deployments",
                    "app.kubernetes.io/created-by": "test",
                    "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                    "app.kubernetes.io/name": "myjob",
                    "app.kubernetes.io/version": "1",
                    "jobs.toolforge.org/emails": "none",
                    "jobs.toolforge.org/filelog": "yes",
                    "jobs.toolforge.org/command-new-format": "yes",
                    "toolforge": "tool",
                }
            },
            "spec": {
                "containers": [
                    {
                        "command": [
                            "/bin/sh",
                            "-c",
                            "--",
                            "exec 1>>myjob.out;exec 2>>myjob.err;./command-by-the-user.sh --with-args ; ./other-command.sh",  # noqa:E501
                        ],
                        "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd:latest",
                        "imagePullPolicy": "Always",
                        "name": "myjob",
                        "workingDir": "/data/project/test",
                    }
                ],
            },
        },
    },
}
JOB_CONT_NO_EMAILS_YES_FILELOG_CUSTOM_STDOUT = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "annotations": {"deployment.kubernetes.io/revision": "1"},
        "labels": {
            "app.kubernetes.io/component": "deployments",
            "app.kubernetes.io/created-by": "test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "myjob",
            "app.kubernetes.io/version": "1",
            "jobs.toolforge.org/emails": "none",
            "jobs.toolforge.org/filelog": "yes",
            "jobs.toolforge.org/command-new-format": "yes",
            "toolforge": "tool",
        },
        "name": "myjob",
        "namespace": "test-tool",
    },
    "spec": {
        "selector": {
            "matchLabels": {
                "app.kubernetes.io/component": "deployments",
                "app.kubernetes.io/created-by": "test",
                "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                "app.kubernetes.io/name": "myjob",
                "app.kubernetes.io/version": "1",
                "jobs.toolforge.org/emails": "none",
                "jobs.toolforge.org/filelog": "yes",
                "jobs.toolforge.org/command-new-format": "yes",
                "toolforge": "tool",
            }
        },
        "template": {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/component": "deployments",
                    "app.kubernetes.io/created-by": "test",
                    "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                    "app.kubernetes.io/name": "myjob",
                    "app.kubernetes.io/version": "1",
                    "jobs.toolforge.org/emails": "none",
                    "jobs.toolforge.org/filelog": "yes",
                    "jobs.toolforge.org/command-new-format": "yes",
                    "toolforge": "tool",
                }
            },
            "spec": {
                "containers": [
                    {
                        "command": [
                            "/bin/sh",
                            "-c",
                            "--",
                            "exec 1>>/data/project/test/logs/myjob.log;exec 2>>myjob.err;./command-by-the-user.sh --with-args",  # noqa:E501
                        ],
                        "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd:latest",
                        "imagePullPolicy": "Always",
                        "name": "myjob",
                        "workingDir": "/data/project/test",
                    }
                ],
            },
        },
    },
}
JOB_CONT_NO_EMAILS_YES_FILELOG_CUSTOM_STDOUT_STDERR = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "annotations": {"deployment.kubernetes.io/revision": "1"},
        "labels": {
            "app.kubernetes.io/component": "deployments",
            "app.kubernetes.io/created-by": "test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "myjob",
            "app.kubernetes.io/version": "1",
            "jobs.toolforge.org/emails": "none",
            "jobs.toolforge.org/filelog": "yes",
            "jobs.toolforge.org/command-new-format": "yes",
            "toolforge": "tool",
        },
        "name": "myjob",
        "namespace": "test-tool",
    },
    "spec": {
        "selector": {
            "matchLabels": {
                "app.kubernetes.io/component": "deployments",
                "app.kubernetes.io/created-by": "test",
                "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                "app.kubernetes.io/name": "myjob",
                "app.kubernetes.io/version": "1",
                "jobs.toolforge.org/emails": "none",
                "jobs.toolforge.org/filelog": "yes",
                "jobs.toolforge.org/command-new-format": "yes",
                "toolforge": "tool",
            }
        },
        "template": {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/component": "deployments",
                    "app.kubernetes.io/created-by": "test",
                    "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                    "app.kubernetes.io/name": "myjob",
                    "app.kubernetes.io/version": "1",
                    "jobs.toolforge.org/emails": "none",
                    "jobs.toolforge.org/filelog": "yes",
                    "jobs.toolforge.org/command-new-format": "yes",
                    "toolforge": "tool",
                }
            },
            "spec": {
                "containers": [
                    {
                        "command": [
                            "/bin/sh",
                            "-c",
                            "--",
                            "exec 1>>/dev/null;exec 2>>logs/customlog.err;./command-by-the-user.sh --with-args",  # noqa:E501
                        ],
                        "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd:latest",
                        "imagePullPolicy": "Always",
                        "name": "myjob",
                        "workingDir": "/data/project/test",
                    }
                ],
            },
        },
    },
}
