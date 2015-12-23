import os, sys
import numpy, scipy

if sys.platform=='win32':
    from distutils.core import setup
    import py2exe

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
                 ("psychopy\\stims", stim_files), ('psychopy', ini_file)]

    setup(console=['gui.py'],
          data_files=all_files,
          windows= [
              {
                  'script' : 'gui.py',
                  'icon_resources' : [(1, 'icon1.ico')]
              }
          ],
          options={
              'py2exe': {
                  # need all these or building fails
                  'includes' : ['scipy.*', 'scipy.integrate', 'scipy.special.*',
                                'scipy.linalg.*', 'scipy.integrate',
                                'scipy.sparse.csgraph._validation',
                                'multiprocessing', 'PIL.*',
                                'psychopy.visual.*']
              }
          })

elif sys.platform=='darwin':
    from setuptools import setup
    import py2app

    pref_files = []
    app_files = []
    stim_files = []

    ini_file = ["./psychopy/config.ini"]

    for files in os.listdir("./psychopy/stims/"):
        f1 = "./psychopy/stims/" + files
        stim_files.append(f1)

    for files in os.listdir('/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/psychopy/preferences/'):
        f1 = '/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/psychopy/preferences/' + files
        pref_files.append(f1)

    all_files = [("psychopy/preferences", pref_files),
                 ("psychopy/stims", stim_files), ('psychopy', ini_file)]

    setup(app=['gui.py'],
          setup_requires=['py2app'],
          data_files=all_files,
          options={
              'py2app': {
                  'packages' : ['PIL'],
                  'includes' : ['scipy.*', 'scipy.integrate', 'scipy.special.*',
                                'scipy.linalg.*', 'scipy.integrate',
                                'scipy.sparse.csgraph._validation',
                                'multiprocessing',
                                'psychopy.visual.*']
              }
          })