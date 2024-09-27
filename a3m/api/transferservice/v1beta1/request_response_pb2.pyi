from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class PackageStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PACKAGE_STATUS_UNSPECIFIED: _ClassVar[PackageStatus]
    PACKAGE_STATUS_FAILED: _ClassVar[PackageStatus]
    PACKAGE_STATUS_REJECTED: _ClassVar[PackageStatus]
    PACKAGE_STATUS_COMPLETE: _ClassVar[PackageStatus]
    PACKAGE_STATUS_PROCESSING: _ClassVar[PackageStatus]

PACKAGE_STATUS_UNSPECIFIED: PackageStatus
PACKAGE_STATUS_FAILED: PackageStatus
PACKAGE_STATUS_REJECTED: PackageStatus
PACKAGE_STATUS_COMPLETE: PackageStatus
PACKAGE_STATUS_PROCESSING: PackageStatus

class SubmitRequest(_message.Message):
    __slots__ = ("name", "url", "config")
    NAME_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    name: str
    url: str
    config: ProcessingConfig
    def __init__(
        self,
        name: _Optional[str] = ...,
        url: _Optional[str] = ...,
        config: _Optional[_Union[ProcessingConfig, _Mapping]] = ...,
    ) -> None: ...

class SubmitResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ReadRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class ReadResponse(_message.Message):
    __slots__ = ("status", "job", "jobs")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    JOB_FIELD_NUMBER: _ClassVar[int]
    JOBS_FIELD_NUMBER: _ClassVar[int]
    status: PackageStatus
    job: str
    jobs: _containers.RepeatedCompositeFieldContainer[Job]
    def __init__(
        self,
        status: _Optional[_Union[PackageStatus, str]] = ...,
        job: _Optional[str] = ...,
        jobs: _Optional[_Iterable[_Union[Job, _Mapping]]] = ...,
    ) -> None: ...

class ListTasksRequest(_message.Message):
    __slots__ = ("job_id",)
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    job_id: str
    def __init__(self, job_id: _Optional[str] = ...) -> None: ...

class ListTasksResponse(_message.Message):
    __slots__ = ("tasks",)
    TASKS_FIELD_NUMBER: _ClassVar[int]
    tasks: _containers.RepeatedCompositeFieldContainer[Task]
    def __init__(
        self, tasks: _Optional[_Iterable[_Union[Task, _Mapping]]] = ...
    ) -> None: ...

class EmptyRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class EmptyResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Job(_message.Message):
    __slots__ = ("id", "name", "group", "link_id", "status", "start_time")
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATUS_UNSPECIFIED: _ClassVar[Job.Status]
        STATUS_COMPLETE: _ClassVar[Job.Status]
        STATUS_PROCESSING: _ClassVar[Job.Status]
        STATUS_FAILED: _ClassVar[Job.Status]

    STATUS_UNSPECIFIED: Job.Status
    STATUS_COMPLETE: Job.Status
    STATUS_PROCESSING: Job.Status
    STATUS_FAILED: Job.Status
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    GROUP_FIELD_NUMBER: _ClassVar[int]
    LINK_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    group: str
    link_id: str
    status: Job.Status
    start_time: _timestamp_pb2.Timestamp
    def __init__(
        self,
        id: _Optional[str] = ...,
        name: _Optional[str] = ...,
        group: _Optional[str] = ...,
        link_id: _Optional[str] = ...,
        status: _Optional[_Union[Job.Status, str]] = ...,
        start_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
    ) -> None: ...

class Task(_message.Message):
    __slots__ = (
        "id",
        "file_id",
        "exit_code",
        "filename",
        "execution",
        "arguments",
        "stdout",
        "stderr",
        "start_time",
        "end_time",
    )
    ID_FIELD_NUMBER: _ClassVar[int]
    FILE_ID_FIELD_NUMBER: _ClassVar[int]
    EXIT_CODE_FIELD_NUMBER: _ClassVar[int]
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_FIELD_NUMBER: _ClassVar[int]
    ARGUMENTS_FIELD_NUMBER: _ClassVar[int]
    STDOUT_FIELD_NUMBER: _ClassVar[int]
    STDERR_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    id: str
    file_id: str
    exit_code: int
    filename: str
    execution: str
    arguments: str
    stdout: str
    stderr: str
    start_time: _timestamp_pb2.Timestamp
    end_time: _timestamp_pb2.Timestamp
    def __init__(
        self,
        id: _Optional[str] = ...,
        file_id: _Optional[str] = ...,
        exit_code: _Optional[int] = ...,
        filename: _Optional[str] = ...,
        execution: _Optional[str] = ...,
        arguments: _Optional[str] = ...,
        stdout: _Optional[str] = ...,
        stderr: _Optional[str] = ...,
        start_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        end_time: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
    ) -> None: ...

