What is it?
-----------

Stimulus Program uses the `Psychopy <www.psychopy.org>`_ library to create
visual stimuli for use in a range of visual neuroscience experiments. It
includes a GUI for ease of use. The program is capable of running at a
minimum of 60 fps for moderately sized stimuli and triggering recording devices
(using a LabJack U3).

Latest Version
--------------

The latest version can be found in the master branch on GitHub. The dev 
branch is experimental, but will usually contain new features and be mostly
functional.

Documentation
-------------

Documentation is included in HTML format in the docs/html/ directory. A
version is available on github pages `here <http://sivyerlab.github.io/pystim/>`_. Further
documentation on Psychopy can be found on the psychopy `website <www.psychopy.org>`_.

Quick Install
-------------

pyStim is tested and works on both OSX and Windows. It does
not work with Python 3, due to incompatible dependencies. Stimulus Program
requires several libraries, along with their associated dependencies, to run.
They are listed below:

- psychopy (see psychopy `documentation <http://www.psychopy.org/documentation.html>`_ for required `dependencies <http://www.psychopy.org/installation.html#essential-packages>`_).
- sortedcontainers (available through pip)
- `wxPython <http://www.wxpython.org/download.php>`_ (for GUI)

Optional libraries:

- tabulate (for formatting logs)
- igor (for parsing tables)
- `u3 <https://labjack.com/support/software/examples/ud/labjackpython>`_ (for triggering from LabJack)
- `ffmpeg <https://www.ffmpeg.org/>`_ (for making movies from captured frames)

Psychopy requires some small editing to source for it to work as of version 1.84.2 (fixed on current master on github).
See docs for detailed instructions. An install walkthrough is also available in the requirements file.

Licensing
---------

pyStim is licensed under GNU GPL v3.0. See :doc:`license <LICENSE>`
for license rights and limitations.

Screen Shots
------------

Screenshots are available in the /docs/screenshots/ folder.

.. image:: ../screenshots/screens.gif