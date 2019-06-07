# Minimal Myro

- supports interaction with [scribbler robots](http://www.betterbots.com/) (with and without fluke1/fluke2)
- only depends on pyserial and PIL for pictures: `takePicture()` & `savePicture()`
- no GUI 
- should work with python3 & python2 (`pip install future`)
- preliminary `takePicture()` support for the Raspberry Pi Camera: `init('pi')`
 -- `pip install picamera`
  


```
cd mmyro 
pip install .

-or-

pip install Pillow
pip install pyserial
python setup.py install
```

