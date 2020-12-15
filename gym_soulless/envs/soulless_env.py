import gym
from gym import error, spaces, utils
from gym.utils import seeding
from pywinauto import Application, findwindows
from pywinauto.keyboard import send_keys
from time import sleep


class SoullessEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        app = self.start_game()
        self.dialog = self.get_window_dialog(app)
        self.navigate_main_menu()

    def start_game(self):
        Application().start(r"C:\Programs\Fangames\Soulless 1.3HM\Soulless Hard Mode(1).exe")
        app = Application().connect(title_re="Soulless.*", timeout=10)
        return app

    def get_window_dialog(self, application):
        dialog = application.top_window()
        dialog.set_focus()
        return dialog

    def navigate_main_menu(self):
        """from the title screen it navigates the menus until it enters the game"""
        send_keys("{VK_LSHIFT down} {VK_LSHIFT up}")
        print("pressing shift")
        sleep(3)
        send_keys("{VK_LSHIFT down} {VK_LSHIFT up}")


    def capture_window(self, dialog):
        """:param dialog is a window dialog
        :returns a PIL image of the dialog"""
        image = dialog.capture_as_image()
        return image

    def step(self, action):
        pass

    def reset(self):
        pass

    def render(self, mode='human'):
        pass

    def close(self):
        pass


