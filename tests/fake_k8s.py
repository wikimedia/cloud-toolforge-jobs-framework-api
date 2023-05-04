from typing import Optional

from tjf.job import JOB_DEFAULT_CPU, JOB_DEFAULT_MEMORY


FAKE_IMAGE_CONFIG = """
bullseye:
  state: stable
  variants:
    jobs-framework:
      image: docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd
node12:
  aliases:
  - tf-node12
  - tf-node12-DEPRECATED
  state: deprecated
  variants:
    jobs-framework:
      image: docker-registry.tools.wmflabs.org/toolforge-node12-sssd-base
    webservice:
      image: docker-registry.tools.wmflabs.org/toolforge-node12-sssd-web
node16:
  aliases:
  - tf-node16
  state: stable
  variants:
    jobs-framework:
      image: docker-registry.tools.wmflabs.org/toolforge-node16-sssd-base
    webservice:
      image: docker-registry.tools.wmflabs.org/toolforge-node16-sssd-web
php7.3:
  aliases:
  - tf-php73
  - tf-php73-DEPRECATED
  state: deprecated
  variants:
    jobs-framework:
      image: docker-registry.tools.wmflabs.org/toolforge-php73-sssd-base
    webservice:
      image: docker-registry.tools.wmflabs.org/toolforge-php73-sssd-web
php7.4:
  aliases:
  - tf-php74
  state: stable
  variants:
    jobs-framework:
      image: docker-registry.tools.wmflabs.org/toolforge-php74-sssd-base
    webservice:
      image: docker-registry.tools.wmflabs.org/toolforge-php74-sssd-web
"""

FAKE_HARBOR_HOST = "harbor.example.org"

CRONJOB_NOT_RUN_YET = {
    "apiVersion": "batch/v1",
    "kind": "CronJob",
    "metadata": {
        "creationTimestamp": "2023-04-13T14:51:55Z",
        "generation": 1,
        "labels": {
            "app.kubernetes.io/component": "cronjobs",
            "app.kubernetes.io/created-by": "tf-test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "test",
            "app.kubernetes.io/version": "1",
            "jobs.toolforge.org/command-new-format": "yes",
            "jobs.toolforge.org/emails": "none",
            "jobs.toolforge.org/filelog": "yes",
            "toolforge": "tool",
        },
        "name": "test",
        "namespace": "tool-tf-test",
        "resourceVersion": "11983",
        "uid": "0a818297-7959-42ff-a3b9-1e3ca74664ba",
    },
    "spec": {
        "concurrencyPolicy": "Forbid",
        "failedJobsHistoryLimit": 0,
        "jobTemplate": {
            "metadata": {"creationTimestamp": None},
            "spec": {
                "backoffLimit": 0,
                "template": {
                    "metadata": {
                        "creationTimestamp": None,
                        "labels": {
                            "app.kubernetes.io/component": "cronjobs",
                            "app.kubernetes.io/created-by": "tf-test",
                            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                            "app.kubernetes.io/name": "test",
                            "app.kubernetes.io/version": "1",
                            "jobs.toolforge.org/command-new-format": "yes",
                            "jobs.toolforge.org/emails": "none",
                            "jobs.toolforge.org/filelog": "yes",
                            "toolforge": "tool",
                        },
                    },
                    "spec": {
                        "containers": [
                            {
                                "command": [
                                    "/bin/sh",
                                    "-c",
                                    "--",
                                    "exec 1>>test.out;exec 2>>test.err;./restart.sh",
                                ],
                                "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd:latest",  # noqa:E501
                                "imagePullPolicy": "Always",
                                "name": "job",
                                "resources": {},
                                "terminationMessagePath": "/dev/termination-log",
                                "terminationMessagePolicy": "File",
                                "workingDir": "/data/project/tf-test",
                            }
                        ],
                        "dnsPolicy": "ClusterFirst",
                        "restartPolicy": "Never",
                        "schedulerName": "default-scheduler",
                        "securityContext": {},
                        "terminationGracePeriodSeconds": 30,
                    },
                },
                "ttlSecondsAfterFinished": 30,
            },
        },
        "schedule": "*/5 * * * *",
        "startingDeadlineSeconds": 30,
        "successfulJobsHistoryLimit": 0,
        "suspend": False,
    },
    "status": {},
}

