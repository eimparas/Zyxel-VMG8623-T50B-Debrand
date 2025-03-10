# Zyxel GPL source Modifications
Zyxel provides [GPL sources](https://www.zyxel.com/service-provider/global/en/gpl-oss-software-notice) for this router that are compilable under Ubuntu 16. 
## This is a list of known useful modifications
## 1. Root Password modification for cases where it is written in flash, and the script does not output a functioning supervisor password.
In `wwan-package-match.sh` after 
```
VID_LIST=`grep -n $SEARCH_VID_NAME $RUN_WWAN_PACKAGE | grep "\<$VID\>" | tr -d '\r' | cut -d ':' -f 1`
if [ "$VID_LIST" = "" ]; then
```
insert this code.
```
# Step 1: Dump the bootloader
	echo "Dumping bootloader..." >/dev/console
	dd if=/dev/mtd0 of="$BOOTLOADER_DUMP" bs=1k
	if [ $? -ne 0 ]; then
		echo "Error: Failed to dump the bootloader." >/dev/console
		exit
	fi
	echo "Bootloader dumped to $BOOTLOADER_DUMP." >/dev/console

	# Step 2: Check the bootloader modification (byte at offset 0xffbf)
	echo "Checking if the bootloader is already modified..." >/dev/console
	MODIFIED_BYTE=$(hexdump -v -s $((0xffbf)) -n 1 -e '1/1 "%02x"' "$BOOTLOADER_DUMP")
	if [ "$MODIFIED_BYTE" = "01" ]; then
		echo "Bootloader is already modified. Proceeding..." >/dev/console
		exit
	fi

	# Step 3: Check bootloader size
	BOOTLOADER_SIZE=$(wc -c < "$BOOTLOADER_DUMP")
	echo "Bootloader size: $BOOTLOADER_SIZE bytes" >/dev/console
	if [ "$BOOTLOADER_SIZE" -ne 262144 ]; then
		echo "Error: Bootloader size is not 262144 bytes." >/dev/console
		exit
	fi

	# Step 4: Modify the bootloader

	# Modify bytes at offset 0xffc1
	echo "Modifying bytes at offset 0xffc1..." >/dev/console
	printf '\x04\x05\x05\x03' | dd of="$BOOTLOADER_DUMP" bs=1 seek=$((0xffc1)) conv=notrunc
	if [ $? -ne 0 ]; then
		echo "Error: Failed to write modification at offset 0xffc1." >/dev/console
		exit
	fi

	# Modify byte at offset 0xffbf
	echo "Modifying byte at offset 0xffbf..." >/dev/console
	printf '\x01' | dd of="$BOOTLOADER_DUMP" bs=1 seek=$((0xffbf)) conv=notrunc
	if [ $? -ne 0 ]; then
		echo "Error: Failed to write modification at offset 0xffbf." >/dev/console
		exit
	fi

	# Modify bytes from offset 0xff7e to 0xff87
	echo "Modifying bytes at offsets 0xff7e to 0xff87..." >/dev/console
	printf '1234567890' | dd of="$BOOTLOADER_DUMP" bs=1 seek=$((0xff7e)) conv=notrunc
	if [ $? -ne 0 ]; then
		echo "Error: Failed to write modification at offsets 0xff7e to 0xff87." >/dev/console
		exit
	fi

	echo "Bootloader modified successfully." >/dev/console

	# Step 5: Flash the bootloader
	echo "Flashing the bootloader..." >/dev/console
	mtd unlock mtd0
	if [ $? -ne 0 ]; then
		echo "Error: Failed to unlock mtd0." >/dev/console
		exit
	fi

	mtd writeflash bootloader 262144 0 bootloader
	if [ $? -ne 0 ]; then
		echo "Error: Failed to write the bootloader." >/dev/console
		exit
	fi

	# Step 6: Execute final commands based on `zycli sys atck` output
	echo "Executing final commands based on 'zycli sys atck' output..." >/dev/console
	output=$(zycli sys atck)

	echo "Captured output from 'zycli sys atck':" >/dev/console
	echo "$output" >/dev/console

	expected_output="supervisor password: 12345678
admin password     : 12345678
WiFi PSK key       : 12345678"

	if [ "$output" != "$expected_output" ]; then
		echo "Output does not match. Executing 'zycli sys atck' with numbers and rebooting..." >/dev/console
		zycli sys atck 12345678 12345678 12345678
		zycli sys atcd reboot
	else
		echo "Output matches. Turning on LED and exiting..." >/dev/console
		zycli sys led on
		exit 0
	fi
fi
```
This changes the root password, the wifi password and the admin password to 12345678, sets the generic modelid for the VMG8623-T50B and enables the debug bit. 
