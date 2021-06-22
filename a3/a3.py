"""
A GUI-based zombie survival game wherein the player has to reach
the hospital whilst evading zombies.
"""
import tkinter as tk
from a2_solution import advanced_game
from constants import TASK, MAP_FILE

# More sophisticated approach to checking which tasks have been implemented.
has_task1 = has_task2 = has_masters = True
try:
    from task1 import BasicGraphicalInterface
except ImportError:
    has_task1 = False

try:
    from task2 import ImageGraphicalInterface
except ImportError:
    has_task2 = False

try:
    from csse7030 import MastersGraphicalInterface
except ImportError:
    has_masters = False


def main() -> None:
    """Entry point to gameplay."""
    game = advanced_game(MAP_FILE)

    root = tk.Tk()
    root.title('EndOfDayz')
    if TASK == 1:
        if not has_task1:
            raise ImportError("Student did not implement "
                              "BasicGraphicalInterface")
        gui = BasicGraphicalInterface
    elif TASK == 2:
        if not has_task2:
            raise ImportError("Student did not implement "
                              "ImageGraphicalInterface")
        gui = ImageGraphicalInterface
    else:
        if not has_masters:
            raise ImportError("Student did not implement "
                              "MastersGraphicalInterface")
        gui = MastersGraphicalInterface
    app = gui(root, game.get_grid().get_size())
    app.play(game)


if __name__ == '__main__':
    main()
