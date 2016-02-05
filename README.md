## Stimulus Program

### What is it?

Stimulus Program uses the [Psychopy](www.psychopy.org) library to create
various visual stimuli for use with patch clamp retinal cells. It comes with 
a GUI for ease of use. The program is capable of running at 60 fps and 
triggering recording devices (using a LabJack U3). The GUI uses wx, and so 
appears with a native theme.

### Latest Version

The latest version can be found in the master branch on GitHub. The dev 
branch is experimental, but will usually  contain new features and be mostly
functional.

### Documentation

Documentation is included in HTML format the docs/html/ directory. Further
documentation on Psychopy can be found at www.psychopy.org.

### Installation

Stimulus Program is tested and works on both OSX and Windows. Stimulus
Program requires several libraries, along with their associated dependencies,
to run. They are listed below:

- psychopy (see psychopy [documentation](http://www.psychopy.org/documentation.html) 
for required [dependencies](http://www.psychopy.org/installation.html#essential-packages))
- wxPython (for GUI)

Optional libraries:

- tabulate (for formatting logs)
- igor (for parsing tables)
- [u3](https://labjack.com/support/software/examples/ud/labjackpython) (for 
triggering from LabJack)

### Licensing

Stimulus Program is licensed under GNU GPL v3.0. See [LICENSE](LICENSE.md)
file for license rights and limitations.

### Screen Shots (Windows 7)

Main screen:

![main screen](docs/screenshots/screen1.PNG)

Stims to run:

![stims added](docs/screenshots/screen3.PNG)

Example stimulus:

![example](docs/screenshots/screen4.PNG)