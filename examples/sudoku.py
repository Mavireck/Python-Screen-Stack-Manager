#!/usr/bin/env python
import sys
sys.path.append("../")
import os
import pssm
import platform
import random
if platform.machine() in ["x86", "AMD64", "i686", "x86_64"]:
    device = "Emulator"
else:
    device = "Kobo"

# ###################### - INIT - ###########################################
# Declare the Screen Stack Manager
screen = pssm.PSSMScreen(device, 'Main')
# Clear and refresh the screen
screen.clear()
screen.refresh()
# Now to initialize the keybaord
screen.OSKInit(area=None)

# Variables:
MARGIN = "H*0.0063"
BIG_MARGIN = "H*0.015"
ERROR_INVERT_DURATION = 1
cursor_position = None
elt_grid = [[None for j in range(9)] for i in range(9)]

# ###################### - SUDOKU LOGIC - ####################################
def isWrong(grid, pos, userInput):
    """
    Returns False if grid is valid, else (i, j) where (i, j) indicate the coords
    of the cell which the addition contradicts
    """
    (i0, j0) = pos
    current = grid[i0][j0]
    # In the same col?
    for i in range(9):
        if grid[i][j0] == current and i!=i0:
            return (i, j0)
    # In the same line?
    for j in range(9):
        if grid[i0][j] == current and j != j0:
            return (i0, j)
    # In the same square?
    for i in range(i0 - i0%3, i0 - i0%3 + 3):
        for j in range(j0 - j0%3, j0 - j0%3 + 3):
            if grid[i][j] == current and i != i0 and j != j0:
                return (i, j)
    return False


