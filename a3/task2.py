""" Task 2 widgets """
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import ImageTk, Image

from a2_solution import GameState, Game, RestartableGame
from task1 import BasicMap, BasicGraphicalInterface
from constants import (
    BACK_GROUND,
    IMAGES,
    TITLE,
    BANNER_HEIGHT,
    INVENTORY_WIDTH,
    CELL_SIZE,
    HIGH_SCORES_FILE,
    MAX_ALLOWED_HIGH_SCORES,
    ACCENT_COLOUR
)


class ImageMap(BasicMap):
    """ An image-based display for the game map. """

    def __init__(self, master, size, **kwargs):
        """ Constructor for BasicMap.

        Parameters:
            master (tk.Tk | tk.Frame): The master frame for this Canvas.
            size (int): The number of rows (= #columns) in this map.
        """
        super().__init__(master, size, bg='white', **kwargs)
        self._images = {}

    def draw_entity(self, position, tile_type):
        """ Draws the entity using a sprite image.

        Parameters:
            position (tuple<int, int>): (row, column) position to draw at.
            tile_type (str): ID of the entity.
        """
        pixel = self.get_position_center(position)
        self.create_image(*pixel, image=self.get_image(tile_type))

    def get_image(self, tile_type, angle=0):
        """ Gets the image for the entity of given type. Creates a new image
            if one doesn't exist for this entity and stores a reference to it.

        Parameters:
            tile_type (str): ID of the entity.

        Returns:
            (ImageTk.PhotoImage): The image for the given tile_type.
        """
        cache_id = f"{tile_type}_{angle}"
        if cache_id not in self._images:
            image = ImageTk.PhotoImage(
                image=Image.open(IMAGES.get(tile_type)).rotate(angle).resize(
                    (CELL_SIZE, CELL_SIZE)))
            self._images[cache_id] = image
        return self._images[cache_id]


class StatusBar(tk.Frame):
    """ A StatusBar to convey some useful information to the user about their
        progress in the game. """

    def __init__(self, master, *args, **kwargs):
        """ Constructor for StatusBar.

        Parameters:
            master (tk.Tk | tk.Frame): The master frame for this Frame.
        """
        super().__init__(master, *args, **kwargs)

        self._chaser = ImageTk.PhotoImage(image=Image.open('images/chaser.png'))
        tk.Label(self, image=self._chaser).pack(side=tk.LEFT, expand=True)

        self._set_up_timer()
        self._set_up_moves_label()
        self._set_up_buttons()

        self._chasee = ImageTk.PhotoImage(image=Image.open('images/chasee.png'))
        tk.Label(self, image=self._chasee).pack(side=tk.LEFT, expand=True)

    def _set_up_timer(self):
        """ Sets up widgets for timer information. """
        timer_frame = tk.Frame(self)
        timer_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        tk.Label(timer_frame, text='Timer').pack()

        self._time_label = tk.Label(timer_frame)
        self._time_label.pack()

    def _set_up_moves_label(self):
        """ Sets up widgets for moves information. """
        moves_frame = tk.Frame(self)
        moves_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        tk.Label(moves_frame, text='Moves made').pack()

        self._moves_label = tk.Label(moves_frame)
        self._moves_label.pack()

    def set_time(self, mins, seconds):
        """ Updates the time on the timer label.

        Parameters:
            mins (int): Number of minutes elapsed.
            seconds (int): Number of seconds elapsed.
        """
        self._time_label.config(text=f'{mins} mins {seconds} seconds')

    def set_moves(self, num_moves):
        """ Updates the moves information.

        Parameters:
            num_moves (int): Number of moves made by the player.
        """
        self._moves_label.config(text=f'{num_moves} moves')

    def _set_up_buttons(self):
        """ Creates the new game and restart buttons. """
        buttons_frame = tk.Frame(self)
        buttons_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self._restart_game_button = tk.Button(buttons_frame,
                                              text='Restart Game')
        self._restart_game_button.pack()
        self._quit_button = tk.Button(buttons_frame, text='Quit Game')
        self._quit_button.pack()

    def set_button_commands(self, restart_command, quit_command):
        """ Set the commands to call when the buttons are pressed.

        Parameters:
            new_game_command (function): The callback for the new game button.
            restart_command (function): The callback for the restart button.
        """
        self._restart_game_button.config(command=restart_command)
        self._quit_button.config(command=quit_command)


