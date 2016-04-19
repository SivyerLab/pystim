#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

"""
Py2exe/py2app setup script. Depending on the OS, the executables fail to
build without the modules added to 'includes'. This clutters the folder in
the dist for windows, but at least it works. Icon inclusion seems buggy as well.

Script uses py2exe/py2app to include the psychopy/preferences folder,
but cannot include the psychopy/app folder because it contains subfolders.
Console commands are used to copy those. User should still check that those
are included, or else the GUI will fail to start (psychopy checks that folder
for user preferences, and throws an error if it can't find all the values for
it's default dictionary.
"""

import os, sys, py_compile
import numpy, scipy

def setup():
    if sys.platform=='win32':
        from distutils.core import setup
        import py2exe
        import ctypes

        pref_files = []
        app_files = []
        stim_files = []

        ini_file = [".\\psychopy\\config.ini"]

        for files in os.listdir(".\\psychopy\\stims\\"):
            f1 = ".\\psychopy\\stims\\" + files
            stim_files.append(f1)

        for files in os.listdir('C:\\Python27\\Lib\\site-packages\\psychopy'
                                '\\preferences\\'):
            f1 = 'C:\\Python27\\Lib\\site-packages\\psychopy\\preferences\\' + files
            pref_files.append(f1)

        all_files = [("psychopy\\preferences", pref_files),
                     ("psychopy\\stims", stim_files),
                     ('psychopy', ini_file)]

        setup(console=['GUI.py'],
              data_files=all_files,
              windows= [
                  {
                      'script' : 'GUI.py',
                      # 'icon_resources' : [(1, 'icon1.ico')]
                  }
              ],
              options={
                  'py2exe': {
                      # need all these or building fails
                      'includes' : ['scipy.*', 'scipy.integrate', 'scipy.special.*',
                                    'scipy.linalg.*', 'scipy.integrate',
                                    'scipy.sparse.csgraph._validation',
                                    'multiprocessing', 'PIL.*',
                                    'psychopy.visual.*', 'matplotlib.afm']
                  }
              })

        os.system('start robocopy "C:\Python27\Lib\site-packages\psychopy\\app" '
                  '".\dist\psychopy\\app" /E')
        py_compile.compile('GammaCorrection.py', cfile='.\dist\GammaCorrection.pyc')

    elif sys.platform=='darwin':
        from setuptools import setup
        import py2app

        pref_files = []
        app_files = []
        stim_files = []

        helper_files = ["./psychopy/config.ini", "./psychopy/gammaTables.txt"]

        for files in os.listdir("./psychopy/stims/"):
            f1 = "./psychopy/stims/" + files
            stim_files.append(f1)

        for files in os.listdir('/Library/Frameworks/Python.framework/Versions/2.7/'
                                'lib/python2.7/site-packages/psychopy/preferences/'):
            f1 = '/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7' \
                 '/site-packages/psychopy/preferences/' + files
            pref_files.append(f1)

        all_files = [("psychopy/preferences", pref_files),
                     ("psychopy/stims", stim_files), ('psychopy', helper_files)]

        setup(app=['GUI.py'],
              setup_requires=['py2app'],
              data_files=all_files,
              options={
                  'py2app': {
                      'packages' : ['PIL'],
                      # 'iconfile' : 'icon1.ico',
                      'includes' : ['scipy.*', 'scipy.integrate',
                                    'scipy.special.*', 'scipy.linalg.*',
                                    'scipy.integrate',
                                    'scipy.sparse.csgraph._validation',
                                    'multiprocessing', 'psychopy.visual.*',
                                    'matplotlib.afm']
                  }
              })

        os.system('cp -r /Library/Frameworks/Python.framework/Versions/2.7/lib'
                  '/python2.7/site-packages/psychopy/app '
                  './dist/gui.app/Contents/Resources/psychopy/app/')
        py_compile.compile('GammaCorrection.py', cfile='./dist/gui.app/Contents/Resources/GammaCorrection.pyc')


if __name__ == '__main__':
    setup()