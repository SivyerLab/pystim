![travis] ![coveralls]

What is it?
===========

pyStim uses the [Psychopy] library to create visual stimuli for use in
our visual neuroscience experiments. It includes a graphic user
interface and is capable of running at a minimum of 60 frames/sec and
with the Texas Instruments LightCrafter 4500 DLP is capable of running
in excess of 180 Hz. pyStim is designed to communicate with exterinal
I/O devices (currently Labjack U3), which we use to trigger the
aquisition of recording amplifiers.

Latest Version
==============

The latest version can be found in the master branch on GitHub. The dev
branch is experimental, but will usually contain new features and be
mostly functional.

Documentation
=============

Documentation is available on github pages [ghpages]. The source of the
documentation can be found in the code and in the /docs/source/ folder.
Further documentation on Psychopy can be found on the psychopy
[website][Psychopy].

Quick Install
=============

pyStim is tested and works on Windows, though it should work on
OSX/Linux (successfully builds on Travis).

1.  Clone the repository:

	```bash
	git clone https://github.com/SivyerLab/pystim.git
	```

2.  Install pipenv:

	```
	pip install pipenv
	```

3.  Create the python environment for pystim and automatically install
    all the necessary packages:

	```
    pipenv install --skip-lock
	```

4.  Run the GUI:

	```
	pipenv run python pyStim/pyStimGUI.py
	```

Optional libraries:

-   pycrafter4500 (for control of a lightcrafter 4500)
-   tabulate (for formatting logs)
-   igor (for parsing tables)
-   labjackpython (see install guide for details)
-   [ffmpeg] (for generating movies)

Licensing
=========

pyStim is licensed under GNU GPL v3.0. See [LICENSE] for license rights and
limitations.

Screenshots
===========

Screenshots are available in the /docs/screenshots/ folder.

![screenshot]

  [travis]: https://travis-ci.org/SivyerLab/pystim.svg?branch=master
  [coveralls]: https://coveralls.io/repos/github/SivyerLab/pystim/badge.svg?branch=master
  [Psychopy]: http://www.psychopy.org
  [ghpages]: https://sivyerlab.github.io/pystim/
  [ffmpeg]: https://www.ffmpeg.org/
  [LICENSE]: http://www.gnu.org/copyleft/gpl.html
  [screenshot]: https://raw.githubusercontent.com/SivyerLab/pystim/master/docs/screenshots/screens.gif