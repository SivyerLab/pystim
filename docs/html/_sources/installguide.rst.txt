Install walkthrough
===================

The following instructions are for Windows machines. The instructions are mostly similar for OSX, except for the
wxpython install. See the wxpython site for details.

Setting up environment
----------------------

Anaconda is a great package manager that will make setting up the
environment to run pyStim much simpler. The following walkthrough uses Anaconda, and lines of code are to be
entered in the terminal/command line. Unless otherwise noted, leave options as defaults. To open command prompt, hit
windows + r, and enter "cmd". A quick of the command prompt: to paste, right click the mouse and paste instead of
doing ctrl + v.

1. Install `Anaconda <https://www.continuum.io/anaconda-overview>`_ (environment manager) for python 3.6 to your user folder
2. Install `Git <https://git-scm.com/downloads>`_ (version control tool)
3. Create the python environment for the pyStim. ::

    conda create -y -n sp_env python=2.7

4. Activate the newly created environment. You know you will have successfully created and entered the environment when it prefixes the current path. ::

    activate sp_env

.. image:: ..\screenshots\cmd_4.PNG

5. Install the packages that are necessary and included with conda (may take 4-5 min and look like nothing is happening as the end, just be patient while the cursor is blinking). ::

    conda install -y numpy scipy Pillow matplotlib pandas pyopengl lxml openpyxl configobj sortedcontainers

6. Install the packages that are necessary and not included with conda. If you run into any problems here, simply close the command window, reopen it then reactivate the env. ::

    pip install tabulate igor tqdm moviepy pyglet psychopy labjackpython

7. Install wxpython (gui interface). ::

    conda install -y -c anaconda wxpython=3.0.0.0

8. Navigate to where you want to save the pyStim repository. ::

    cd C:/your/location/of/choice

9. Download the repository (a new folder will be automatically created for it). ::

    git clone https://github.com/awctomlinson/StimulusProgram.git

10. Navigate into the pyStim folder. ::

        cd StimulusProgram

11. Navigate into the code folder. ::

        cd pyStim

12. Make necessary changes to psychopy source in "\\Anaconda3\\envs\\sp_env\\Lib\\site-packages\\psychopy\\visual\\window.py". If you are having trouble finding the "Anaconda3" folder, it is usually either in "C:\\ProgramData" or your user folder. You can open "window.py" in any basic text editor. Line 297 needs to be changed from:

    .. code-block:: python
      :lineno-start: 297

      if self.viewOri is not 0. and self.viewPos is not None:

    to the following:

    .. code-block:: python
       :lineno-start: 297

       if self.viewOri != 0. and self.viewPos is not None:


13. Run the pyStim GUI. ::

        python pyStimGUI.py

14. If want triggering, install the labjack driver from the labjack site. If want video saving, install ffmpeg.