class ImageGraphicalInterface(BasicGraphicalInterface):
    """ An image-based graphical interface for EndOfDayz. """

    def __init__(self, root, size):
        """ Constructor for ImageGraphicalInterface.

        Parameters:
            root (tk.Tk | tk.Frame): The master frame for this Frame.
            size (int): The number of rows (and height) in the map.
        """
        super().__init__(root, size, bg='white')

        self._status_bar = StatusBar(self._container)
        self._status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self._status_bar.set_moves(0)
        self._step_event = None

    def _add_title(self):
        """ Configure the window title and add a new title label. """
        self._root.title(TITLE)

        # Resize banner image and draw instead of heading label.
        image = Image.open('images/banner.png')
        banner_size = (INVENTORY_WIDTH + self._size * CELL_SIZE, BANNER_HEIGHT)
        image = image.resize(banner_size, Image.ANTIALIAS)
        self._banner_image = ImageTk.PhotoImage(image=image)
        tk.Label(self._container, image=self._banner_image).pack()

    def _get_map(self):
        """ (ImageMap) Gets the map instance. """
        return ImageMap(self._game_frame, self._size)

    def _step(self, game):
        """ The _step method is called every second. This method triggers the
            step method for all entities and updates the view accordingly.

        Parameters:
            game (Game): The game instance.
        """
        time = game.get_steps()
        self._status_bar.set_time(time // 60, time % 60)
        super()._step(game)

    def _draw_background(self):
        """ Handles drawing the background for the whole grid. """
        for i in range(self._size):
            for j in range(self._size):
                self._grid.draw_entity((i, j), BACK_GROUND)

    def _set_up_file_menu(self, game):
        """
        Set up file menu.

        Parameters:
            game: Current game being played
        """
        menubar = tk.Menu(self._root)
        self._root.config(menu=menubar)

        filemenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Restart game",
                             command=lambda: self.restart_game(game))
        filemenu.add_separator()

        filemenu.add_command(label="Load game",
                             command=lambda: self.load_game(game))
        filemenu.add_command(label="Save game",
                             command=lambda: self.save_game(game))
        filemenu.add_separator()

        filemenu.add_command(label="High scores", command=self.high_scores)
        filemenu.add_separator()

        filemenu.add_command(label="Quit", command=self.quit_game)

    def _handle_win(self, game):
        """
        Handles win behaviour.

        Parameters:
            game: Current game being played
        """
        self._root.after_cancel(self._step_event)
        self._root.update()
        self.high_scores_prompt(game)

    def high_scores(self):
        """ Displays high scores table. """
        HighScoresTable(self._root)

    def high_scores_prompt(self, game):
        """ Prompting for users name, and logging to high scores file. """
        prompt = HighScorePrompt(
            self._root,
            game.get_steps(),
            restart_callback=lambda: self.restart_game(game))
        prompt.set_focus()
        prompt.wm_transient(self._root)
        self._root.wait_window(prompt)

    def _handle_loss(self):
        """ Handles loss behaviour. """
        self._root.update()  # For Mac to update GUI before showing message.
        messagebox.showinfo('Game Over', 'You lose!')

    def restart_game(self, game):
        """ Restarts the current game (including statusbar info).
        
        Parameters:
            game (Game): Current game instance.
        """
        self.pause()
        game.restart()
        new_inventory = game.get_player().get_inventory()
        self._bind_inventory(new_inventory)
        self.draw(game)
        self.resume(game)

    def quit_game(self):
        """ Prompts the user for whether they really want to quit and ends
            the program if they do.
        """
        if messagebox.askyesno('Quit?', 'Do you really want to quit?'):
            self._root.destroy()

    def load_game(self, game: RestartableGame):
        """
        Prompts the user with a filedialog and loads the selected file.

        Parameters:
            game: game whose state is to be changed after loading
        """
        filename = filedialog.askopenfilename(initialdir=".",
                                              title="Save game",
                                              filetypes=[("Text", "*.txt")],
                                              defaultextension="txt")
        with open(filename) as file:
            try:
                game.apply_state(GameState.deserialise(file.read()))
                self.draw(game)
            except (IndexError, ValueError) as e:
                print("Invalid", e)
                messagebox.showerror("Invalid file format",
                                     "Invalid file format")
        self._root.grab_set()

    def save_game(self, game):
        """ Prompts the user with a filedialog and saves the game to the
            requested location.

            Simple error handling is expected.

            Intentionally not implemented in sample solution; follow whatever
            approach the student is suggesting (they need to do most of this
            themselves).
        """
        filename = filedialog.asksaveasfilename(initialdir=".",
                                                title="Save game",
                                                filetypes=[("Text", "*.txt")],
                                                defaultextension="txt")
        with open(filename, "w") as file:
            file.write(GameState(game).serialise())
        self._root.grab_set()

    def _move(self, game, direction):
        """ Handles player move.

        Parameters:
            game (Game): The current game.
            direction (str): The key the player pressed.
        """
        super()._move(game, direction)
        self._status_bar.set_moves(game.get_move_count())

    def play(self, game):
        """ Binds events and initializes gameplay.

        Parameters:
            game (Game): The game instance.
        """
        self._status_bar.set_button_commands(lambda: self.restart_game(game),
                                             self.quit_game)
        self._set_up_file_menu(game)
        super().play(game)


