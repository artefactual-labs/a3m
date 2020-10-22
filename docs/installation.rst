============
Installation
============

a3m is available in PyPI, a software repository for Python projects::

    pip install a3m

We also publish a Docker image that bundles all software dependencies that a3m
needs for a good out-of-box experience. This image is public and can be pulled
from the command line with::

	docker pull ghcr.io/artefactual-labs/a3m:main

If you don't want to use Docker, it is still possible to run a3m successfully
as long as the software dependencies are provided in some other way. Please
continue reading.

Dependencies
============

We don't have a comprehensive list of software dependencies yet or mechanisms
to manage them dynamically. For the time being, here are some examples valid
for an Ubuntu/Debian Linux environment:

`Siegfried <https://www.itforarchivists.com/siegfried>`_::

    wget -qO - https://bintray.com/user/downloadSubjectPublicKey?username=bintray | sudo apt-key add -
    echo "deb http://dl.bintray.com/siegfried/debian wheezy main" | sudo tee -a /etc/apt/sources.list
    sudo apt-get update && sudo apt-get install siegfried

`Unar <https://software.opensuse.org/package/unar>`_::

    sudo apt-get install unar

`FFmpeg (ffprobe) <https://ffmpeg.org/ffprobe.html>`_::

    sudo apt-get install ffmpeg

`ExifTool <https://exiftool.org>`_::

    wget https://packages.archivematica.org/1.11.x/ubuntu-externals/pool/main/libi/libimage-exiftool-perl/libimage-exiftool-perl_10.10-2~14.04_all.deb`
    sudo dkpg -i libimage-exiftool-perl_10.10-2~14.04_all.deb

`MediaInfo <https://mediaarea.net/en/MediaInfo>`_::

    sudo apt-get install mediainfo

`Sleuth Kit (fiwalk) <https://sleuthkit.org/>`_::

    sudo apt-get install sleuthkit

`JHOVE <https://jhove.openpreservation.org/>`_::

    sudo apt-get ca-certificates-java java-common openjdk-8-jre-headless
    wget https://packages.archivematica.org/1.11.x/ubuntu-externals/pool/main/j/jhove/jhove_1.20.1-6~18.04_all.deb
    sudo dpkg -i jhove_1.20.1-6~18.04_all.deb

`7-Zip <https://www.7-zip.org/>`_::

    sudo apt-get install pzip-full

`atool <https://www.nongnu.org/atool/>`_::

    sudo apt-get install atool

`test <https://www.gnu.org/software/coreutils/coreutils.html>`_::

    sudo apt-get install coreutils
