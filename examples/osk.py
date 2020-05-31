#!/usr/bin/env python
import sys
sys.path.append("../")
import pssm
import platform
if platform.machine() in ["x86", "AMD64", "i686", "x86_64"]:
    device = "Emulator"
else:
    device = "Kobo"


lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras "\
        "placerat diam at leo blandit vulputate. Donec rutrum feugiat sapien,"\
        " sed volutpat quam facilisis eu. Vestibulum ante ipsum primis in "\
        "faucibus orci luctus et ultrices posuere cubilia curae; "\
        "Cras vel augue vitae dolor placerat tincidunt ac ut turpis."

# Declare the Screen Stack Manager
screen = pssm.PSSMScreen(device, 'Main')


# ########################### - Main logic - ##################################
def main():
    # Clear and refresh the screen
    screen.clear()
    screen.refresh()
    # Now to initialize the keybaord
    screen.OSKInit(area=None)
    # Start Touch listener, as a separate thread
    screen.startListenerThread(grabInput=True)

    inputText = pssm.Input(
        text=lorem,
        outline_color="black",
        text_xPosition="left",
        text_yPosition="top"
    )
    mainLayout_array = [
        ["p*20"],
        ["H*0.62", (None, "p*5"), (inputText, "?"), (None, "p*5")]
    ]
    mainLayout = pssm.Layout(mainLayout_array, screen.area)
    screen.addElt(mainLayout)


if __name__ == "__main__":
    main()
    if device == "Emulator":
        # only necessary for the emulator, and must be at the very end
        screen.device.startMainLoop()