class HighScorePrompt(tk.Toplevel):
    def __init__(self, master: tk.Tk, time: int, restart_callback=lambda: None):
        """
        Constructor

        Parameters:
            master: master widget, usually the root window
            time: time that the user spent after winning
            restart_callback: callback fired when user wants to restart
        """
        super().__init__(master)
        self._time = time
        self._restart_callback = restart_callback

        self.title("You Win!")

        minutes, seconds = time // 60, time % 60
        message = f"You won in {minutes}m and {seconds}s! Enter your name:"
        tk.Label(self, text=message).pack()

        self._name_entry = tk.Entry(self)
        self._name_entry.bind('<Return>', lambda e: self.save_score())
        self._name_entry.pack()

        btn_frame = tk.Frame(self)
        btn_frame.pack(ipady=5)

        tk.Button(btn_frame,
                  text="Enter",
                  command=self.save_score).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Enter and play again",
                  command=self.save_score_and_restart).pack(side=tk.LEFT,
                                                            padx=5)

    def set_focus(self):
        self._name_entry.focus_set()

    def save_score(self):
        """ Logs users score in high scores file if it's part of the top 3. """
        scores = []
        # Open high scores file and populate score list.
        try:
            with open(HIGH_SCORES_FILE, "r") as file:
                for line in file:
                    name, score = line.strip().split(",")
                    scores.append((name, int(score)))
        except FileNotFoundError:
            pass

        # Add score to list if it's in top 3.
        scores.append((self._name_entry.get(), self._time))
        scores.sort(key=lambda item: item[1])
        if len(scores) > MAX_ALLOWED_HIGH_SCORES:
            scores = scores[:MAX_ALLOWED_HIGH_SCORES]

        # Write the new scores to the file.
        with open(HIGH_SCORES_FILE, "w") as file:
            for name, score in scores:
                file.write(f"{name},{score}\n")

        self.destroy()

    def save_score_and_restart(self):
        self.save_score()
        self._restart_callback()


class HighScoresTable(tk.Toplevel):
    """ A Toplevel window for displaying top 3 high scores. """

    def __init__(self, master, file=HIGH_SCORES_FILE):
        """ Constructor for HighScoresTable.
        Parameters:
            file (str): Name of high scores file.
        """
        super().__init__(master)
        self.title("Top 3")
        tk.Label(
            self,
            text="High Scores",
            bg=ACCENT_COLOUR,
            relief=tk.RAISED,
            fg='white',
            font=('Arial', 28)
        ).pack()

        try:
            with open(file, "r") as file:
                for line in file:
                    name, score = line.strip().split(",")
                    score = int(score)
                    mins, seconds = score // 60, score % 60
                    mins_formatted = f"{mins}m " if mins != 0 else ""
                    tk.Label(self,
                             text=f"{name}: {mins_formatted}{seconds}s").pack()

            tk.Button(self, text="Done", command=self.destroy).pack()
        except FileNotFoundError:
            tk.Label(self, text="No highscores yet!").pack()
