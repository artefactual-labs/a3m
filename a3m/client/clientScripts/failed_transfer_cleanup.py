from a3m.client import metrics


FAILED = "fail"


def call(jobs):
    # Transfer UUID can be found in sys.args[1] but it is currently unused.
    job = jobs[0]
    with job.JobContext():
        metrics.transfer_failed(FAILED)
        job.set_status(0)
