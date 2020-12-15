from gym.envs.registration import register

register(
    id='soulless-v0',
    entry_point='gym_soulless.envs:SoullessEnv',
)
register(
    id='soulless-extrahard-v0',
    entry_point='gym_soulless.envs:SoullessExtraHardEnv',
)