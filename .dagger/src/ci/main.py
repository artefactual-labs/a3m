"""Acceptance tests against the production a3m image."""

from typing import Annotated

import dagger
from dagger import DefaultPath
from dagger import Ignore
from dagger import dag
from dagger import function
from dagger import object_type

Source = Annotated[
    dagger.Directory,
    DefaultPath("acceptance"),
    Ignore([".venv", "__pycache__", ".pytest_cache", "reports"]),
]


@object_type
class Ci:
    def _argmin(self) -> dagger.Service:
        # Match the pinned Argmin build used by Enduro's acceptance harness.
        source = (
            dag.git("https://github.com/justincormack/argmin.git")
            .commit("8ebbf735460e1e6e38333571853b460c40d09879")
            .tree()
        )
        binary = (
            dag.container()
            .from_("rust:1.99.1-bookworm")
            .with_directory("/src", source)
            .with_workdir("/src")
            .with_mounted_cache(
                "/usr/local/cargo/registry", dag.cache_volume("argmin-cargo-registry")
            )
            .with_mounted_cache(
                "/usr/local/cargo/git", dag.cache_volume("argmin-cargo-git")
            )
            .with_mounted_cache(
                "/src/target",
                dag.cache_volume("argmin-cargo-target"),
                sharing=dagger.CacheSharingMode.LOCKED,
            )
            .with_exec(["cargo", "build", "--locked", "--release", "-p", "argmin-s3"])
            .with_exec(["install", "-D", "target/release/argmin-s3", "/out/argmin-s3"])
            .file("/out/argmin-s3")
        )
        return (
            dag.container()
            .from_("debian:bookworm-slim")
            .with_file("/usr/local/bin/argmin-s3", binary)
            .with_exec(["install", "-d", "-o", "1000", "-g", "1000", "/data"])
            .with_user("1000:1000")
            .with_env_variable("ARGMIN_ACCOUNT_ID", "111122223333")
            .with_env_variable("ARGMIN_ACCESS_KEY_ID", "acceptance")
            .with_env_variable("ARGMIN_SECRET_ACCESS_KEY", "acceptance-secret")
            # Test-only wrapping key; service data is ephemeral, never cached.
            .with_env_variable(
                "ARGMIN_SSE_S3_WRAPPING_KEY",
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
            )
            .with_env_variable("ARGMIN_REGION", "us-east-1")
            .with_env_variable("ARGMIN_DATA_DIR", "/data")
            .with_env_variable("ARGMIN_LISTEN_ADDR", "0.0.0.0:9000")
            .with_exposed_port(9000)
            .as_service(args=["argmin-s3"])
        )

    def _acceptance(
        self, source: dagger.Directory, image: dagger.File
    ) -> dagger.Container:
        # Keep the production build and its dependencies unchanged. Test tools
        # live in their own environment and invoke the installed a3m command.
        return (
            dag.container()
            .import_(image)
            .with_directory("/acceptance", source, owner="a3m")
            .with_workdir("/acceptance")
            .with_exec(
                [
                    "uv",
                    "sync",
                    "--locked",
                    "--no-dev",
                    "--python",
                    "/app/.venv/bin/python",
                ]
            )
            .with_env_variable("ACCEPTANCE_REPORTS", "/acceptance/reports")
            .with_service_binding("argmin", self._argmin())
            .with_env_variable("ACCEPTANCE_S3_ENDPOINT", "http://argmin:9000")
            .with_exec(
                [
                    "/acceptance/.venv/bin/pytest",
                    "-v",
                    "--junitxml=/acceptance/reports/junit.xml",
                ],
                expect=dagger.ReturnType.ANY,
            )
        )

    @function
    async def acceptance(self, image: dagger.File, source: Source) -> dagger.Directory:
        """Run CLI scenarios and export reports with pytest's exit-code.txt."""
        result = self._acceptance(source, image)
        exit_code = await result.exit_code()
        return (
            result.directory("/acceptance/reports")
            .with_new_file("exit-code.txt", f"{exit_code}\n")
            .with_new_file("pytest.log", await result.stdout() + await result.stderr())
        )