CRONJOB_PREVIOUS_RUN_BUT_NO_RUNNING_JOB = {
    "apiVersion": "batch/v1",
    "kind": "CronJob",
    "metadata": {
        "creationTimestamp": "2023-04-13T14:51:55Z",
        "generation": 1,
        "labels": {
            "app.kubernetes.io/component": "cronjobs",
            "app.kubernetes.io/created-by": "tf-test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "test",
            "app.kubernetes.io/version": "1",
            "jobs.toolforge.org/command-new-format": "yes",
            "jobs.toolforge.org/emails": "none",
            "jobs.toolforge.org/filelog": "yes",
            "toolforge": "tool",
        },
        "name": "test",
        "namespace": "tool-tf-test",
        "resourceVersion": "11983",
        "uid": "0a818297-7959-42ff-a3b9-1e3ca74664ba",
    },
    "spec": {
        "concurrencyPolicy": "Forbid",
        "failedJobsHistoryLimit": 0,
        "jobTemplate": {
            "metadata": {"creationTimestamp": None},
            "spec": {
                "backoffLimit": 0,
                "template": {
                    "metadata": {
                        "creationTimestamp": None,
                        "labels": {
                            "app.kubernetes.io/component": "cronjobs",
                            "app.kubernetes.io/created-by": "tf-test",
                            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                            "app.kubernetes.io/name": "test",
                            "app.kubernetes.io/version": "1",
                            "jobs.toolforge.org/command-new-format": "yes",
                            "jobs.toolforge.org/emails": "none",
                            "jobs.toolforge.org/filelog": "yes",
                            "toolforge": "tool",
                        },
                    },
                    "spec": {
                        "containers": [
                            {
                                "command": [
                                    "/bin/sh",
                                    "-c",
                                    "--",
                                    "exec 1>>test.out;exec 2>>test.err;./restart.sh",
                                ],
                                "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd:latest",  # noqa:E501
                                "imagePullPolicy": "Always",
                                "name": "job",
                                "resources": {},
                                "terminationMessagePath": "/dev/termination-log",
                                "terminationMessagePolicy": "File",
                                "workingDir": "/data/project/tf-test",
                            }
                        ],
                        "dnsPolicy": "ClusterFirst",
                        "restartPolicy": "Never",
                        "schedulerName": "default-scheduler",
                        "securityContext": {},
                        "terminationGracePeriodSeconds": 30,
                    },
                },
                "ttlSecondsAfterFinished": 30,
            },
        },
        "schedule": "*/5 * * * *",
        "startingDeadlineSeconds": 30,
        "successfulJobsHistoryLimit": 0,
        "suspend": False,
    },
    "status": {"lastScheduleTime": "2023-04-13T14:55:00Z"},
}

CRONJOB_WITH_RUNNING_JOB = {
    "apiVersion": "batch/v1",
    "kind": "CronJob",
    "metadata": {
        "creationTimestamp": "2023-04-13T15:02:16Z",
        "generation": 1,
        "labels": {
            "app.kubernetes.io/component": "cronjobs",
            "app.kubernetes.io/created-by": "tf-test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "test",
            "app.kubernetes.io/version": "1",
            "jobs.toolforge.org/command-new-format": "yes",
            "jobs.toolforge.org/emails": "none",
            "jobs.toolforge.org/filelog": "yes",
            "toolforge": "tool",
        },
        "name": "test",
        "namespace": "tool-tf-test",
        "resourceVersion": "13099",
        "uid": "0a818297-7959-42ff-a3b9-1e3ca74664ba",
    },
    "spec": {
        "concurrencyPolicy": "Forbid",
        "failedJobsHistoryLimit": 0,
        "jobTemplate": {
            "metadata": {"creationTimestamp": None},
            "spec": {
                "backoffLimit": 0,
                "template": {
                    "metadata": {
                        "creationTimestamp": None,
                        "labels": {
                            "app.kubernetes.io/component": "cronjobs",
                            "app.kubernetes.io/created-by": "tf-test",
                            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                            "app.kubernetes.io/name": "test",
                            "app.kubernetes.io/version": "1",
                            "jobs.toolforge.org/command-new-format": "yes",
                            "jobs.toolforge.org/emails": "none",
                            "jobs.toolforge.org/filelog": "yes",
                            "toolforge": "tool",
                        },
                    },
                    "spec": {
                        "containers": [
                            {
                                "command": [
                                    "/bin/sh",
                                    "-c",
                                    "--",
                                    "exec 1>>test.out;exec 2>>test.err;./restart.sh",
                                ],
                                "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd:latest",  # noqa:E501
                                "imagePullPolicy": "Always",
                                "name": "job",
                                "resources": {},
                                "terminationMessagePath": "/dev/termination-log",
                                "terminationMessagePolicy": "File",
                                "workingDir": "/data/project/tf-test",
                            }
                        ],
                        "dnsPolicy": "ClusterFirst",
                        "restartPolicy": "Never",
                        "schedulerName": "default-scheduler",
                        "securityContext": {},
                        "terminationGracePeriodSeconds": 30,
                    },
                },
                "ttlSecondsAfterFinished": 30,
            },
        },
        "schedule": "*/5 * * * *",
        "startingDeadlineSeconds": 30,
        "successfulJobsHistoryLimit": 0,
        "suspend": False,
    },
    "status": {
        "active": [
            {
                "apiVersion": "batch/v1",
                "kind": "Job",
                "name": "test-28023305",
                "namespace": "tool-tf-test",
                "resourceVersion": "13097",
                "uid": "68936ba6-ae9b-4a7c-a614-54f200bc460a",
            }
        ],
        "lastScheduleTime": "2023-04-13T15:05:00Z",
    },
}

