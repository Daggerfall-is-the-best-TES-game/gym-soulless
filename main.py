from gym import make
from gym_soulless.envs import SoullessEnv

if __name__ == "__main__":
    env = make("soulless-v0")
    RUNS = 10
    for x in range(RUNS):
        total_reward = 0.0
        total_steps = 0
        obs = env.reset()
        done = False

        while not done:
            action = env.action_space.sample()
            obs, reward, done, _ = env.step(action)
            total_reward += reward
            total_steps += 1

        print(f"Episode done in {total_steps:d}, total reward {total_reward:.2f}")

    env.close()
