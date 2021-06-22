""" Task 1 widgets """
import tkinter as tk
from tkinter import messagebox
from typing import Tuple

from a2_solution import first_in_direction, Game, Position, Zombie, Inventory
from constants import (
    TITLE,
    PLAYER,
    HOSPITAL,
    CROSSBOW,
    ZOMBIES,
    ENTITY_COLOURS,
    MAX_ITEMS,
    INVENTORY_WIDTH,
    DARK_PURPLE,
    ACCENT_COLOUR,
    MAP_BACKGROUND_COLOUR,
    LIGHT_PURPLE,
    CELL_SIZE,
    DIRECTIONS,
    ARROWS_TO_DIRECTIONS
)


class AbstractGrid(tk.Canvas):
    """ Support for creation of and annotation on grids. """

    def __init__(self, master, rows, cols, width, height, **kwargs):
        """ Constructor for AbstractGrid.

        Parameters:
            master (tk.Tk | tk.Frame): The master frame for this Canvas.
            rows (int): Number of rows.
            cols (int): Number of columns.
            width (int): The width of the Canvas in pixels.
            height (int): The height of the Canvas in pixels.
        """
        super().__init__(master, width=width, height=height, **kwargs)
        self._rows = rows
        self._cols = cols
        self._cell_width = width // cols
        self._cell_height = height // rows

    def get_bbox(self, position):
        """ Returns the bounding box of the given (row, col) position.

        Parameters:
            position (tuple<int, int>): The (row, col) cell position.

        Returns:
            (tuple<int * 4>): Bounding box for this position as
                              (x_min, y_min, x_max, y_max).
        """
        row, col = position
        x_min, y_min = col * self._cell_width, row * self._cell_height
        x_max, y_max = x_min + self._cell_width, y_min + self._cell_height
        return x_min, y_min, x_max, y_max

    def pixel_to_position(self, pixel):
        """ Converts the x, y pixel position to a (row, col) position.

        Parameters:
            pixel (tuple<int, int>): x, y position.
        Returns:
            (tuple<int, int): (row, col) position.
        """
        x_coord, y_coord = pixel
        return y_coord // self._cell_height, x_coord // self._cell_width

    def get_position_center(self, position):
        """ Gets the graphics coordinates for the center of the cell at the
            given (row, col) position.

        Parameters:
            position (tuple<int, int>): The (row, col) cell position.

        Returns:
            tuple(int, int): The x, y pixel position of the center of the cell.
        """
        row, col = position
        x_pos = col * self._cell_width + self._cell_width // 2
        y_pos = row * self._cell_height + self._cell_height // 2
        return x_pos, y_pos

    def annotate_position(self, position, text):
        """ Annotates the cell at the given (row, col) position with the
            provided text.

        Parameters:
            position (tuple<int, int>): The (row, col) cell position.
            text (str): The text to draw.
        """
        self.create_text(self.get_position_center(position), text=text)

    def clear(self):
        """ Clears all child widgets off the canvas. """
        self.delete("all")


class BasicMap(AbstractGrid):
    """ A simple rectangle-based display for the game map. """

    def __init__(self, master, size, bg=MAP_BACKGROUND_COLOUR, **kwargs):
        """ Constructor for BasicMap.

        Parameters:
            master (tk.Tk | tk.Frame): The master frame for this Canvas.
            size (int): The number of rows (= #columns) in this map.
        """
        width = height = CELL_SIZE * size
        super().__init__(master, size, size, width, height, bg=bg, **kwargs)

    def draw_entity(self, position, tile_type):
        """ Draws the entity with id tile_type at the given position using a
            coloured rectangle with superimposed text for the ID.

        Parameters:
            position (tuple<int, int>): (row, column) position to draw at.
            tile_type (str): ID of the entity.
        """
        text_colour = 'white' if tile_type in (PLAYER, HOSPITAL) else 'black'
        colour = ENTITY_COLOURS.get(tile_type, MAP_BACKGROUND_COLOUR)
        bbox = self.get_bbox(position)
        center = self.get_position_center(position)

        self.create_rectangle(bbox, fill=colour)
        self.create_text(center, text=tile_type, fill=text_colour)