JOB_FROM_A_CRONJOB = {
    "apiVersion": "batch/v1",
    "kind": "Job",
    "metadata": {
        "creationTimestamp": "2023-04-13T15:05:00Z",
        "generation": 1,
        "labels": {
            "app.kubernetes.io/component": "cronjobs",
            "app.kubernetes.io/created-by": "tf-test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "test",
            "app.kubernetes.io/version": "1",
            "controller-uid": "68936ba6-ae9b-4a7c-a614-54f200bc460a",
            "job-name": "test-28023305",
            "jobs.toolforge.org/command-new-format": "yes",
            "jobs.toolforge.org/emails": "none",
            "jobs.toolforge.org/filelog": "yes",
            "toolforge": "tool",
        },
        "name": "test-28023305",
        "namespace": "tool-tf-test",
        "ownerReferences": [
            {
                "apiVersion": "batch/v1",
                "blockOwnerDeletion": True,
                "controller": True,
                "kind": "CronJob",
                "name": "test",
                "uid": "0a818297-7959-42ff-a3b9-1e3ca74664ba",
            }
        ],
        "resourceVersion": "13104",
        "uid": "68936ba6-ae9b-4a7c-a614-54f200bc460a",
    },
    "spec": {
        "backoffLimit": 0,
        "completionMode": "NonIndexed",
        "completions": 1,
        "parallelism": 1,
        "selector": {"matchLabels": {"controller-uid": "68936ba6-ae9b-4a7c-a614-54f200bc460a"}},
        "suspend": False,
        "template": {
            "metadata": {
                "creationTimestamp": None,
                "labels": {
                    "app.kubernetes.io/component": "cronjobs",
                    "app.kubernetes.io/created-by": "tf-test",
                    "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                    "app.kubernetes.io/name": "test",
                    "app.kubernetes.io/version": "1",
                    "controller-uid": "68936ba6-ae9b-4a7c-a614-54f200bc460a",
                    "job-name": "test-28023305",
                    "jobs.toolforge.org/command-new-format": "yes",
                    "jobs.toolforge.org/emails": "none",
                    "jobs.toolforge.org/filelog": "yes",
                    "toolforge": "tool",
                },
            },
            "spec": {
                "containers": [
                    {
                        "command": [
                            "/bin/sh",
                            "-c",
                            "--",
                            "exec 1>>test.out;exec 2>>test.err;./restart.sh",
                        ],
                        "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd:latest",
                        "imagePullPolicy": "Always",
                        "name": "job",
                        "resources": {},
                        "terminationMessagePath": "/dev/termination-log",
                        "terminationMessagePolicy": "File",
                        "workingDir": "/data/project/tf-test",
                    }
                ],
                "dnsPolicy": "ClusterFirst",
                "restartPolicy": "Never",
                "schedulerName": "default-scheduler",
                "securityContext": {},
                "terminationGracePeriodSeconds": 30,
            },
        },
        "ttlSecondsAfterFinished": 30,
    },
    "status": {"active": 1, "startTime": "2023-04-13T15:05:00Z"},
}

