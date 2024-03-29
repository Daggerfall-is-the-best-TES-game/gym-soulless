from gym import make
from gym_soulless.envs import SoullessEnv

if __name__ == "__main__":
    # envs = [make("soulless-v0") for x in range(5)]
    # RUNS = 1
    # for env in envs:
    #     for x in range(RUNS):
    #         total_reward = 0.0
    #         total_steps = 0
    #         obs = env.reset()
    #         done = False
    #
    #         while not done:
    #             action = env.action_space.sample()
    #             obs, reward, done, _ = env.step(action)
    #             total_reward += reward
    #             total_steps += 1
    #
    #         print(f"Episode done in {total_steps:d}, total reward {total_reward:.2f}")
    #
    #     env.close()

    envs = [make("soulless-v0") for x in range(1)]
    for env in envs:
        env.reset()
    total_reward = [0] * len(envs)
    while True:
        for env_idx, env in enumerate(envs):

            obs, reward, done, _ = env.step(env.action_space.sample())
            total_reward[env_idx] += reward
            if done:
                print(f"{env_idx}: {total_reward}")
                print(env.deathcount)
                total_reward[env_idx] = 0
                env.reset()


