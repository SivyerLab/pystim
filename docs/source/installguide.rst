Install walkthrough
===================

The following instructions are for Windows machines. The instructions are mostly similar for OSX/Linux. If you run into
a problem with installing wxPython, please see the wxPython `website <https://www.wxpython.org/>`_ for help.

Installing PyStim
*****************
The following walkthrough uses Anaconda, an all in one Python environment manager. Unless otherwise noted, leave options
during install as defaults.

Enter lines of code in the terminal/command line. To open the command prompt, hit Windows + r, and type "cmd".


**NOTE:** to paste text copied from this guide into the terminal command: use mouse right click and paste. Ctrl + v will
not work.

#. Install `Miniconda`_. Two important options during install must be adhered to: Check the option to add conda to
   your PATH environment variable, and select the option to install conda only for the local user, NOT all users.

#. Install `Git`_ (version control tool). Make sure to select the option to add git to your PATH variable
   ("Git from the command line and also from 3rd-party software").

#. Navigate to where you want to install the pyStim repository (ex: C:/Users/sivyer/stimulus_software): ::

    cd "C:/Users/sivyer/stimulus_software"

#. Download the repository (a new folder called pystim will be automatically created): ::

    git clone https://github.com/SivyerLab/pystim.git

#. Create a conda environment from the included environment file: ::

    cd pystim
    conda env create -f environment.yml
    
#. Activate the environment. You should see `(pystim)` prepend lines on the command prompt after this: ::

    conda activate pystim

#. (OPTIONAL) If you wish to be able to save captures of your stims, install `ffmpeg`_.

#. (OPTIONAL) If you wish to be able to playback movies, install `avbin`_.

#. Run the pyStim GUI. ::

    python pyStim/pyStimGUI.py

.. _Miniconda: https://docs.conda.io/en/latest/miniconda.html
.. _Git: https://git-scm.com/downloads
.. _avbin: http://avbin.github.io/AVbin/Download.html
.. _ffmpeg: https://www.ffmpeg.org/
.. _labjack website: https://labjack.com/support/software/examples/ud/labjackpython
.. _pycrafter4500: https://github.com/SivyerLab/pyCrafter4500