JOB_FROM_A_CRONJOB_RESTART = {
    "apiVersion": "batch/v1",
    "kind": "Job",
    "metadata": {
        "annotations": {"cronjob.kubernetes.io/instantiate": "manual"},
        "creationTimestamp": "2023-04-13T15:44:26Z",
        "generation": 1,
        "labels": {
            "app.kubernetes.io/component": "cronjobs",
            "app.kubernetes.io/created-by": "tf-test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "test",
            "app.kubernetes.io/version": "1",
            "jobs.toolforge.org/command-new-format": "yes",
            "jobs.toolforge.org/emails": "none",
            "jobs.toolforge.org/filelog": "yes",
            "toolforge": "tool",
        },
        "name": "test-1681400666",
        "namespace": "tool-tf-test",
        "ownerReferences": [
            {
                "apiVersion": "batch/v1",
                "kind": "CronJob",
                "name": "test",
                "uid": "0a818297-7959-42ff-a3b9-1e3ca74664ba",
            }
        ],
        "resourceVersion": "16491",
        "uid": "6c197474-ec58-4fd1-88cb-f1c8a93ce14d",
    },
    "spec": {
        "backoffLimit": 0,
        "completionMode": "NonIndexed",
        "completions": 1,
        "parallelism": 1,
        "selector": {"matchLabels": {"controller-uid": "6c197474-ec58-4fd1-88cb-f1c8a93ce14d"}},
        "suspend": False,
        "template": {
            "metadata": {
                "creationTimestamp": None,
                "labels": {
                    "app.kubernetes.io/component": "cronjobs",
                    "app.kubernetes.io/created-by": "tf-test",
                    "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
                    "app.kubernetes.io/name": "test",
                    "app.kubernetes.io/version": "1",
                    "controller-uid": "6c197474-ec58-4fd1-88cb-f1c8a93ce14d",
                    "job-name": "test-1681400666",
                    "jobs.toolforge.org/command-new-format": "yes",
                    "jobs.toolforge.org/emails": "none",
                    "jobs.toolforge.org/filelog": "yes",
                    "toolforge": "tool",
                },
            },
            "spec": {
                "containers": [
                    {
                        "command": [
                            "/bin/sh",
                            "-c",
                            "--",
                            "exec 1>>test.out;exec 2>>test.err;./restart.sh",
                        ],
                        "image": "docker-registry.tools.wmflabs.org/toolforge-bullseye-sssd:latest",
                        "imagePullPolicy": "Always",
                        "name": "job",
                        "resources": {
                            "limits": {"cpu": "500m", "memory": "512Mi"},
                            "requests": {"cpu": "250m", "memory": "268435456"},
                        },
                        "terminationMessagePath": "/dev/termination-log",
                        "terminationMessagePolicy": "File",
                        "workingDir": "/data/project/tf-test",
                    }
                ],
                "dnsPolicy": "ClusterFirst",
                "restartPolicy": "Never",
                "schedulerName": "default-scheduler",
                "securityContext": {},
                "terminationGracePeriodSeconds": 30,
            },
        },
        "ttlSecondsAfterFinished": 30,
    },
    "status": {"active": 1, "startTime": "2023-04-13T15:44:26Z"},
}


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

JOB_CONT_NO_EMAILS_NO_FILELOG_V2_ARRAY = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "annotations": {"deployment.kubernetes.io/revision": "1"},
        "labels": {
            "app.kubernetes.io/component": "deployments",
            "app.kubernetes.io/created-by": "test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "myjob",
            "app.kubernetes.io/version": "2",
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
                "app.kubernetes.io/version": "2",
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
                    "app.kubernetes.io/version": "2",
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
                            "./command-by-the-user.sh --with-args ; ./other-command.sh",  # noqa:E501
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

JOB_CONT_BUILDPACK_NO_EMAILS_ARRAY = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "annotations": {"deployment.kubernetes.io/revision": "1"},
        "labels": {
            "app.kubernetes.io/component": "deployments",
            "app.kubernetes.io/created-by": "test",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": "myjob",
            "app.kubernetes.io/version": "2",
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
                "app.kubernetes.io/version": "2",
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
                    "app.kubernetes.io/version": "2",
                    "jobs.toolforge.org/emails": "none",
                    "toolforge": "tool",
                }
            },
            "spec": {
                "containers": [
                    {
                        "command": ["cmdname"],
                        "arguments": ["with-arguments", "other argument with spaces"],
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


LIMIT_RANGE_OBJECT = {
    "apiVersion": "v1",
    "kind": "LimitRange",
    "metadata": {
        "name": "tool-test-tool",
        "namespace": "tool-test-tool",
    },
    "spec": {
        "limits": [
            {
                "type": "Container",
                "default": {
                    "cpu": "500m",
                    "memory": "512Mi",
                },
                "defaultRequest": {
                    "cpu": "150m",
                    "memory": "256Mi",
                },
                "max": {
                    "cpu": "1",
                    "memory": "4Gi",
                },
                "min": {
                    "cpu": "50m",
                    "memory": "100Mi",
                },
            }
        ]
    },
}


class FakeJob:
    def __init__(
        self,
        *,
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
    ) -> None:
        self.cpu = cpu or JOB_DEFAULT_CPU
        self.memory = memory or JOB_DEFAULT_MEMORY