class InventoryView(AbstractGrid):
    """ A display of the inventory which allows users to activate items with a
        left click.
    """

    def __init__(self, master, rows, **kwargs):
        """ Constructor for InventoryView.

        Parameters:
            master (tk.Tk | tk.Frame): The master frame for this canvas.
            rows (int): #rows to allow in this inventory (including header).
        """
        super().__init__(master, rows, 2, INVENTORY_WIDTH, CELL_SIZE * rows,
                         bg=LIGHT_PURPLE, **kwargs)

    def draw(self, inventory):
        """ Draws the inventory label and current items with their remaining
            lifetimes.

        Parameters:
            inventory (Inventory): The games inventory instance.
        """
        self._draw_inventory_label()

        for i, pickup in enumerate(inventory.get_items()):
            entity_name = pickup.__class__.__name__
            lifetime = pickup.get_lifetime()
            entity_pos = self.get_position_center((i + 1, 0))
            lifetime_pos = self.get_position_center((i + 1, 1))

            # Colour background and change text colour for active items
            text_colour = 'black'
            if pickup.is_active():
                x_min, y_min, _, y_max = self.get_bbox(((i + 1), 0))
                x_max = x_min + INVENTORY_WIDTH
                self.create_rectangle((x_min, y_min, x_max, y_max),
                                      fill=DARK_PURPLE, outline='')
                text_colour = 'white'

            # Add text for entity type and lifetime
            self.create_text(entity_pos, text=entity_name, fill=text_colour)
            self.create_text(lifetime_pos, text=lifetime, fill=text_colour)

    def _draw_inventory_label(self):
        """ Draws the inventory label centered in the first row. """
        # middle of first row is same as top left of second column first row
        middle_x, *_ = self.get_bbox((0, 1))
        _, middle_y = self.get_position_center((0, 0))
        self.create_text(middle_x, middle_y, text='Inventory', fill=DARK_PURPLE,
                         font=('Comic Sans', 22))

    def use_item(self, pixel, inventory):
        """ Activates the item in the given row if one exists.

        Parameters:
            pixel (tuple<int, int>): The pixel position of the click event.
            inventory (Inventory): The player's current inventory instance.
        """
        row = self.pixel_to_position(pixel)[0] - 1  # -1 to account for header
        items = inventory.get_items()
        if 0 <= row < len(items) and (items[row].is_active() or
                                      not inventory.any_active()):
            items[row].toggle_active()
            self.clear()
            self.draw(inventory)


