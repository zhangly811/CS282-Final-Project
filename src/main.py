from mdp.builder import make_mdp
from mdp.solver import solve_mdp
from policy.policy import GreedyPolicy
from policy.custom_policy import get_physician_policy
from utils.utils import load_data, extract_trajectories
from irl.irl import *
from optimize.quad_opt import QuadOpt

# let us think about what we need purely
'''
- MDP: states, transitions, reward(just in case)
- phi, weights
- policy
- mdp solver: given T and R(phi*W), find the policy that minimizes the expected difference

todo
- make mdp builder work
    - fix transition matrix not summing to one
    - add load and save state centroids
    - find binary cols
- get the mvp irl workflow done
    - implement estimate feature expectation
    - implement naive phi
    - implement reward function
    - implement state value estimation function
- get expert pi_e
- test if the mdp solver work
- make mdp more efficienct (using outside code)
'''

if __name__ == '__main__':
    # loading the whole data
    # TODO: load only train data
    df, df_cleansed, df_centroids = load_data()
    trajectories = extract_trajectories(df_cleansed, NUM_PURE_STATES)
    transition_matrix, reward_matrix = make_mdp(trajectories, NUM_STATES, NUM_ACTIONS)
    
    # arbitrary feature columns to use
    # they become binary arbitrarily
    # to check how, see phi() definition
    feature_columns = df_centroids.columns
    
    # initialize s_0 sampler
    sample_initial_state = make_initial_state_sampler(df_cleansed)
    get_state = make_state_centroid_finder(df_centroids, feature_columns)
    
    # initialize w
    np.random.seed(1)
    alphas = np.ones(len(feature_columns))
    W = np.random.dirichlet(alphas, size=1)[0]
    
    # get pi_expert
    pi_expert = get_physician_policy(trajectories)
    mu_pi_expert = estimate_feature_expectation(transition_matrix, sample_initial_state, get_state, pi_expert)
    v_pi_expert = estimate_v_pi(W, mu_pi_expert)
    
    # initialize opt
    opt = QuadOpt()
    import time
    start_t = time.time()
    # initialize with a Greedy Policy
    # we can swap for other types of pis later
    # we may have to index s.t. pi_tilda_i
    pi_tilda = GreedyPolicy(NUM_STATES, NUM_ACTIONS)
    while True:
        # mdp solve to get pi_tilda
        pi_tilda = solve_mdp(transition_matrix, compute_reward)

        mu_pi_tilda = estimate_feature_expectation(transition_matrix, sample_initial_state, get_state, pi_tilda)
        v_pi_tilda = estimate_v_pi(W, mu_pi_tilda)

        # diff
        diff = v_pi_tilda - v_pi_expert
        W, converged = opt.optimize(mu_pi_expert, mu_pi_tilda)

        end_t = time.time()
        print("Total time", end_t - start_t)
        # minimize diff
        # solve MDP

    import pdb;pdb.set_trace()
