from a3m.api.transferservice import v1beta1 as transfer_service_api

DEFAULT_PROCESSING_CONFIG = transfer_service_api.request_response_pb2.ProcessingConfig(
    assign_uuids_to_directories=True,
    examine_contents=False,
    generate_transfer_structure_report=True,
    document_empty_directories=True,
    extract_packages=True,
    delete_packages_after_extraction=False,
    identify_transfer=True,
    identify_submission_and_metadata=True,
    identify_before_normalization=True,
    normalize=True,
    transcribe_files=True,
    perform_policy_checks_on_originals=True,
    perform_policy_checks_on_preservation_derivatives=True,
    aip_compression_level=1,
    aip_compression_algorithm=transfer_service_api.request_response_pb2.ProcessingConfig.AIP_COMPRESSION_ALGORITHM_S7_COPY,
)