class ProcessingConfig(_message.Message):
    __slots__ = (
        "assign_uuids_to_directories",
        "examine_contents",
        "generate_transfer_structure_report",
        "document_empty_directories",
        "extract_packages",
        "delete_packages_after_extraction",
        "identify_transfer",
        "identify_submission_and_metadata",
        "identify_before_normalization",
        "normalize",
        "transcribe_files",
        "perform_policy_checks_on_originals",
        "perform_policy_checks_on_preservation_derivatives",
        "aip_compression_level",
        "aip_compression_algorithm",
    )
    class AIPCompressionAlgorithm(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        AIP_COMPRESSION_ALGORITHM_UNSPECIFIED: _ClassVar[
            ProcessingConfig.AIPCompressionAlgorithm
        ]
        AIP_COMPRESSION_ALGORITHM_UNCOMPRESSED: _ClassVar[
            ProcessingConfig.AIPCompressionAlgorithm
        ]
        AIP_COMPRESSION_ALGORITHM_TAR: _ClassVar[
            ProcessingConfig.AIPCompressionAlgorithm
        ]
        AIP_COMPRESSION_ALGORITHM_TAR_BZIP2: _ClassVar[
            ProcessingConfig.AIPCompressionAlgorithm
        ]
        AIP_COMPRESSION_ALGORITHM_TAR_GZIP: _ClassVar[
            ProcessingConfig.AIPCompressionAlgorithm
        ]
        AIP_COMPRESSION_ALGORITHM_S7_COPY: _ClassVar[
            ProcessingConfig.AIPCompressionAlgorithm
        ]
        AIP_COMPRESSION_ALGORITHM_S7_BZIP2: _ClassVar[
            ProcessingConfig.AIPCompressionAlgorithm
        ]
        AIP_COMPRESSION_ALGORITHM_S7_LZMA: _ClassVar[
            ProcessingConfig.AIPCompressionAlgorithm
        ]

    AIP_COMPRESSION_ALGORITHM_UNSPECIFIED: ProcessingConfig.AIPCompressionAlgorithm
    AIP_COMPRESSION_ALGORITHM_UNCOMPRESSED: ProcessingConfig.AIPCompressionAlgorithm
    AIP_COMPRESSION_ALGORITHM_TAR: ProcessingConfig.AIPCompressionAlgorithm
    AIP_COMPRESSION_ALGORITHM_TAR_BZIP2: ProcessingConfig.AIPCompressionAlgorithm
    AIP_COMPRESSION_ALGORITHM_TAR_GZIP: ProcessingConfig.AIPCompressionAlgorithm
    AIP_COMPRESSION_ALGORITHM_S7_COPY: ProcessingConfig.AIPCompressionAlgorithm
    AIP_COMPRESSION_ALGORITHM_S7_BZIP2: ProcessingConfig.AIPCompressionAlgorithm
    AIP_COMPRESSION_ALGORITHM_S7_LZMA: ProcessingConfig.AIPCompressionAlgorithm
    ASSIGN_UUIDS_TO_DIRECTORIES_FIELD_NUMBER: _ClassVar[int]
    EXAMINE_CONTENTS_FIELD_NUMBER: _ClassVar[int]
    GENERATE_TRANSFER_STRUCTURE_REPORT_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_EMPTY_DIRECTORIES_FIELD_NUMBER: _ClassVar[int]
    EXTRACT_PACKAGES_FIELD_NUMBER: _ClassVar[int]
    DELETE_PACKAGES_AFTER_EXTRACTION_FIELD_NUMBER: _ClassVar[int]
    IDENTIFY_TRANSFER_FIELD_NUMBER: _ClassVar[int]
    IDENTIFY_SUBMISSION_AND_METADATA_FIELD_NUMBER: _ClassVar[int]
    IDENTIFY_BEFORE_NORMALIZATION_FIELD_NUMBER: _ClassVar[int]
    NORMALIZE_FIELD_NUMBER: _ClassVar[int]
    TRANSCRIBE_FILES_FIELD_NUMBER: _ClassVar[int]
    PERFORM_POLICY_CHECKS_ON_ORIGINALS_FIELD_NUMBER: _ClassVar[int]
    PERFORM_POLICY_CHECKS_ON_PRESERVATION_DERIVATIVES_FIELD_NUMBER: _ClassVar[int]
    AIP_COMPRESSION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    AIP_COMPRESSION_ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    assign_uuids_to_directories: bool
    examine_contents: bool
    generate_transfer_structure_report: bool
    document_empty_directories: bool
    extract_packages: bool
    delete_packages_after_extraction: bool
    identify_transfer: bool
    identify_submission_and_metadata: bool
    identify_before_normalization: bool
    normalize: bool
    transcribe_files: bool
    perform_policy_checks_on_originals: bool
    perform_policy_checks_on_preservation_derivatives: bool
    aip_compression_level: int
    aip_compression_algorithm: ProcessingConfig.AIPCompressionAlgorithm
    def __init__(
        self,
        assign_uuids_to_directories: bool = ...,
        examine_contents: bool = ...,
        generate_transfer_structure_report: bool = ...,
        document_empty_directories: bool = ...,
        extract_packages: bool = ...,
        delete_packages_after_extraction: bool = ...,
        identify_transfer: bool = ...,
        identify_submission_and_metadata: bool = ...,
        identify_before_normalization: bool = ...,
        normalize: bool = ...,
        transcribe_files: bool = ...,
        perform_policy_checks_on_originals: bool = ...,
        perform_policy_checks_on_preservation_derivatives: bool = ...,
        aip_compression_level: _Optional[int] = ...,
        aip_compression_algorithm: _Optional[
            _Union[ProcessingConfig.AIPCompressionAlgorithm, str]
        ] = ...,
    ) -> None: ...
