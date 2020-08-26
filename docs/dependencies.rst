Dependencies
============

a3m has many dependencies that need to be available in the system path. Some
examples are Siegfried, Unar or FFmpeg. Our :ref:`Docker <docker>` image
includes these dependences so you don't have to install them.

In some cases, you may still prefer to install them manually, e.g. during
development or when Docker is not at reach. Here are some examples valid for
an Ubuntu/Debian Linux environment:

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
