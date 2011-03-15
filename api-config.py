import os


def cpus():
    if not hasattr(os, "sysconf"):
        raise RuntimeError("No sysconf detected.")

    return os.sysconf("SC_NPROCESSORS_ONLN")


bind = "0.0.0.0:8000"
workers = cpus() * 2 + 1
