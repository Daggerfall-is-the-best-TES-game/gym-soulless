## Fangame AI Project
The purpose of this project is to develop and train an AI to play the game “Soulless Hardmode” at a superhuman level. The plan is to create an openai gym environment out of Soulless Hardmode, which can be used in a “dropin” fashion with the code I already have for Deep-Q learning. Hopefully this will be sufficient to achieve my goal.
In order to create an openai gym environment, I need Python to be able to interact with the game in three ways.
1. Python must have access to the game screen to create observations
2. Python must be able to send input to the game to perform actions
3. Python must be able to detect when the player has died or beaten the game to trigger the end of an episode
4. need to be able to control framerate for stepping through the environment
