Detailed install instructions
=============================

Python and required dependencies
--------------------------------

pyStim is created and tested using Python 2.7.10 on both Windows and OSX. pyStim is
not supported on Python 3 because of incompatible dependencies.

pyStim requires the following dependencies(found in ``requirements.txt``):

- psychopy (see psychopy `documentation <http://www.psychopy.org/documentation.html>`_ for required `dependencies <http://www.psychopy.org/installation.html#essential-packages>`_).
- `wxPython <http://www.wxpython.org/download.php)>`_
- pyglet
- sortedcontainers
- numpy
- scipy
- PIL (use Pillow)
- tqdm

Optional libraries:

- tabulate (for formatting logs)
- igor (for parsing igor tables)
- `u3 <https://labjack.com/support/software/examples/ud/labjackpython>`_ (for triggering from LabJack)
- `ffmpeg <https://www.ffmpeg.org/>`_ (for making movies from captured frames)

All of the above can be installed through pip, except for ``wxPython``,
``ffmpeg``, and ``u3``. These need to be installed from their respective
websites.

pip will occasionally fail to build some libraries on Windows machines. Compiled
versions of these binaries can be found `here <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_.
Or preferrably use a package manager like `Anaconda <https://www.continuum.io/anaconda-overview>`_.


Psychopy source changes
-----------------------

The following changes to the psychopy source code (version 1.84.2) are
required to run the application. This has been fixed for subsequent
releases. Psychopy source can be found in the python site-packages folder.

1. In order to allow simultaneous offsetting and scaling of the pyglet
   window, line 297 in::

    /psychopy/visual/window.py

   need to be changed to the following:

   .. code-block:: python
      :lineno-start: 297

      if self.viewOri != 0. and self.viewPos is not None:


2. TODO: small window changes (small window not vsynced)