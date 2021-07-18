import gym
from gym import spaces
from pywinauto import Application
from time import sleep
from psutil import Process
import re
import numpy as np
from PIL import Image
from time import perf_counter
from win32gui import GetClientRect, GetWindowDC, DeleteObject, ReleaseDC
from win32ui import CreateDCFromHandle, CreateBitmap
from ctypes import WinDLL
from ctypes.wintypes import HWND
from decorator import decorator
from ahk.window import Window
from ahk.keys import KEYS
from ahk import AHK





@decorator
def try_loop(func, error_type=RuntimeError, *args, **kwargs):
    """executes func until it runs without throwing error_type"""
    while True:
        try:
            result = func(*args, **kwargs)
        except error_type as e:
            print(e)
        else:
            break
    return result


class SoullessEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    user32 = WinDLL("user32")
    DEATHCOUNT_PATTERN = re.compile("(\d+)")
    KEYS = (KEYS.LEFT, KEYS.RIGHT, KEYS.SHIFT)
    TRANSITION_TO_ACTION = {"10": "UP", "01": "DOWN", "00": False, "11": False}

    def __init__(self):
        self.AHK = AHK()
        self.application = self.start_game()
        self.process_id = self.application.process
        self.process = Process(pid=self.process_id)
        self.dialog = self.get_window_dialog()
        self.handle = self.dialog.handle
        self.window = Window.from_pid(self.AHK, self.process_id)

        left, top, right, bot = GetClientRect(self.handle)
        w = right - left
        h = bot - top

        self.hwndDC = GetWindowDC(self.handle)
        self.mfcDC = CreateDCFromHandle(self.hwndDC)
        self.saveDC = self.mfcDC.CreateCompatibleDC()
        self.saveDC_handle = self.saveDC.GetSafeHdc()

        self.saveBitMap = CreateBitmap()
        self.saveBitMap.CreateCompatibleBitmap(self.mfcDC, w, h)
        self.bmpinfo = self.saveBitMap.GetInfo()
        self.saveDC.SelectObject(self.saveBitMap)

        self.navigate_main_menu()
        self.enter_avoidance()
        self.process.suspend()

        self.PREVIOUS_ACTION = 0
        self.deathcount = self.get_game_deathcount()
        self.action_space = spaces.Discrete(6)
        self.observation_space = spaces.Box(low=0, high=255, shape=self.get_observation_space_size())

    def start_game(self):
        """starts the Soulless process"""
        app = Application().start("D:/Users/david/PycharmProjects/reinforcement-learning/gym-soulless/Soulless 1.3HM/Soulless Hard Mode.exe")
        return app

    def get_window_dialog(self):
        """:returns the main dialog of the application, which is the entry-point for interacting with it"""
        return self._top_window()

    @try_loop(error_type=RuntimeError)
    def _top_window(self):
        return self.application.top_window()

    def navigate_main_menu(self):
        """from the title screen it navigates the menus until it enters the game"""
        self.window.send("{Shift}", blocking=False)
        sleep(3)
        self.window.send("{Shift}", blocking=False)

    def enter_avoidance(self):
        self.window.send("{Left down}", blocking=False)
        sleep(0.1)
        self.window.send("{Left up}", blocking=False)
        sleep(2)

    def capture_window(self):
        """:returns a np array image of the dialog cropped to exclude the margins for resizing the window
        https://stackoverflow.com/questions/19695214/python-screenshot-of-inactive-window-printwindow-win32gui"""

        SoullessEnv.user32.PrintWindow(HWND(self.handle), self.saveDC_handle, 3)
        bmpstr = self.saveBitMap.GetBitmapBits(True)

        im = Image.frombuffer(
            'RGB',
            (self.bmpinfo['bmWidth'], self.bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)
        return np.array(im, copy=False)

    def step(self, action: int):
        """expects the game to be in a suspended state"""
        is_done, obs, reward = self.step_and_track_elapsed_time(action)
        return obs, reward, is_done, {}

    def step_and_track_elapsed_time(self, action):
        self.process.resume()
        step_start_time = perf_counter()
        is_done, obs = self._step(action)
        self.process.suspend()
        step_end_time = perf_counter()
        elapsed_time = step_end_time - step_start_time
        return is_done, obs, elapsed_time

    def _step(self, action):
        is_done = self.is_done()
        self.update_env_deathcount()
        obs = self.capture_window()
        self.perform_action(action)
        return is_done, obs

    def perform_action(self, action):
        keystrokes = self.get_action_transition(self.PREVIOUS_ACTION, action)
        self.send_input_to_game(keystrokes)
        self.PREVIOUS_ACTION = action

    def is_done(self):
        return self.get_game_deathcount() > self.deathcount

    def update_env_deathcount(self):
        self.deathcount = self.get_game_deathcount()

    def get_action_transition(self, old_action: int, new_action: int):
        """:param old_action is the action performed on the previous step, or no-op if this is the first step
        :param new_action is the action performed on this step
        :returns the input to the send function needed to transition from the old action to the new action"""

        old_action, new_action = bin(old_action)[2:].zfill(3), bin(new_action)[2:].zfill(3)
        actions = map(SoullessEnv.TRANSITION_TO_ACTION.get, map("".join, zip(old_action, new_action)))

        return "".join(getattr(key, action) for key, action in zip(SoullessEnv.KEYS, actions) if action)

    def send_input_to_game(self, keystrokes: str):
        """:param keystrokes is the input to the send_keys function"""
        self.window.send(keystrokes, blocking=False)

    def reset(self):
        self.process.resume()
        self.window.send("r", delay=70)
        self.process.suspend()

        return self.capture_window()

    def render(self, mode='human'):
        pass

    def close(self):
        DeleteObject(self.saveBitMap.GetHandle())
        self.saveDC.DeleteDC()
        self.mfcDC.DeleteDC()
        ReleaseDC(self.handle, self.hwndDC)
        self.application.kill()

    def get_observation_space_size(self):
        return tuple([*self.capture_window().shape, 3])

    def get_game_deathcount(self):
        """:returns the number of times the kid has died"""
        title = self.window.title.decode("utf8")
        return int(re.search(SoullessEnv.DEATHCOUNT_PATTERN, title)[0])



