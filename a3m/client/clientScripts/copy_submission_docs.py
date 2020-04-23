import os

from a3m.executeOrRunSubProcess import executeOrRun


def call(jobs):
    for job in jobs:
        with job.JobContext():
            sip_dir = job.args[1]
            sip_name = job.args[2]

            source_dir = os.path.join(
                sip_dir, sip_name, "data", "objects", "submissionDocumentation"
            )
            submission_docs_dir = os.path.join(sip_dir, "submissionDocumentation")

            os.makedirs(submission_docs_dir, mode=0o770, exist_ok=True)

            exit_code, std_out, std_error = executeOrRun(
                "command",
                ["cp", "-R", source_dir, submission_docs_dir],
                capture_output=True,
            )

            job.write_error(std_error)
            job.write_output(std_out)
            job.set_status(exit_code)
