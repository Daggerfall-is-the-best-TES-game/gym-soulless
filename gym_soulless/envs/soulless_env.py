import gym
from gym import error, spaces, utils
from gym.utils import seeding
from pywinauto import Application, findwindows
from pywinauto.keyboard import send_keys
from time import sleep
from psutil import Process
from pywinauto.timings import Timings
import re
import numpy as np
from PIL.ImageOps import crop


class SoullessEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    DEATHCOUNT_PATTERN = re.compile("(\d+)")
    KEYS = ("VK_LEFT", "VK_RIGHT", "VK_LSHIFT")
    TRANSITION_TO_ACTION = {"10": "up", "01": "down", "00": False, "11": False}
    def __init__(self):
        self.application = self.start_game()
        self.process_id = self.application.process
        self.process = Process(pid=self.process_id)
        self.dialog = self.get_window_dialog()
        self.navigate_main_menu()
        self.enter_avoidance()
        self.process.suspend()
        
        self.PREVIOUS_ACTION = 0
        self.deathcount = self.get_deathcount()
        self.action_space = spaces.Discrete(6)
        self.observation_space = spaces.Box(low=0, high=255, shape=self.get_observation_space_size())

    def start_game(self):
        """starts the Soulless process"""
        Application().start("Soulless 1.3HM/Soulless Hard Mode.exe")
        app = Application().connect(title_re="Soulless.*", timeout=20)
        return app

    def get_window_dialog(self):
        """:returns the main dialog of the application, which is the entry-point for interacting with it"""
        dialog = self.application.top_window()
        dialog.set_focus()
        return dialog

    def navigate_main_menu(self):
        """from the title screen it navigates the menus until it enters the game"""
        send_keys("{VK_LSHIFT down} {VK_LSHIFT up}")
        sleep(3)
        send_keys("{VK_LSHIFT down} {VK_LSHIFT up}")

    def enter_avoidance(self):
        send_keys("{VK_LEFT down}")
        send_keys("{VK_LEFT up}")
        sleep(2)


    def capture_window(self):
        """:returns a PIL image of the dialog cropped to exclude the margins for resizing the window"""
        return crop(self.dialog.capture_as_image(), (8, 0, 8, 7))

    def step(self, action: int):
        """expects the game to be in a suspended state"""
        self.dialog.set_focus()
        current_deathcount = self.get_deathcount()
        is_done = current_deathcount > self.deathcount
        self.deathcount = current_deathcount
        obs = np.array(self.capture_window())
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

        return "".join(f"{{{key} {action}}}" for key, action in zip(SoullessEnv.KEYS, actions) if action)

    def perform_action(self, keystrokes: str):
        """:param keystrokes is the input to the send_keys function"""
        self.process.resume()
        send_keys(keystrokes)
        self.process.suspend()

    def reset(self):
        self.process.resume()
        send_keys("{r down}")
        send_keys("{r up}")
        self.process.suspend()

    def render(self, mode='human'):
        pass

    def close(self):
        self.application.kill()

    def get_observation_space_size(self):
        return tuple([*self.capture_window().size, 3])

    def get_deathcount(self):
        """:returns the number of times the kid has died"""
        self.process.resume()
        title = self.dialog.texts()[0]
        self.process.suspend()
        return int(re.search(SoullessEnv.DEATHCOUNT_PATTERN, title)[0])



