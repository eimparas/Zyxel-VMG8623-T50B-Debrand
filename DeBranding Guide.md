# Zyxel VMG8623-T50B DeBranding
> A guide to debrand (remove ISP firmware & locked bootloader) the Zyxel VMG8623-T50B router

## Tools required 
- A Linux machine(or a machine that can ssh into the router)


# Step 0 (Pre-Requisites)

## 1. Obtain the root password for your device 

Use the password generator in the ZyxelRoot.py file (Execute it online [Here](https://www.onlinegdb.com/XR_spa_we)) to generate the device's root password for the zycli shell, accessible from both SSH & serial TTL. 

## 2. Connect to the device 

This operation will be done from ssh.
Using the serial header  can give you a better picture of the state of the device since it outputs bootloader & other debug messages, but it is not required. 
```
ssh -oHostKeyAlgorithms=+ssh-dss root@192.168.1.254
``` 


The stock device reports `zycli sys atsh` as following: 

```
Firmware Version        : V[version in the x.xx format](A[branch].[some revision])[higher level revision]
Bootbase Version        : V[version] | [date{
Vendor Name             : Zyxel Communications Corp.
Product Model           : VMG8623-T50B
Serial Number           : S220Y10021864
First MAC Address       : macaddress
Last MAC Address        : macaddress+0xf
MAC Address Quantity    : 16
Default Country Code    : (country code)
Boot Module Debug Flag  : 00
Kernel Checksum         : 68A00776
RootFS Checksum         : EB4B7592
Romfile Checksum        : 00000F7B
Main Feature Bits       : 00
Other Feature Bits      :
7f9ca5d2: 04050f0d 00000100 00000000 00000000
7f9ca5e2: 00000000 00000000 00000000
```

On [this](https://github.com/AgostinoA/OpenWrt-ZyXEL-VMG8825-T50/blob/main/stock/V5.50(ABOM.3)C0/docs_zyxel/Zyxel_Model_ID_and_Firmware_version.xlsx) xlsx file from the OpenWrt-ZyXEL-VMG8825-T50 project we see that there is a Model with an ID that corresponds to 0x45FD

|Model ID|	Project|	Notes |
|-|-|-|
|0x45FD|	VMG8623-T50B WindGreece|	EN7516+256MB RAM|

This happens to have very similar specs (SoC & ram capacity) with the _VMG8623-T50B Generic_ whose model ID is `0x4553`, shared with `EMG5523-T50A Generic`.

While Investigating the firmware available on [zyxel's website](https://www.zyxel.com/global/en/support/download?model=vmg3625-t50b) we find out that `04 05 05 03` with a hex encoding is found in what looks to be a file header on the ABPM branch.
therefore, changing the ModelID is  possible. Lets do it then 


# Step 1 (Unlocking the bootloader)

## 1. Dump The bootloader 

Knowing that the bootloader used mtd0 we can dump it using the following command

```
dd if=/dev/mtd0 of=/home/root/bootloader
```
We now have saved the bootloader in `/home/root/bootloader` as _bootloader_ .

## 3. Patch the bootloader 

Validate that you have the correct file and the offsets are correct. The router provides a hexdump utility that can be used for that.(note that we use ffd0 not because thats the true offset but because we want the hexdump to provide the ModelID first for this guide's easy use)
```
hexdump -C bootloader | grep -B 1 -A 1 "ffd0"
```
Confirm the output starts as following
```
0000ffc0  00 04 05 0f 0d 00 00 00  00 00 00 00 00 00 00 00  |................|

```

Edit the byte sequence : `04 05 0F 0D` at offset `0000FFC0` (on my bootloader , yours might be different, if it is search it using hexdump -C bootloader | grep -i -A 5 "04 05 0F 0D"
) To `04 05 05 03`,with the following command
```
printf '\x04\x05\x05\x03' | dd of=bootloader bs=1 seek=$((0xffc1)) conv=notrunc
```
You should also consider enabling the debug bit while you're doing it to gain access to all the bootloader commands and all zycli commands and some wifi calibration commands too
```
printf '\x01' | dd of=bootloader bs=1 seek=$((0xffc7)) conv=notrunc
```
 After all that assuming that all went well and we did enable the debug bit the output should be as following from the following command
```
hexdump -C bootloader | grep -B 1 -A 1 "ffd0"
```
Confirm the output starts as following
```
0000ffc0  00 04 05 05 03 00 00 01  00 00 00 00 00 00 00 00  |................|
```
If you followed the exact steps you should be safe but to prevent the router from dying one last measure you can take is to check the bootloader file has the right size.
```
wc -c bootloader
```
The output should be as follows
```
262144 bootloader
```
If both the previous steps are complete then we are ready to flash the file using the following commands
```
mtd unlock
mtd writeflash bootloader 262144 0 bootloader
zycli sys atcd
reboot
```


# Step 2  (Flashing Stock Firmware)

After a reboot we see that we can update the firmware using [Zyxel's official downloads](https://www.zyxel.com/global/en/support/download?model=vmg3625-t50b)

After that we flash the firmware [at https://192.168.1.254/FirmwareUpgrade)](https://192.168.1.254/FirmwareUpgrade) checking the "Reset All Settings After Firmware Upgrade" option

After flashing the firmware the device will change IP from `192.168.1.254` to `192.168.1.1` , you can login as a admin with the password written in the label
or as a supervisor using the password from the ZyxelRoot.py

Now you own a device that can , from now on ,be updated using the web Ui and is basically indistinguishable in all terms other than the Serial Number being marked as an ISP device from a Generic Device.
