Feature: Create preservation packages through the command line
  Scenario: Preserve and normalize a local JPEG 2000 image
    Given a local JPEG 2000 image with spaces in its name
    When I ingest it with the a3m command
    Then the command succeeds
    And one valid BagIt AIP contains the unchanged original
    And the AIP contains a TIFF preservation copy
    And METS records both files with fixity and a normalization event

  Scenario: Reject a missing local source
    Given a local source that does not exist
    When I ingest it with the a3m command
    Then the command fails
    And no completed AIP is produced

  Scenario: Store a preservation package in S3
    Given a local JPEG 2000 image with spaces in its name
    And an empty S3 bucket
    When I ingest it with the a3m command
    Then the command succeeds
    And S3 stores the complete AIP under its package identifier
    And one valid BagIt AIP contains the unchanged original
    And the AIP contains a TIFF preservation copy
    And METS records both files with fixity and a normalization event
