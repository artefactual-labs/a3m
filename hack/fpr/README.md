## Import FPR dataset from Archivematica

Generate a dump:

    manage.py dumpdata --format=json fpr

Remove unused models:

    jq --sort-keys --indent 4 '[.[] | select(.model == "fpr.format" or .model == "fpr.formatgroup" or .model == "fpr.formatversion" or .model == "fpr.fpcommand" or .model == "fpr.fprule" or .model == "fpr.fptool")]' fpr-dumpdata.json > output.json

Replace the dataset:

    mv output.json ../../a3m/fpr/migrations/initial-data.json

From the root directory, run the registry sanity checks:

    pytest tests/test_registry.py

Based on the validation issues reported, fix as needed. In the latest update,
the following issues were repoted and the corresponding rules were disabled:

    Rule in service 3a19de70-0e42-4145-976b-3a248d43b462 is using a Command not in service: <a3m.fpr.registry.Command object at 0x7f4d55684250> (FITS).
    Rule in service 20cad741-3cf1-4b6a-9e71-d1e8af13ba3f is using a FormatVersion not in service: <a3m.fpr.registry.FormatVersion object at 0x7f3761395150> (Advanced Forensic Format).
    Rule in service 9e502f30-ba01-4981-8377-dd01ecf2dc5c is using a FormatVersion not in service: <a3m.fpr.registry.FormatVersion object at 0x7fbe6e2b9c10> (Advanced Forensic Format).

Also, make sure that the fiwalk command is not using a ficonfig file.
