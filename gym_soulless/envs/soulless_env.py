import gym
from gym import spaces
from pywinauto import Application
from time import sleep
from psutil import Process
import re
import numpy as np
from PIL import Image
from win32gui import GetClientRect, GetWindowDC, DeleteObject, ReleaseDC
from win32ui import CreateDCFromHandle, CreateBitmap
from ctypes import windll
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
    DEATHCOUNT_PATTERN = re.compile("(\d+)")
    KEYS = (KEYS.LEFT, KEYS.RIGHT, KEYS.SHIFT)
    TRANSITION_TO_ACTION = {"10": "UP", "01": "DOWN", "00": False, "11": False}

    def __init__(self):
        self.AHK = AHK()
        self.application = self.start_game()
        self.process_id = self.application.process
        self.process = Process(pid=self.process_id)
        sleep(10)
        self.window = Window.from_pid(self.AHK, self.process_id)
        self.dialog = self.get_window_dialog()
        self.handle = self.dialog.handle
        self.navigate_main_menu()
        self.enter_avoidance()
        self.process.suspend()

        self.PREVIOUS_ACTION = 0
        self.deathcount = self.get_deathcount()
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
        self.window.send("{Shift}")
        sleep(3)
        self.window.send("{Shift}")

    def enter_avoidance(self):
        self.window.send("{Left down}")
        sleep(0.1)
        self.window.send("{Left up}")
        sleep(2)

    def capture_window(self):
        """:returns a np array image of the dialog cropped to exclude the margins for resizing the window
        https://stackoverflow.com/questions/19695214/python-screenshot-of-inactive-window-printwindow-win32gui"""
        left, top, right, bot = GetClientRect(self.handle)
        w = right - left
        h = bot - top

        hwndDC = GetWindowDC(self.handle)
        mfcDC = CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

        saveDC.SelectObject(saveBitMap)

        result = windll.user32.PrintWindow(self.handle, saveDC.GetSafeHdc(), 3)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)

        DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        ReleaseDC(self.handle, hwndDC)
        return np.array(im)

    def step(self, action: int):
        """expects the game to be in a suspended state"""

        try:
            current_deathcount = self.get_deathcount()
            is_done = current_deathcount > self.deathcount
            self.deathcount = current_deathcount
        except TypeError as e:
            print("could not find deathcount")
            is_done = False
        obs = self.capture_window()
        keystrokes = self.get_action_transition(self.PREVIOUS_ACTION, action)
        self.perform_action(keystrokes)
        self.PREVIOUS_ACTION = action

        return obs, 1.0, is_done, {}

    def get_action_transition(self, old_action: int, new_action: int):
        """:param old_action is the action performed on the previous step, or no-op if this is the first step
        :param new_action is the action performed on this step
        :returns the input to the sendkeys function need to transition from the old action to the new action"""

        old_action, new_action = bin(old_action)[2:].zfill(3), bin(new_action)[2:].zfill(3)
        actions = map(SoullessEnv.TRANSITION_TO_ACTION.get, map("".join, zip(old_action, new_action)))

        return "".join(getattr(key, action) for key, action in zip(SoullessEnv.KEYS, actions) if action)

    def perform_action(self, keystrokes: str):
        """:param keystrokes is the input to the send_keys function"""
        self.process.resume()
        self.window.send(keystrokes)
        self.process.suspend()

    def reset(self):
        self.process.resume()
        self.window.send("r")
        self.process.suspend()

        return self.capture_window()

    def render(self, mode='human'):
        pass

    def close(self):
        self.application.kill()

    def get_observation_space_size(self):
        return tuple([*self.capture_window().shape, 3])

    def get_deathcount(self):
        """:returns the number of times the kid has died"""
        title = self.window.title.decode("utf8")
        return int(re.search(SoullessEnv.DEATHCOUNT_PATTERN, title)[0])



