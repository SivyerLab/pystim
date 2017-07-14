conda create -y -n test_env python=2.7
call activate test_env
cmd /c "conda install -y numpy scipy Pillow matplotlib pandas pyopengl lxml openpyxl configobj sortedcontainers"
pip install tabulate igor tqdm moviepy pyglet psychopy labjackpython pyusb pycrafter4500
cmd /c "conda install -y -c anaconda wxpython=3.0.0.0"
cmd /c "conda install -y -c conda-forge ffmpeg=3.2.4"

@echo off 
set /p FOL=enter pystim desired install directory (create first): 
@echo on

cd %FOL%
git clone https://github.com/SivyerLab/pystim.git

cd pyStim/pyStim
python pyStimGUI.py