Changed
-------

Filename normalization now uses Unidecode 1.4. Some Unicode characters have
updated transliterations, such as ``℃`` becoming ``degC`` and ``Ŋ`` becoming
``NG``. Original filenames remain recorded in preservation metadata, and
colliding normalized names receive a numeric suffix.
