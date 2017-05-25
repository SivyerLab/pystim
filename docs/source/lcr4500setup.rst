LCR 4500 quick setup
====================

Instructions for 180 hz stimuli

Description
-----------
Using the framepacking capabilities of the lightcrafter 4500, we are able to display stimuli at speeds greater than 60 hz. This is done by replacing the individual RGB planes of a single frame with 3 separate monochrome frames, thus tripling the effective frames per second coming out the projector.

Requirements
------------
* `DLP LightCrafter 4500 Development Module <http://www.ti.com/tool/dlplcr4500evm>`_ (LCR 4500)
* Power supply for LCR 4500 (`recommended <https://www.digikey.com/product-detail/en/CENB1060A1203F01/271-2718-ND/2533054>`_)
* Appropriate connectors:
    * Male mini USB to male USB
    * Male mini HDMI to male HDMI
* Computer with sufficient CPU/GPU specs
* LCR 4500 GUI (available from the LCR 4500 page above)
* Stimulus software (`pyStim <https://github.com/SivyerLab/pyStim>`_)

Instructions
------------
1. Connect the LCR 4500 to the power supply. It should power on and start working.
2. Connect the USB and HDMI inputs between the computer and LCR.
3. Install the LCR 4500 GUI and run it. The GUI should find and connect to the LCR automatically.
4. Set the resolution of the LCR to 912 x 1140, with the frequency set to 60 hz.
5. In the GUI, change the LCR to pattern sequence mode, and set up a pattern sequence with the parameters from screenshot below.
6. Press “Send”, then “Validate”, then “Play”. The LCR 4500 should now be unpacking each frame into three separate monochrome frames, running at 180 hz.

.. image:: ..\screenshots\lcr4500_180_setup.PNG