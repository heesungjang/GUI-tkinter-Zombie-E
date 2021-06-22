from a2_solution import TimeMachine, SuperUltraHyperMegaAdvancedGame, Grid
from task2 import ImageGraphicalInterface
from constants import ARROW, TIME_MACHINE


class Animation:
    """
    An animation which is played out via the AnimationManager.
    """
    DEFAULT_FRAMERATE = 20

    def __init__(self):
        self._start_callback = lambda: None
        self._finish_callback = lambda: None

    def on_finish(self, callback):
        """
        Register a callback when the animation is completed.
        """
        self._finish_callback = callback

    def on_start(self, start_callback):
        self._start_callback = start_callback

    def get_framerate(self):
        """
        Get the 'framerate' of this animation, how many seconds between
        calls to the step method.
        """
        return Animation.DEFAULT_FRAMERATE

    def step(self, canvas) -> bool:
        """
        Implements an animation step by rendering to the canvas.

        Return True to continue with animation steps and False to stop
        an animation from continuing.
        """
        raise NotImplementedError("Abstract animation object stepped")

    def start(self, canvas):
        """
        Perform any setup actions when an animation first starts playing.
        """
        self._start_callback()

    def finish(self, canvas):
        """
        Perform any destruct actions when an animation stops playing.
        """
        self._finish_callback()

    def get_frequency(self):
        return round(1000 / self.get_framerate())


class CrossboltAnimation(Animation):
    """
    Implementation of a crossbolt animation which moves the crossbolt
    image from the starting position to the target position.
    """
    ANGLE_MAP = {(0, -1): 90, (0, 1): 270, (-1, 0): 180, (1, 0): 0}
    STEP_SIZE = 25

    def __init__(self, canvas, start, target):
        self._position = canvas.get_position_center(start)
        self._target = canvas.get_position_center(target)

        self._direction = self._direction_from_positions(start, target)
        self._angle = self._angle_from_direction(self._direction)

        self._image = None

    def _direction_from_positions(self, start, target):
        start_x, start_y = start
        target_x, target_y = target
        if start_x < target_x:
            return 0, 1
        elif start_x > target_x:
            return 0, -1
        elif start_y < target_y:
            return 1, 0
        elif start_y > target_y:
            return -1, 0
        else:
            raise ValueError("Invalid start and target specified for "
                             "crossbolt animation")

    def _angle_from_direction(self, direction):
        return CrossboltAnimation.ANGLE_MAP.get(direction)

    def get_framerate(self):
        return 10

    def _clear(self, canvas):
        if self._image is not None:
            canvas.delete(self._image)

    def _draw(self, canvas):
        self._clear(canvas)
        self._image = canvas.create_image(
            self._position,
            image=canvas.get_image(ARROW, angle=self._angle))

    def _has_passed_target(self) -> bool:
        """Checks if crossbolt has passed the target"""
        dx, dy = self._direction
        current_x, current_y = self._position
        target_x, target_y = self._target
        moving_left = dy < 0
        moving_right = dy > 0
        moving_up = dx < 0
        moving_down = dx > 0

        if moving_left and current_y < target_y:
            return True
        elif moving_right and current_y > target_y:
            return True
        elif moving_up and current_x < target_x:
            return True
        elif moving_down and current_x > target_x:
            return True
        return False

    def _move_one_step(self):
        current_x, current_y = self._position
        dx, dy = self._direction
        current_x += self.STEP_SIZE * dx
        current_y += self.STEP_SIZE * dy
        self._position = current_x, current_y

    def step(self, canvas):
        if self._has_passed_target():
            return False

        self._draw(canvas)
        self._move_one_step()
        return True

    def finish(self, canvas):
        self._clear(canvas)
        super().finish(canvas)


class TimeMachineAnimation(Animation):
    def __init__(self, canvas, game_states, draw_game_callback):
        super().__init__()
        self._canvas = canvas
        self._game_states = game_states
        self._draw_game = draw_game_callback
        self._current_step = len(game_states) - 1

    def get_frequency(self):
        return round(1000 / len(self._game_states))

    def step(self, canvas) -> bool:
        if self._current_step < 0:
            return False

        current_state = self._game_states[self._current_step]
        game = SuperUltraHyperMegaAdvancedGame(current_state.get_grid())
        game.apply_state(current_state)
        self._draw_game(game)

        self._current_step -= 1
        return True


class AnimationManager:
    """
    Manage possibly multiple animations for a tkinter canvas.
    """

    def __init__(self, canvas):
        """
        Construct an animation manager for a particular tkinter canvas.
        """
        self._canvas = canvas

    def _step_animation(self, animation: Animation):
        if not animation.step(self._canvas):
            animation.finish(self._canvas)
        else:
            self._canvas.after(animation.get_frequency(),
                               lambda: self._step_animation(animation))

    def play_animation(self, animation: Animation):
        """
        Playout an animation.
        """
        animation.start(self._canvas)
        self._step_animation(animation)


class MastersGraphicalInterface(ImageGraphicalInterface):
    def __init__(self, root, size):
        super().__init__(root, size)
        self._animator: AnimationManager = AnimationManager(self._grid)

    def _shoot_at_zombie(self, game, first):
        position, entity = first

        player_pos = game.get_grid().find_player()
        start_pos = (player_pos.get_y(), player_pos.get_x())
        goal_pos = (position.get_y(), position.get_x())

        crossbolt_animation = CrossboltAnimation(self._grid,
                                                 start_pos, goal_pos)
        crossbolt_animation.on_start(lambda: self._freeze_zombie(game,
                                                                 position))
        crossbolt_animation.on_finish(lambda: self._remove_zombie(game,
                                                                  position))

        self._animator.play_animation(crossbolt_animation)

    def _remove_zombie(self, game, position):
        game.get_grid().remove_entity(position)
        self.draw(game)

    def _freeze_zombie(self, game, position):
        zombie = game.get_grid().get_entity(position)
        zombie.cancel_step()

    def _reverse_time(self, game):
        inventory = game.get_player().get_inventory()
        time_machine = None
        for item in inventory.get_items():
            if isinstance(item, TimeMachine):
                time_machine = item
        if time_machine is None:
            return  # Should not happen.
        game_states = time_machine.get_game_states()
        time_machine_animation = TimeMachineAnimation(self._grid,
                                                      game_states,
                                                      self.draw)
        time_machine_animation.on_start(self.pause)
        time_machine_animation.on_finish(
            lambda: self._use_time_machine(time_machine, game))
        self._animator.play_animation(time_machine_animation)

    def _game_has_lost(self, game):
        if not game.has_lost():
            return False
        if game.get_player().get_inventory().contains(TIME_MACHINE):
            self._reverse_time(game)
            return False
        self._handle_loss()
        return True

    def _use_time_machine(self, time_machine, game):
        time_machine.use(game)
        self._bind_inventory(game.get_player().get_inventory())
        self.resume(game)
