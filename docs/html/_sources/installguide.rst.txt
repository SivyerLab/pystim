Install walkthrough
===================

Setting up environment
----------------------

`Anaconda <https://www.continuum.io/anaconda-overview>`_ is a great package manager that will make setting up the
environment to run pyStim much simpler. The following walkthrough uses Anaconda, and lines of code are to be
entered in the terminal/command line.

1. Install Anaconda (environment manager)
2. Install `Git <https://git-scm.com/downloads>`_ (version control tool)
3. Create the python environment for the pyStim::

    conda create -y --name sp_env python=2.7

4. Activate the newly created environment::

    activate sp_env

5. Install the packages that are necessary and included with conda (may take a bit and look like nothing is happening as the end, just be patient)::

    conda install -y numpy scipy Pillow matplotlib pandas pyopengl lxml openpyxl configobj sortedcontainers

6. Install the packages that are necessary and not included with conda::

    pip install tabulate igor tqdm moviepy pyglet psychopy labjackpython

7. Install wxpython (gui interface)::

    conda install -y -c anaconda wxpython=3.0.0.0

8. Navigate to where you want to save the pyStim repository::

    cd C:/your/location/of/choice

9. Download the repository (a new folder will be automatically created for it)::

    git clone https://github.com/awctomlinson/StimulusProgram.git

10. Navigate into the pyStim folder::

        cd StimulusProgram

11. Navigate into the code folder::

        cd pyStim

12. Make necessary changes to psychopy source in "\\Anaconda3\\envs\\pyStim\\Lib\\site-packages\\psychopy\\visual". Line 297 needs to be changed to::

        if self.viewOri != 0. and self.viewPos is not None:

13. Run the pyStim::

        python pyStimGUI.py

14. If want triggering, install the labjack driver from the labjack site. If want video saving, install ffmpeg.
