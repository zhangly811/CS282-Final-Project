# This gridworld was created by Ken Arnold and Allen Schmaltz as part
# of the 2015 offering of CS282 at Harvard; I've adapted things just
# slightly to make for a very simple tutorial.  

import numpy as np

# Maze state is represented as a 2-element NumPy array: (Y, X). Increasing Y is South.

# Possible actions, expressed as (delta-y, delta-x).
maze_actions = {
    'N': np.array([-1, 0]),
    'S': np.array([1, 0]),
    'E': np.array([0, 1]),
    'W': np.array([0, -1]),
}

def parse_topology(topology):
    return np.array([list(row) for row in topology])


class Maze(object):
    """
    Simple wrapper around a NumPy 2D array to handle flattened indexing and staying in bounds.
    """
    def __init__(self, topology):
        self.topology = parse_topology(topology)
        self.flat_topology = self.topology.ravel()
        self.shape = self.topology.shape

    def in_bounds_flat(self, position):
        return 0 <= position < np.product(self.shape)

    def in_bounds_unflat(self, position):
        return 0 <= position[0] < self.shape[0] and 0 <= position[1] < self.shape[1]
    
    # translation: position and topo sign 
    def get_flat(self, position):
        if not self.in_bounds_flat(position):
            raise IndexError("Position out of bounds: {}".format(position))
        return self.flat_topology[position]

    def get_unflat(self, position):
        if not self.in_bounds_unflat(position):
            raise IndexError("Position out of bounds: {}".format(position))
        return self.topology[tuple(position)]

    # # translation: 2d index and position index
    def flatten_index(self, index_tuple):
        return np.ravel_multi_index(index_tuple, self.shape)

    def unflatten_index(self, flattened_index):
        return np.unravel_index(flattened_index, self.shape)

    def flat_positions_containing(self, x):
        return list(np.nonzero(self.flat_topology == x)[0])

    def flat_positions_not_containing(self, x):
        return list(np.nonzero(self.flat_topology != x)[0])

    def __str__(self):
        return '\n'.join(''.join(row) for row in self.topology.tolist())

    def __repr__(self):
        return 'Maze({})'.format(repr(self.topology.tolist()))


def move_avoiding_walls(maze, position, action):
    """
    Return the new position after moving, and the event that happened ('hit-wall' or 'moved').

    Works with the position and action as a (row, column) array.
    """
    # Compute new position
    new_position = position + action

    # Compute collisions with walls, including implicit walls at the ends of the world.
    if not maze.in_bounds_unflat(new_position) or maze.get_unflat(new_position) == '#':
        return position, 'hit-wall'

    return new_position, 'moved'

class GridWorld(object):
    """
    A simple task in a maze: get to the goal.

    Parameters
    ----------

    maze : list of strings or lists
        maze topology (see below)

    rewards: dict of string to number. default: {'*': 10}.
        Rewards obtained by being in a maze grid with the specified contents,
        or experiencing the specified event (either 'hit-wall' or 'moved'). The
        contributions of content reward and event reward are summed. For
        example, you might specify a cost for moving by passing
        rewards={'*': 10, 'moved': -1}.

    terminal_markers: sequence of chars, default '*'
        A grid cell containing any of these markers will be considered a
        "terminal" state.

    action_error_prob: float
        With this probability, the requested action is ignored and a random
        action is chosen instead.

    Notes
    -----

    Maze topology is expressed textually. Key:
     '#': wall
     '.': open (really, anything that's not '#')
     '*': goal
     'o': origin
     'X': pitfall
    """

    def __init__(self, maze, rewards={'*': 10}, terminal_markers='*', walls = '#', action_error_prob=0, directions="NSEW" ):

        self.maze = Maze(maze) if not isinstance(maze, Maze) else maze
        self.rewards = rewards
        self.terminal_markers = terminal_markers
        self.walls = walls
        self.action_error_prob = action_error_prob

        self.actions = [maze_actions[direction] for direction in directions]
        self.num_actions = len(self.actions)
        self.state = None
        self.reset()
        self.num_states = self.maze.shape[0] * self.maze.shape[1]
        
        
    def __repr__(self):
        return 'GridWorld(maze={maze!r}, rewards={rewards}, terminal_markers={terminal_markers}, action_error_prob={action_error_prob})'.format(**self.__dict__)

    def reset(self):
        """
        Reset the position to a starting position (an 'o'), chosen at random.
        """
        # Since only one 'o' in the maze, so always start at the same position???
        options = self.maze.flat_positions_not_containing('*')
        self.state = int(options[ np.random.choice(len(options)) ])

    def is_terminal(self, state):
        """Check if the given state is a terminal state."""
        return self.maze.get_flat(state) in self.terminal_markers

    def is_wall(self, state):
        """Check if the given state is a wall state."""
        return self.maze.get_flat(state) in self.walls

    def observe(self):
        """
        Return the current state as an integer.

        The state is the index into the flattened maze.
        """
        return self.state

    def perform_action(self, action_idx):
        """Perform an action (specified by index), yielding a new state and reward."""
        # In the absorbing end state, nothing does anything.
        if self.is_terminal(self.state):
            return self.observe(), 0

        if self.action_error_prob and np.random.rand() < self.action_error_prob:
            # finale! this would be just pick any direction; we
            # changed it to be slip 90-degrees in some direction
            # action_idx = np.random.choice(self.num_actions)
            if np.random.rand() < .5:
                if action_idx == 0 or action_idx == 1:
                    action_idx = 2
                else: 
                    action_idx = 0
            else: 
                if action_idx == 0 or action_idx == 1:
                    action_idx = 3
                else: 
                    action_idx = 1
            
        action = self.actions[action_idx]
        # new_state_tuple = (3,3), result = "moved" or "hit wall"
        new_state_tuple, result = move_avoiding_walls(self.maze, self.maze.unflatten_index(self.state), action)
        self.state = self.maze.flatten_index(new_state_tuple)

        reward = self.rewards.get(self.maze.get_flat(self.state), 0) + self.rewards.get(result, 0)
        return self.observe(), reward
