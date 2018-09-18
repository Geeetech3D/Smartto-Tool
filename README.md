## Smartto Tool

### Where I can find the latest version of firmware
You can find all firmwares from our [file server](http://geeetech.com/firmware/)

The changelog about firmwares located in [smartto-iar project](https://github.com/Geeetech3D/Smartto-IAR/tree/master/log/firmware_changelog.md)

### Which application should I use to upgrade the printer

We will put the executions in applications/

If your OS is Win*, you should download the zip package whose name take "forWin" as a suffix. Firmware one for upgrading your machine and motor one for motor parameters adjustment.

If your OS is Mac*, you can download the whole .app folder and run it directly in your OS X.(Make sure your OS X version 10.13+ )

The changelog about firmwares located [here](https://github.com/Geeetech3D/Smartto-Tool/blob/master/CHANGELOG.md)

### About Upgrading

Usually, user improves machine's mainboard first and then upgrades LCD screen(if exists)

**Attention1**: Character 'S' in name of bin file(such as A30_APP_S_V1.38.61.bin) means "Slave Device" and 'M' for "Master Device.(Maybe it's a very old naming error) \
**Attention2**: Make sure your SD card has been inserted before upgrading.

### Preview and Usage

#### Firmware tool

<div align=center><img src="https://raw.githubusercontent.com/geeetech3d/smartto-tool/master/docs/assets/local_upgrading.gif" alt="firmware-tool-usage1" /></div>
<div align=center><img src="https://raw.githubusercontent.com/geeetech3d/smartto-tool/master/docs/assets/remote_upgrading.gif" alt="firmware-tool-usage2" /></div>

**Attention**: Remote upgrading only upgrade your mainboard. You can access the folder "{ROOT}/Firmware/extract/"(*.app/Contents/Resources/Firmware/extract/ in Mac version) to find your target firmware file

#### Motor tool

<div align=center><img src="https://raw.githubusercontent.com/geeetech3d/smartto-tool/master/docs/assets/motor.gif" alt="motor-tool-usage" /></div>

