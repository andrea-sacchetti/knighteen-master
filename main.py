__version__ = '1.1.1'

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, OptionProperty, ObjectProperty
from kivy.graphics import Color, BorderImage, Rectangle, Line
from kivy.graphics.instructions import InstructionGroup
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.utils import platform
from kivy.factory import Factory
from random import choice, random
from time import sleep
import math
from kivy.storage.jsonstore import JsonStore

platform = platform()
app = None

if platform=="android":
    from jnius import autoclass
    PythonActivity=autoclass("org.renpy.android.PythonActivity")
    AdBuddiz=autoclass("com.purplebrain.adbuddiz.sdk.AdBuddiz")

class RotatedImage(Image):
    angle = NumericProperty()

    def __init__(self, **kwargs):
        super(RotatedImage, self).__init__(**kwargs)
        anim = Animation(d=.15, t='out_quad')
        # anim.bind(on_complete=self.clean_canvas)
        anim.start(self)

    def clean_canvas(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()

    def destroy(self, *args):
        self.parent.remove_widget(self)


class Number(Widget):
    number = NumericProperty(2)
    scale = NumericProperty(.1)

    def __init__(self, **kwargs):
        super(Number, self).__init__(**kwargs)
        anim = Animation(scale=1., d=.15, t='out_quad')
        anim.bind(on_complete=self.clean_canvas)
        anim.start(self)

    def get_colors(self, number, dummy):
        return [math.cos(math.pi / 4. * i + (number - 1) * 0.505)**2 for i in range(3)]

    def clean_canvas(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()

    def destroy(self, *args):
        self.parent.remove_widget(self)

class HelpPage(Widget):
    def __init__(self, **kwargs):
        super(HelpPage, self).__init__(**kwargs)

board_size = 8
animation_delay = 0.1

store = JsonStore('storage.json')

class GameK19(Widget):

    cube_size = NumericProperty(10)
    cube_padding = NumericProperty(10)
    score = NumericProperty(0)
    max_num = NumericProperty(0)

    def __init__(self, **kwargs):
        super(GameK19, self).__init__()
        if platform == 'android':
            AdBuddiz.setPublisherKey("40a7f4b5-a0d1-4f79-9f7b-11f1c251f95b") #replace the key with your app Key
            # AdBuddiz.setTestModeActive() #test mode will be active
            AdBuddiz.cacheAds(PythonActivity.mActivity) #now we are caching the ads

        self.grid = [[None for iy in range(board_size)] for ix in range(board_size)]
        self.internal_grid = [[0 for iy in range(board_size)] for ix in range(board_size)]
        self.previous_state = None
        self.start_numbers = 6
        self.repetitions = 3
        self.animation_queue = []
        self.block_ui = False
        self.view_help = False
        if platform in ('windows', 'linux', 'macosx'):
            Window.size = (576, 1048)
        # bind keyboard
        Window.bind(on_key_down=self.on_key_down)
        Window.on_keyboard = lambda *x: None
        self.help_pages = []
        self.shown_help_pages = [False, False, False, False]
        self.help_backrgound = Image(size = (5000, 5000), pos = (0, 0), color = (0xfa / 255., 0xf8 / 255., 0xef / 255., 1.), allow_stretch = True, keep_ratio = False)
        for i in range(4):
            self.help_pages.append(Image(pos = (Window.size[0], 0), size = Window.size, source = 'data/help_%i.png' % (i + 1), allow_stretch = True))

        self.arrow = [[0, 0], [0, 0], 0]
        self.generate_arrow()
        self.arrow_widget = None

        self.restart(mode = 'resume')

    def possible_moves(self, ix_from, iy_from):
        for ix_delta in [-2, -1, 1, 2]:
            for iy_delta in [(3 - abs(ix_delta)), -(3 - abs(ix_delta))]:
                if (0 <= (ix_from + ix_delta) < board_size) and (0 <= (iy_from + iy_delta) < board_size) and (self.internal_grid[ix_from + ix_delta][iy_from + iy_delta] == 0):
                    yield ix_from + ix_delta, iy_from + iy_delta

    def temp_iterate(self):
        for ix in range(board_size):
            for iy in range(board_size):
                if self.internal_grid[ix][iy] != 0:
                    yield ix, iy

    def temp_iterate_empty(self):
        for ix in range(board_size):
            for iy in range(board_size):
                if self.internal_grid[ix][iy] == 0:
                    yield ix, iy

    def check_combination_temp(self, ix_in, iy_in):
        score = 0
        n_combs = 0
        for ix in range(board_size):
            for iy in range(board_size):
                if abs(ix - ix_in) * abs(iy - iy_in) == 2 and self.internal_grid[ix][iy] == self.internal_grid[ix_in][iy_in] != 0:
                    self.internal_grid[ix][iy] = 0
                    n_combs += 1
        if n_combs > 0:
            self.internal_grid[ix_in][iy_in] += n_combs
            score += self.internal_grid[ix_in][iy_in]
            score += self.check_combination_temp(ix_in, iy_in)
        return score

    def generate_arrow(self):
        internal_grid_temp = [[self.internal_grid[ix][iy] for iy in range(board_size)] for ix in range(board_size)]
        move_score = 0
        num_empty = len([1 for i in self.temp_iterate_empty()])
        move = [[], []]
        move[0] = [int(random() * board_size), int(random() * board_size)]
        invalid = True
        while invalid:
            delta = ([[ix, (3 - abs(ix))] for ix in [-2, -1, 1, 2]] + [[ix, -(3 - abs(ix))] for ix in [-2, -1, 1, 2]])[int(random() * 8)]
            move[1] = [move[0][i] + delta[i] for i in range(2)]
            invalid = any([not(0 <= move[1][i] < board_size) for i in range(2)])
        num_moves = sum([len([1 for i in self.possible_moves(ix, iy)]) for ix, iy in self.temp_iterate()])
        print num_moves

        for ix_from, iy_from, cube in self.iterate():
            for ix_to, iy_to in self.possible_moves(ix_from, iy_from):
                self.internal_grid[ix_to][iy_to] = self.internal_grid[ix_from][iy_from]
                self.internal_grid[ix_from][iy_from] = 0
                temp_score = self.check_combination_temp(ix_to, iy_to)
                temp_score += 0.5 * (len([1 for i in self.temp_iterate_empty()]) - num_empty)
                temp_num_moves = sum([len([1 for i in self.possible_moves(ix, iy)]) for ix, iy in self.temp_iterate()])
                temp_score += 0.1 * (temp_num_moves - num_moves)
                if temp_score > move_score:
                    move_score = temp_score
                    move = [[ix_from, iy_from], [ix_to, iy_to]]
                print temp_score, move_score, [[ix_from, iy_from], [ix_to, iy_to]], move, temp_num_moves
                self.internal_grid = [[internal_grid_temp[ix][iy] for iy in range(board_size)] for ix in range(board_size)]
        self.arrow = move + [self.arrow[2]]
        print move_score, move

    def arrow_size(self):
        return [[5.**0.5, 1.][i] * self.size[i] / board_size for i in range(2)]

    def arrow_angle(self):
        angle = math.atan2(float(self.arrow[1][1] - self.arrow[0][1]), float(self.arrow[1][0] - self.arrow[0][0])) / math.pi * 180
        print angle
        return angle

    def arrow_position(self):
        print self.pos, self.size
        position = [(self.arrow[0][i] + [0.45, -0.08][i]) for i in range(2)]
        print position
        return position

    def on_key_down(self, window, key, *args):
        if key == 27:
            if self.view_help:
                for i in range(4):
                    if self.shown_help_pages[i]:
                        Window.remove_widget(self.help_pages[i])
                        self.shown_help_pages[i] = False
                Window.remove_widget(self.help_backrgound)
                self.view_help = False

    def hint(self):
        # self.arrow[2] = 1 - self.arrow[2]
        self.arrow[2] = 1
        if self.arrow[2] == 1:
            if self.arrow_widget is not None:
                self.remove_widget(self.arrow_widget)
            self.generate_arrow()
            self.arrow_widget = RotatedImage(pos=self.index_to_pos(*self.arrow_position()), size=self.arrow_size(),
                                             source='data/arrow.png', angle=self.arrow_angle())
            self.add_widget(self.arrow_widget)
        else:
            self.remove_widget(self.arrow_widget)
            self.arrow_widget = None
        self.arrow[2] = 0

    def help(self):
        Window.add_widget(self.help_backrgound)
        Window.add_widget(self.help_pages[0])
        Animation(pos=(0,0), d = 0.1).start(self.help_pages[0])
        self.shown_help_pages[0] = True
        self.shown_help_page = 0
        self.view_help = True

    def rebuild_background(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0xbb / 255., 0xad / 255., 0xa0 / 255.)
            BorderImage(pos=self.pos, size=self.size, source='data/round.png')
            Color(0xcc / 255., 0xc0 / 255., 0xb3 / 255.)
            csize = self.cube_size, self.cube_size
            for ix, iy in self.iterate_pos():
                BorderImage(pos=self.index_to_pos(ix, iy), size=csize, source='data/round.png')

    def reposition(self, *args):
        self.rebuild_background()
        # calculate the size of a number
        l = min(self.width, self.height)
        padding = (l / board_size) / board_size
        cube_size = (l - (padding * (board_size + 1))) / board_size
        self.cube_size = cube_size
        self.cube_padding = padding

        for ix, iy, number in self.iterate():
            number.size = cube_size, cube_size
            number.pos = self.index_to_pos(ix, iy)
        if self.arrow_widget is not None:
            self.arrow_widget.pos = self.index_to_pos(*self.arrow_position())
            self.arrow_widget.size = self.arrow_size()

    def iterate(self):
        for ix, iy in self.iterate_pos():
            child = self.grid[ix][iy]
            if child is not None:
                yield ix, iy, child

    def iterate_empty(self):
        for ix, iy in self.iterate_pos():
            child = self.grid[ix][iy]
            if not child:
                yield ix, iy

    def iterate_pos(self):
        for ix in range(board_size):
            for iy in range(board_size):
                yield ix, iy

    def index_to_pos(self, ix, iy):
        padding = self.cube_padding
        cube_size = self.cube_size
        return [
            (self.x + padding) + ix * (cube_size + padding),
            (self.y + padding) + iy * (cube_size + padding)]

    def pos_to_index(self, x, y):
        padding = self.cube_padding
        cube_size = self.cube_size
        return [
            int((x - (self.x + padding)) / (cube_size + padding)),
            int((y - (self.y + padding)) / (cube_size + padding))]

    def check_blocked(self, ix_in, iy_in):
        for ix, iy in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
            if 0 <= ix_in + ix < board_size and 0 <= iy_in + iy < board_size:
                if self.grid[ix_in + ix][iy_in + iy] is None:
                    return False
        return True

    def spawn_number(self, value = None, total = 1, count = 1):
        empty = list(self.iterate_empty())
        if value is None:
            if not empty:
                return
            n_min, n_max = self.minimum_number(), self.maximum_number()
            n_low = max(1, min(n_min, n_max - 8 - (n_max + 1) / 2))
            n_high = min(n_max, n_min + 1)
            n_low, n_high = 1, max(2, n_max - 1)
            r = random()
            value = int(round(r**8 * (n_high - n_low) + n_low))
            # value = 1 if random() < 2./3. else 2
            if self.count_number(self.minimum_number()) == 1:
                value = self.minimum_number()

        ix, iy = choice(empty)
        self.spawn_number_at(ix, iy, value)
        self.check_combination(ix, iy)
        if count < total:
            self.animation_queue.append((total, count + 1, 'new'))
        self.animate_combination()

    def spawn_number_at(self, ix, iy, value):
        number = Number(
                size=(self.cube_size, self.cube_size),
                pos=self.index_to_pos(ix, iy),
                number=value)
        self.grid[ix][iy] = number
        self.internal_grid[ix][iy] = value
        self.add_widget(number)

    def count_number(self, n):
        counts = 0
        for cubes in self.internal_grid:
            for cube in cubes:
                if cube == n:
                    counts += 1
        return counts

    def minimum_number(self):
        numbers = []
        for cubes in self.internal_grid:
            for cube in cubes:
                if cube != 0:
                    numbers.append(cube)
        if len(numbers) == 0:
            return 1
        else:
            return min(numbers)

    def maximum_number(self):
        numbers = []
        for cubes in self.internal_grid:
            for cube in cubes:
                if cube != 0:
                    numbers.append(cube)
        if len(numbers) == 0:
            return 1
        else:
            return max(numbers)

    def on_touch_up(self, touch):
        if self.view_help:
            if touch.pos[0] - touch.opos[0] > 50:
                if self.shown_help_page > 0:
                    Animation(pos=(Window.size[0], 0), d = 0.1).start(self.help_pages[self.shown_help_page])
                    # Window.remove_widget(self.help_pages[self.shown_help_page])
                    # self.shown_help_pages[self.shown_help_page] = False
                    self.shown_help_page -= 1
                    # Animation(pos=(0, 0), d = 0.1).start(self.help_pages[self.shown_help_page])
            if touch.opos[0] - touch.pos[0] > 50:
                if self.shown_help_page < 3:
                    self.shown_help_page += 1
                    Animation(pos=(0, 0), d = 0.1).start(self.help_pages[self.shown_help_page])
                    if not self.shown_help_pages[self.shown_help_page]:
                        Window.add_widget(self.help_pages[self.shown_help_page])
                    self.shown_help_pages[self.shown_help_page] = True
            return
        if self.block_ui:
            return
        selected = None
        for ix, cubes in enumerate(self.grid):
            for iy, cube in enumerate(cubes):
                if cube is not None:
                    if cube.collide_point(*touch.opos):
                        selected = cube
                        ix_from, iy_from = self.pos_to_index(*touch.opos)
        if selected is None:
            return

        ix_to, iy_to = self.pos_to_index(*touch.pos)
        if not(0 <= ix_to < board_size) or not(0 <= iy_to < board_size):
            return
        if abs(ix_to - ix_from) * abs(iy_to - iy_from) == 2 and self.grid[ix_to][iy_to] is None:
            self.previous_state = [[self.internal_grid[ix][iy] for iy in range(board_size)] for ix in range(board_size)]
            self.grid[ix_to][iy_to] = self.grid[ix_from][iy_from]
            self.grid[ix_from][iy_from] = None
            self.internal_grid[ix_from][iy_from] = 0
            self.internal_grid[ix_to][iy_to] = self.grid[ix_to][iy_to].number
            pos = self.index_to_pos(ix_to, iy_to)
            self.animation_queue.append((ix_to, iy_to, Animation(pos=pos, d=animation_delay, t='out_quad')))
            # if self.arrow[2] == 1:
            if self.arrow_widget is not None:
                self.remove_widget(self.arrow_widget)
                self.arrow_widget = None
        else:
            return None

        self.check_combination(ix_to, iy_to)
        self.animation_queue.append((self.repetitions, 0, 'new'))
        self.animate_combination()
        # for i in range(self.repetitions):
        #     self.spawn_number()
        self.check_legal_move()
        return True

    def undo(self):
        if self.previous_state is None or self.ids.end.opacity == 1 or self.ids.yesno.opacity == 1:
            return
        for ix, iy, cube in self.iterate():
                self.grid[ix][iy].parent.remove_widget(self.grid[ix][iy])
        for ix in range(board_size):
            for iy in range(board_size):
                self.internal_grid[ix][iy] = self.previous_state[ix][iy]
                if self.internal_grid[ix][iy] == 0:
                    self.grid[ix][iy] = None
                else:
                    self.grid[ix][iy] = Number(size=(self.cube_size, self.cube_size), pos=self.index_to_pos(ix, iy), number=self.internal_grid[ix][iy])
                    self.add_widget(self.grid[ix][iy])
                    # Animation(pos = self.grid[ix][iy].pos, d = 0.01).start(self.grid[ix][iy])
        self.ids.end.opacity = 0
        self.ids.yesno.opacity = 0
        # self.reposition()

    def animate_combination(self, *args):
        self.block_ui = True
        if len(self.animation_queue) > 0:
            ix, iy, a = self.animation_queue.pop(0)
            if type(a) == str:
                if a == 'dummy':
                    if self.grid[ix][iy] is not None:
                        anim = Animation(pos=self.grid[ix][iy].pos, d=animation_delay, t='out_quad')
                        anim.bind(on_complete = self.animate_combination)
                        anim.start(self.grid[ix][iy])
                        # sleep(animation_delay)
                if a == 'destroy':
                    if self.grid[ix][iy] is not None:
                        # sleep(animation_delay)
                        self.grid[ix][iy].parent.remove_widget(self.grid[ix][iy])
                        self.grid[ix][iy] = None
                        self.animate_combination()
                        # Clock.schedule_once(lambda x: self.animate_combination(), 1.0)
                if a == 'new':
                    Clock.schedule_once(lambda x: self.spawn_number(total = ix, count = iy), animation_delay)
                    self.check_end()
                    # self.spawn_number(total = ix, count = iy)
            elif type(a) == int:
                if self.grid[ix][iy] is not None:
                    # sleep(animation_delay)
                    self.grid[ix][iy].number = a
                    self.score += self.grid[ix][iy].number
                    self.animate_combination()
                    # Clock.schedule_once(lambda x: self.animate_combination(), 1.0)
            else:
                if self.grid[ix][iy] is not None:
                    # sleep(animation_delay)
                    a.bind(on_complete = lambda x, y: self.animate_combination())
                    a.start(self.grid[ix][iy])
                    # self.animate_combination()
        else:
            self.check_end()
            self.max_num = self.maximum_number()
            self.block_ui = False
            if self.arrow[2] == 1:
                if self.arrow_widget is not None:
                    self.remove_widget(self.arrow_widget)
                self.generate_arrow()
                self.arrow_widget = RotatedImage(pos=self.index_to_pos(*self.arrow_position()), size=self.arrow_size(),
                                                 source='data/arrow.png', angle=self.arrow_angle())
                self.add_widget(self.arrow_widget)

    def check_combination(self, ix_in, iy_in):
        n_combs = 0
        for ix in range(board_size):
            for iy in range(board_size):
                if abs(ix - ix_in) * abs(iy - iy_in) == 2 and self.internal_grid[ix][iy] == self.internal_grid[ix_in][iy_in] != 0:
                    self.animation_queue.append((ix, iy, Animation(pos=self.index_to_pos(ix_in, iy_in), d=animation_delay, t='out_quad')))
                    self.animation_queue.append((ix, iy, 'dummy'))
                    self.animation_queue.append((ix, iy, 'destroy'))
                    self.internal_grid[ix][iy] = 0
                    n_combs += 1
        if n_combs > 0:
            self.internal_grid[ix_in][iy_in] += n_combs
            self.animation_queue.append((ix_in, iy_in, 'dummy'))
            self.animation_queue.append((ix_in, iy_in, self.internal_grid[ix_in][iy_in]))
            self.check_combination(ix_in, iy_in)

    def check_end(self):
        # we still have empty space
        if any(self.iterate_empty()):
            return False

        self.end()
        return True

    def check_legal_move(self):
        # we still have a legal move here
        for ix in range(board_size):
            for iy in range(board_size):
                for dx, dy in [[-2, -1], [-2, 1], [-1, -2], [-1, 2], [1, -2], [1, 2], [2, -1], [2, 1]]:
                    if 0 <= ix + dx < board_size and 0 <= iy + dy < board_size and self.internal_grid[ix + dx][iy + dy] == 0:
                        return True

        self.end()
        return True

    def ask_restart(self):
        yesno = self.ids.yesno.__self__
        self.remove_widget(yesno)
        self.add_widget(yesno)
        Animation(opacity=1., d=.5).start(yesno)

    def end(self):
        end = self.ids.end.__self__
        self.remove_widget(end)
        self.add_widget(end)
        text = 'Game\nover!'
        for ix, iy, cube in self.iterate():
            if cube.number >= 19:
                text = 'WIN !'
        self.ids.end_label.text = text
        if store.exists('state'):
            store.delete('state')
        Animation(opacity=1., d=.5).start(end)

    def restart(self, mode = 'normal'):
        if platform == 'android':
            AdBuddiz.showAd(PythonActivity.mActivity)
        self.score = 0
        self.best_number = 0
        self.best_score = 0
        if store.exists('scores'):
            self.best_number = store.get('scores')['max_number']
            self.best_score = store.get('scores')['max_score']
        for ix, iy, child in self.iterate():
            child.destroy()
        if store.exists('state') and mode != 'normal':
            self.internal_grid = store.get('state')['grid']
            self.grid = [[]]
            for ix in range(board_size):
                for iy in range(board_size):
                    if self.internal_grid[ix][iy] == 0:
                        element = None
                    else:
                        element = Number()
                        element.number = self.internal_grid[ix][iy]
                        self.add_widget(element)
                    self.grid[ix].append(element)
                self.grid.append([])
            self.score = store.get('state')['score']
            self.max_num = store.get('state')['max_num']
            self.reposition()
        else:
            self.grid = [[None for iy in range(board_size)] for ix in range(board_size)]
            self.internal_grid = [[0 for iy in range(board_size)] for ix in range(board_size)]
            self.reposition()
            for i in range(self.start_numbers):
                self.spawn_number()
            # for i in range(40):
            #     self.spawn_number(int(-math.log(random()) * 4 + 1))
                # self.spawn_number()
            # for i in range(30):
            #     self.spawn_number(i + 1)
            self.score = 0
        self.previous_state = None
        self.ids.yesno.opacity = 0
        self.ids.end.opacity = 0

    def no_restart(self):
        self.ids.yesno.opacity = 0

class GameK19App(App):
    use_kivy_settings = False

    def build_config(self, config):
        pass

    def build(self):
        global app
        app = self

    def store_state(self):
        scores = {'max_number': 0, 'max_score': 0}
        if self.root.ids.game.max_num > self.root.ids.game.best_number:
            scores['max_number'] = self.root.ids.game.max_num
        if self.root.ids.game.score > self.root.ids.game.best_score:
            scores['max_score'] = self.root.ids.game.score
        store.put('scores', **scores)
        store.put('state', grid = self.root.ids.game.internal_grid, score = self.root.ids.game.score, max_num = self.root.ids.game.max_num)

    def on_pause(self):
        self.store_state()
        return True

    def on_stop(self):
        self.store_state()

    def on_resume(self):
        pass

    def _on_keyboard_settings(self, *args):
        return

if __name__ == '__main__':
    GameK19App().run()
