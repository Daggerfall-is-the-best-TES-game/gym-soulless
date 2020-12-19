from gym_soulless.envs import SoullessEnv
from gym import make
from time import sleep


env = make("soulless-v0")
for action in range(6):
    for _ in range(15):
        env.step(action)
        sleep(0.2)
