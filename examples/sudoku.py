#!/usr/bin/env python
import sys
sys.path.append("../")
import os
from PSSM import Stack
from PSSM.elements import Rectangle, Margin
from PSSM.styles import DEFAULT as DEFAULT_STYLE
from PSSM.layouts import Collection
from PSSM.layouts import OSK, KTstandardChar,KTcarriageReturn,KTbackspace, KTdelete, KTcapsLock, KTcontrol, KTalt
import platform
import random
if platform.machine() in ["x86", "AMD64", "i686", "x86_64"]:
    device = "Emulator"
else:
    device = "Kobo"

# ###################### - INIT - ###########################################
# Declare the Screen Stack Manager
stack = Stack(device)
# Clear and refresh the stack
stack.screen.clear()
stack.screen.refresh()
# Now to initialize the keybaord
osk = OSK()

# Variables:
MARGIN = "H*0.0063"
BIG_MARGIN = "H*0.015"
ERROR_INVERT_DURATION = 1000
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
    board_coll_array = []
    for i in range(9):
        board_row = [Margin(width=BIG_MARGIN)]
        for j in range(9):
            elt = Rectangle(
                user_data = (i, j),
                onclick = setCursorPosition
            )
            elt.add_text(str(grid[i][j]), x="center", y="center")
            elt_grid[i][j] = elt
            board_row.append(elt)
            if j in [2, 5, 8]:
                board_row.append(Margin(width=BIG_MARGIN))
            else:
                board_row.append(Margin(width=MARGIN))
        board_coll_array.append(Collection(board_row, height="?"))
        if i in [2, 5, 8]:
            board_coll_array.append(Margin(height=BIG_MARGIN))
        else:
            board_coll_array.append(Margin(height=MARGIN))
    return Collection(axis="y", coll=board_coll_array)


def getDigitList():
    digits = [Margin(width=BIG_MARGIN)]
    for i in range(9):
        elt = Rectangle(
            user_data=i+1,
            onclick=setValue,
            background_color=(230,230,230,1)
        )
        elt.add_text(str(i+1), x="center", y="center")
        elt.height = "?"
        digits.append(elt)
        digits.append(Margin(width=BIG_MARGIN))
    return digits


def setCursorPosition(elt,coords=None):
    """
    Sets the cursor position (add a gray background to the new cell, removes
    the gray background from the previous one).
    Also handles selecting an item for the first time or deselecting an item.
    Note : the most natural way to do it would be to run :
        elt_grid[i][j].update(attr={
            'background_color':(255,255,255,0)
        })
        for both element.
        Yet that is *very* slow. It's much faster to run:
        elt_grid[i][j].update(
            attr={'background_color':(255,255,255,0)},
            on_top=True
        )
    """
    global cursor_position
    global elt_grid
    if cursor_position:
        (i, j) = cursor_position
        # Reset previous selected item:
        elt_grid[i][j].update(
            attr={'background_color':(255,255,255,255)},
            on_top=True
        )
    # Set the new selected item (unless you only want to deselect)
    if cursor_position == elt.user_data:
        cursor_position = None
    else:
        cursor_position = elt.user_data
        elt.update(
            attr={'background_color':(200,200,200,255)},
            on_top=True
        )


def setValue(elt,coords=None):
    global cursor_position
    global elt_grid
    user_input = str(elt.user_data)
    if cursor_position:
        (i, j) = cursor_position
        if base_grid[i][j] != "":
            # Can't change base_grid
            return None
        grid[i][j] = user_input
        contradiction = isWrong(grid, cursor_position, user_input)
        if contradiction:
            print("There is contradiction", (i,j), contradiction)
            i2, j2 = contradiction
            # Show indicator
            elt_grid[i][j].update(
                attr={'text': user_input, 'font_color': (80,80,80,255)},
                on_top=True
            )
            elt_grid[i2][j2].update(
                attr={'background_color': (200,200,200,255)},
                on_top=True
            )
            # Then reset
            def invertback():
                grid[i][j] = ""
                elt_grid[i][j].update(
                    attr={'text':""},
                    on_top=True
                )
                elt_grid[i2][j2].update(
                    attr={'background_color':(255,255,255,255)},
                    on_top=True
                )
            stack.hardware.after(ERROR_INVERT_DURATION, invertback)
        else:
            elt_grid[i][j].update(
                attr={'text':user_input, 'font_color':(80,80,80,255)},
                on_top=True
            )


def quit_fct(*args):
    print("Quitting not implemented yet")


def main(numberOfCells=10):
    global grid
    global base_grid
    base_grid = generateSudokuGrid(numberOfCells=numberOfCells)
    grid = base_grid[:]
    boardCollection = getBoardLayout(grid)
    digits = getDigitList()
    quitBtn = Rectangle(onclick=quit_fct, width="W/4")
    quitBtn.add_text("Quit", x="center", y="center")

    main_coll = Collection(axis="y", area = stack.screen.area, coll=[
        Collection([],                  height=BIG_MARGIN),
        Collection([boardCollection],   height="?*6"),
        Collection(digits,              height="?*0.5"),
        Collection([],                  height=BIG_MARGIN),
        Collection([Margin(width=BIG_MARGIN), quitBtn, Margin(width=BIG_MARGIN)], height="?"),
        Collection([],                  height=BIG_MARGIN)
    ])
    stack.add(main_coll)


if __name__ == "__main__":
    n = 30
    main(numberOfCells=n)
    stack.mainloop()