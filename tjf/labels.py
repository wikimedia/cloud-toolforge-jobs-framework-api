def labels(jobname: str, username: str, type: str):
    obj = {
        "toolforge": "tool",
        "app.kubernetes.io/version": "1",
        "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
        "app.kubernetes.io/created-by": username,
    }

    if type is not None:
        obj["app.kubernetes.io/component"] = type

    if jobname is not None:
        obj["app.kubernetes.io/name"] = jobname

    return obj


def labels_selector(jobname: str, username: str, type: str):
    return ",".join(
        ["{k}={v}".format(k=k, v=v) for k, v in labels(jobname, username, type).items()]
    )
