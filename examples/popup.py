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


# ########################### - Main logic - ##################################
# Declare the Screen Stack Manager
screen = pssm.PSSMScreen(device, 'Main')
# Clear and refresh the screen
screen.clear()
screen.refresh()
# Now to initialize the keybaord
screen.OSKInit(area=None)


if __name__ == "__main__":
    # Start Touch listener, as a separate thread
    screen.startListenerThread(grabInput=True)


    myPopup = pssm.PoputInput(
        titleText="Title",
        titleFont=pssm.DEFAULT_FONTBOLD,
        titleFontSize="H*0.04",
        mainText=lorem,
        mainFontSize="H*0.02",
        inputFontSize="H*0.025"
    )
    screen.addElt(myPopup)
    user_input = myPopup.waitForResponse()  # This will wait for user response

    confirmPopup = pssm.PopupConfirm(
        titleText="Title",
        titleFont=pssm.DEFAULT_FONTBOLD,
        titleFontSize="H*0.04",
        mainText=lorem,
        mainFontSize="H*0.02"
    )
    screen.addElt(confirmPopup)
    user_confirm = confirmPopup.waitForResponse()

    text = "User typed : \n \n " + str(user_input) + "\n \n \n" + str(user_confirm)
    myButton  = pssm.Button(text=text,area=screen.area)
    screen.addElt(myButton)

    screen.device.startMainLoop()
