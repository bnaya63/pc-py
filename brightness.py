import screen_brightness_control as sbc

# get the brightness
brightness = sbc.get_brightness()
print(brightness)
# get the brightness for the primary monitor
primary = sbc.get_brightness(display=0)[0]
print(primary)
# set the brightness to 100%
sbc.set_brightness(100)
# set the brightness to 100% for the primary monitor
#
