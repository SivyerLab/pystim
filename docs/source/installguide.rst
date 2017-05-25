Install walkthrough
===================

The following instructions are for Windows machines. The instructions are mostly similar for OSX, except for the
wxpython install. See the wxpython site for details.

Setting up environment
----------------------

The following walkthrough uses Anaconda, a Python environment manager. Unless otherwise noted, leave options as defaults.

Enter lines of code in the terminal/command line. To open the terminal command prompt, hit
windows + r, and enter "cmd". **NOTE** to paste text copied from this guide into the terminal
command: use mouse right click and paste. Ctrl + v will not work.

1. Install `Anaconda <https://www.continuum.io/anaconda-overview>`_ (environment manager) for python 3.6 to your user folder
2. Install `Git <https://git-scm.com/downloads>`_ (version control tool)
3. Create the python environment for the pyStim by entering the following text into the terminal command. ::

    conda create -y -n sp_env python=2.7

4. Activate the newly created environment by entering the following code: (**NOTE** You know you will have successfully created and entered the environment when it prefixes the current path). ::

    activate sp_env

.. image:: ../screenshots/cmd_4.jpg
    :width: 600 px

5. Install the packages included with conda: (**NOTE** this may take ~5 min, wait while the underscore is blinking). ::

    conda install -y numpy scipy Pillow matplotlib pandas pyopengl lxml openpyxl configobj sortedcontainers

6. Install the packages not included with conda. If you run into any problems here, simply close the command window, reopen it then reactivate the env. ::

    pip install tabulate igor tqdm moviepy pyglet psychopy labjackpython

7. Install wxpython (gui interface). ::

    conda install -y -c anaconda wxpython=3.0.0.0

8. Navigate to where you want to save the pyStim repository. ::

    cd C:/your/location/of/choice

For example C:/Users/bensivyer/PycharmProjects

To copy the path location: go to your desired folder in Windows and click to the right of the foldername in the search bar
and simply paste this text after "cd" in the terminal command

.. image:: ../screenshots/Copy_directory_path.jpg
    :width: 800 px
.. image:: ../screenshots/Terminal_command.jpg
    :width: 800 px

9. Download the repository (a new repositry folder will be automatically created). ::

    git clone https://github.com/awctomlinson/StimulusProgram.git

10. Navigate into the pyStim folder and code folder. ::

        cd pyStim/pyStim

11. Make necessary changes to psychopy source in "\\Anaconda3\\envs\\sp_env\\Lib\\site-packages\\psychopy\\visual\\window.py". If you are having trouble finding the "Anaconda3" folder,
it is usually either in "C:\\ProgramData" or your user folder. You can open "window.py" in any basic text editor. Line 297 needs to be changed from:

    .. code-block:: python
      :lineno-start: 297

      if self.viewOri is not 0. and self.viewPos is not None:

    to the following:

    .. code-block:: python
       :lineno-start: 297

       if self.viewOri != 0. and self.viewPos is not None:


12. Run the pyStim GUI. ::

        python pyStimGUI.py

13. If want to trigger an external device using a labjack install the labjack driver from the labjack site: `Labjack driver instructions <https://labjack.com/support/software/examples/ud/labjackpython>`_

To use the video saving function (i.e. to make an example video for a talk), install `ffmpeg <https://ffmpeg.org/>`_.