class BasicGraphicalInterface:
    """ A basic graphical interface for EndOfDayz. """

    def __init__(self, root, size, **kwargs):
        """ Constructor for BasicGraphicalInterface.

        Parameters:
            root (tk.Tk | tk.Frame): The master frame for this Frame.
            size (int): The number of rows (and height) in the map.
        """
        self._root = root
        self._size = size

        self._container = tk.Frame(root)
        self._container.pack()

        self._add_title()
        self._set_up_view()

        self._step_event = None
        self._running = True

    def _add_title(self):
        """ Configure the window title and add a new title label. """
        self._root.title(TITLE)

        tk.Label(
            self._container,
            text=TITLE,
            bg=ACCENT_COLOUR,
            relief=tk.RAISED,
            fg='white',
            font=('Arial', 28)
        ).pack(fill=tk.X)

    def _set_up_view(self):
        """ Set up widgets for map and inventory. """
        # Outer frame
        self._game_frame = tk.Frame(self._container)
        self._game_frame.pack()

        # Map
        self._grid = self._get_map()
        self._grid.pack(side=tk.LEFT)

        # Inventory
        self._inventory_display = InventoryView(self._game_frame, MAX_ITEMS)
        self._inventory_display.pack(side=tk.LEFT)

    def _get_map(self):
        """ (BasicMap) Gets the map instance. """
        return BasicMap(self._game_frame, self._size, bg=MAP_BACKGROUND_COLOUR)

    def _inventory_click(self, event, inventory):
        """ Event handler for left click on inventory.

        Parameters:
            event (tk.Event): Event object.
            inventory (Inventory): The player's current inventory.
        """

        pixel = event.x, event.y
        self._inventory_display.use_item(pixel, inventory)

    def draw(self, game):
        """ Clears and redraws the view based on the current game state.

        Parameters:
            game (Game): The current game.
        """
        self._grid.clear()
        mapping = game.get_grid().serialize()
        self._draw_background()
        for position, tile in mapping.items():
            self._grid.draw_entity(position[::-1], tile)
        self._inventory_display.clear()
        self._inventory_display.draw(game.get_player().get_inventory())

    def _draw_background(self):
        """ Handles drawing the background for the whole grid. """
        pass  # Nothing for task 1 because bg is set through Frame bg argument

    def _handle_win(self, game):
        """ Handles win behaviour. """
        self._root.update()  # For mac to update GUI before showing message
        messagebox.showinfo('Game Over', 'You win!')
        self._root.destroy()

    def _handle_loss(self):
        """ Handles loss behaviour. """
        self._root.update()  # For mac to update GUI before showing message
        messagebox.showinfo('Game Over', 'You lose!')
        self._root.destroy()

    def _move(self, game, direction):
        """ Handles player move.

        Parameters:
            game (Game): The current game.
            direction (str): The key the player pressed.
        """
        offset = game.direction_to_offset(direction)
        if offset is not None:
            game.move_player(offset)
            self.draw(game)

        if game.has_won():
            self._handle_win(game)

    def _step(self, game):
        """ The _step method is called every second. This method triggers the
            step method for all entities and updates the view accordingly.

        Parameters:
            game (Game): The game instance.
        """
        if not self._running:
            return
        game.step()
        self.draw(game)

        if self._game_has_lost(game):
            return

        self._step_event = self._root.after(1000, lambda: self._step(game))

    def _game_has_lost(self, game: Game) -> bool:
        """
        Checks if game has lost and return the result. Handle lost event as
        appropriate

        Parameters:
            game: Game to be checked
        """
        if game.has_lost():
            self._handle_loss()
            return True
        return False

    def _try_fire_crossbow(self, direction: str, game: Game):
        """
        Attempts to fire a crossbow in the given direction, kills a zombie if
        there's one

        Parameters:
            direction: direction to fire in
            game: game being played
        """
        player = game.get_player()

        # Ensure player has a weapon that they can fire.
        if player.get_inventory().has_active(CROSSBOW):

            # Fire the weapon in the indicated direction, if possible.
            if direction in DIRECTIONS:
                start = game.get_grid().find_player()
                offset = game.direction_to_offset(direction)
                if start is None or offset is None:
                    return  # Should never happen.

                # Find the first entity in the direction player fired.
                first = first_in_direction(game.get_grid(), start, offset)

                # If the entity is a zombie, kill it.
                if first is not None and first[1].display() in ZOMBIES:
                    self._shoot_at_zombie(game, first)

    def _shoot_at_zombie(self, game: Game, first: Tuple[Position, Zombie]):
        """
        Shoot a zombie

        Parameters:
            game: Current game being played
            first: the zombie and its position
        """
        position, entity = first
        game.get_grid().remove_entity(position)
        self.draw(game)

    def _handle_keypress(self, event, game):
        if event.char.lower() in ('w', 'a', 's', 'd'):
            self._move(game, event.char.upper())

        if event.keysym in ('Left', 'Right', 'Up', 'Down'):
            self._try_fire_crossbow(ARROWS_TO_DIRECTIONS.get(event.keysym),
                                    game)

    def pause(self):
        self._root.after_cancel(self._step_event)
        self._running = False

    def resume(self, game):
        self._running = True
        self._step_event = self._root.after(1000, self._step, game)

    def play(self, game):
        """ Binds events and initializes gameplay.

        Parameters:
            game (Game): The game instance.
        """
        self.draw(game)

        inventory = game.get_player().get_inventory()
        self._bind_inventory(inventory)

        self._root.bind('<KeyPress>', lambda e: self._handle_keypress(e, game))

        self.resume(game)
        self._root.mainloop()

    def _bind_inventory(self, inventory: Inventory):
        """
        Binds the click events to the current inventory

        Parameters:
            inventory: inventory to be bound
        """
        self._inventory_display.bind(
            '<Button-1>', lambda e: self._inventory_click(e, inventory))