def generateSudokuGrid(numberOfCells):
    """
    https://stackoverflow.com/questions/45471152/how-to-create-a-sudoku-puzzle-in-python
    """
    if numberOfCells >= 81 or numberOfCells < 0:
        # Return empty grid
        return [["" for j in range(9)] for i in range(9)]
    # Create Board
    base  = 3
    side  = base*base
    # pattern for a baseline valid solution
    def pattern(r,c): return (base*(r%base)+r//base+c)%side
    # randomize rows, columns and numbers (of valid base pattern)
    from random import sample
    def shuffle(s): return sample(s,len(s))
    rBase = range(base)
    rows  = [ g*base + r for g in shuffle(rBase) for r in shuffle(rBase) ]
    cols  = [ g*base + c for g in shuffle(rBase) for c in shuffle(rBase) ]
    nums  = shuffle(range(1,base*base+1))
    # produce board using randomized baseline pattern
    board = [ [str(nums[pattern(r,c)]) for c in cols] for r in rows ]

    # THEN REMOVE 'numberOfCells' elements.
    indexesToKeep = []
    for i in range(9):
        for j in range(9):
            indexesToKeep.append((i,j))
    for n in range(numberOfCells):
        indexesToKeep.pop(random.randrange(len(indexesToKeep)))
    for (i,j) in indexesToKeep:
        board[i][j] = ""
    return board


# ###################### - GUI LOGIC - #######################################
def getBoardLayout(grid):
    global elt_grid
    board_layout = []
    for i in range(9):
        board_row = ["?", (None, BIG_MARGIN)]
        for j in range(9):
            elt = pssm.Button(
                text=str(grid[i][j]),
                user_data = (i, j),
                onclickInside = setCursorPosition
            )
            elt_grid[i][j] = elt
            board_row.append((elt, "?"))
            if j in [2, 5, 8]:
                board_row.append((None, BIG_MARGIN))
            else:
                board_row.append((None, MARGIN))
        board_layout.append(board_row)
        if i in [2, 5, 8]:
            board_layout.append([BIG_MARGIN])
        else:
            board_layout.append([MARGIN])
    return board_layout


def getDigitList():
    digits = [(None,BIG_MARGIN)]
    for i in range(9):
        elt = pssm.Button(
            text=str(i+1),
            user_data=i+1,
            onclickInside=setValue,
            background_color='gray12'
        )
        digits.append((elt,"?"))
        digits.append((None,BIG_MARGIN))
    return digits


@pssm.timer
def setCursorPosition(elt,coords=None):
    """
    Sets the cursor position (add a gray background to the new cell, removes
    the gray background from the previous one).
    Also handles selecting an item for the first time or deselecting an item.

    Note : the most natural way to do it would be to run :
        elt_grid[i][j].update(newAttributes={
            'background_color':'white'
        })
        for both element.
        Yet that is *very* slow. It's much faster to run:
        elt_grid[i][j].update(
            newAttributes={'background_color':'white'},
            reprintOnTop=True
        )
    """
    global cursor_position
    global elt_grid
    if cursor_position:
        (i, j) = cursor_position
        # Reset previous selected item:
        elt_grid[i][j].update(
            newAttributes={'background_color':'white'},
            reprintOnTop=True
        )
    # Set the new selected item (unless you only want to deselect)
    if cursor_position == elt.user_data:
        cursor_position = None
    else:
        cursor_position = elt.user_data
        elt.update(
            newAttributes={'background_color':'gray12'},
            reprintOnTop=True
        )


def setValue(elt,coords=None):
    global cursor_position
    global grid
    user_input = str(elt.user_data)
    if cursor_position:
        (i, j) = cursor_position
        if base_grid[i][j] != "":
            # Can't change base_grid
            return None
        grid[i][j] = user_input
        contradiction = isWrong(grid, cursor_position, user_input)
        if contradiction:
            i2, j2 = contradiction
            # Show indicator
            elt_grid[i][j].update(
                newAttributes={'text': user_input, 'font_color': "gray4"},
                reprintOnTop=True
            )
            elt_grid[i2][j2].update(
                newAttributes={'background_color': "gray10"},
                reprintOnTop=True
            )
            # Then reset
            screen.device.wait(ERROR_INVERT_DURATION)
            screen.startBatchWriting()
            grid[i][j] = ""
            elt_grid[i][j].update(
                newAttributes={'text':""},
                reprintOnTop=True
            )
            elt_grid[i2][j2].update(
                newAttributes={'background_color':"white"},
                reprintOnTop=True
            )
        else:
            elt_grid[i][j].update(
                newAttributes={'text':user_input, 'font_color':"gray4"},
                reprintOnTop=True
            )


def main(numberOfCells=10):
    global grid
    global base_grid
    base_grid = generateSudokuGrid(numberOfCells=numberOfCells)
    grid = base_grid[:]
    board_layout = getBoardLayout(grid)
    digits = getDigitList()

    boardLayout = pssm.Layout(board_layout)
    quitBtn = pssm.Button("Quit", onclickInside=quit)
    main_layout  = [
        [BIG_MARGIN],
        ["?*6", (boardLayout, "?")],
        ["?*0.5", *digits],
        [BIG_MARGIN],
        ["?*1", (None, "?"), (quitBtn, "W/4"), (None,BIG_MARGIN)],
        [BIG_MARGIN]
    ]
    mainLayout = pssm.Layout(main_layout,screen.area)
    screen.addElt(mainLayout)


def quit(elt,coords=None):
    #Closing this FBInk session
    screen.device.closePrintHandler()
    #Closing touch file
    screen.device.closeInteractionHandler()
    os.system("killall python3")


if __name__ == "__main__":
    # Start Touch listener, as a separate thread
    screen.startListenerThread(grabInput=True)
    n = None
    while n is None:
        myPopup = pssm.PoputInput(
            titleText="Difficulty",
            titleFont=pssm.DEFAULT_FONTBOLD,
            titleFontSize="H*0.04",
            mainText="How many cells do you want to be given at start?",
            mainFontSize="H*0.02",
            inputFontSize="H*0.025"
        )
        screen.addElt(myPopup)
        user_input = myPopup.waitForResponse()
        try:
            n = int(user_input)
        except:
            n = None
    main(numberOfCells=n)
    if device == "Emulator":
        # only necessary for the emulator, and must be at the very end
        screen.device.startMainLoop()
