from ray.rllib.agents.ppo import PPOTrainer
import gym
from assets import game,team


class G_environment(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 4}
    def __init__(self,config) -> None:
        self.create_game()
        self.action_space = gym.spaces.Tuple((
            #'mvFrom':
                gym.spaces.Tuple(
                    (gym.spaces.Discrete(8),gym.spaces.Discrete(8))
                ),
            #, 'mvTo':
                gym.spaces.Tuple(
                    (gym.spaces.Discrete(8),gym.spaces.Discrete(8))
                )
        ))
        self.observation_space = gym.spaces.Tuple(gym.spaces.Tuple(
            (gym.spaces.Discrete(8),gym.spaces.Discrete(8),gym.spaces.Discrete(5))
        ) for x in range(32))   

    def render(self, action, mode="human"):
        return print(self.G.board.show() + f'\nteam1:{self.team1.score} | team2:{self.team2.score}' + f'\naction: {action}' + f'\n\n\n {self.G.observation()}')

    def create_game(self):
        self.G = game()
        self.team1 = team(0)
        self.team2 = team(2)
        self.G.create_game(self.team1,self.team2)
        self.team1.join_game(self.G)
        self.team2.join_game(self.G)

    def reset(self):
        self.create_game()
        self.render(action='reset board')
        return self.G.observation()

    def step(self,action):
        start_reward = self.team1.score
        self.team1.move(*action)
        if self.G.finished:
            self.render(action)
            reward = self.team1.score - start_reward
            return self.G.observation(),reward,self.G.finished,{}
        if self.G.initiative is self.team2:
            self.team2.move(**self.G.random_move(self.team2))
            self.render(action)
        reward = self.team1.score - start_reward
        return self.G.observation(),reward,self.G.finished,{}









# Create an RLlib Trainer instance.
trainer = PPOTrainer(
    config={
        # Env class to use (here: our gym.Env sub-class from above).
        "env": G_environment,
        # Config dict to be passed to our custom env's constructor.
        "env_config": {
            # Use corridor with 20 fields (including S and G).
            # "corridor_length": 20
        },
        # Parallelize environment rollouts.
        "num_workers": 6,
    })

# Train for n iterations and report results (mean episode rewards).
# Since we have to move at least 19 times in the env to reach the goal and
# each move gives us -0.1 reward (except the last move at the end: +1.0),
# we can expect to reach an optimal episode reward of -0.1*18 + 1.0 = -0.8
for i in range(250):
    results = trainer.train()
    print(f"Iter: {i}; avg. reward={results['episode_reward_mean']}")

# Perform inference (action computations) based on given env observations.
# Note that we are using a slightly different env here (len 10 instead of 20),
# however, this should still work as the agent has (hopefully) learned
# to "just always walk right!"
env = G_environment({})
# Get the initial observation (should be: [0.0] for the starting position).
obs = env.reset()
done = False
total_reward = 0.0
# Play one episode.
while not done:
    # Compute a single action, given the current observation
    # from the environment.
    action = trainer.compute_single_action(obs)
    # Apply the computed action in the environment.
    obs, reward, done, info = env.step(action)
    # Sum up rewards for reporting purposes.
    total_reward += reward
# Report results.
print(f"Played 1 episode; total-reward={total_reward}")