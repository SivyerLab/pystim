Install walkthrough
===================

The following instructions are for Windows machines. The instructions are mostly similar for OSX/Linux. If you run into
a problem with installing wxPython, please see the wxPython `website <https://www.wxpython.org/>`_ for help.

Installing PyStim
*****************
The following walkthrough uses pipenv, an all in one Python environment manager. Unless otherwise noted, leave options
during install as defaults.

Enter lines of code in the terminal/command line. To open the terminal/command prompt, hit windows + r, and enter "cmd".
|
**NOTE** to paste text copied from this guide into the terminal command: use mouse right click and paste. Ctrl + v will
not work.

#. Install `Python 3.6`_. Make sure to select the option to add Python to your PATH variable.

#. Install `Git`_ (version control tool). Make sure to select the option to add git to your PATH variable
   ("Run Git from Windows Command Prompt").

#. Navigate to where you want to install the pyStim repository (ex: C:/Users/bensivyer/stimulus_software): ::

    cd "C:/Users/bensivyer/stimulus_software"

#. Download the repository (a new folder called pystim will be automatically created): ::

    git clone https://github.com/SivyerLab/pystim.git

#. Install pipenv: ::

    pip install pipenv
    
#. Enter the pystim directory: ::

    cd pystim

#. Create the python environment for pystim and automatically install all the necessary packages by entering the
   following text into the terminal command. ::

    pipenv install --skip-lock

#. (OPTIONAL) If you wish to be able to save captures of your stims, install `ffmpeg`_.

#. (OPTIONAL) If you wish to be able to playback movies, install `avbin`_.

#. (OPTIONAL) If needing to trigger an external device using a labjack install the labjack "UD driver" from the
   `labjack website`_. Then install the labjack package: ::

    pipenv run pip install git+https://github.com/labjack/LabJackPython.git

#. Run the pyStim GUI. ::

    pipenv run python pyStim/pyStimGUI.py

.. _Python 3.6: https://www.python.org/downloads/
.. _Git: https://git-scm.com/downloads
.. _avbin: http://avbin.github.io/AVbin/Download.html
.. _ffmpeg: https://www.ffmpeg.org/
.. _labjack website: https://labjack.com/support/software/examples/ud/labjackpython
