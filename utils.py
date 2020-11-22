
def coords_in_area(area, click_x, click_y):
    """
    Returns a boolean indicating if the click was in the given area
    Args:
        area (list): The area (of shape : [(x, y), (w, h)])
        click_x (str): The x coordinate of the click
        click_y (str): The y coordinate of the click
    """
    [(x, y), (w, h)] = area
    if click_x >= x and click_x < x+w and click_y >= y and click_y < y+h:
        return True
    else:
        return False