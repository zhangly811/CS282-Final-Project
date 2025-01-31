from sklearn.metrics import mutual_info_score as mis
from scipy.stats import entropy
import numpy as np
import math
import pdb
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style='dark', palette='Set1')
from numpy import mean
import pandas as pd
from constants import IMG_PATH

FONT_SIZE = 20
#font = {'weight' : 'bold',
#        'size'   : FONT_SIZE}
#matplotlib.rc('font', **font)
sns.set(font_scale=2)

#p,q are distributions - p is base distribution and q is approximate
def KL_divergence(p,q):
    return entropy(p,q)

def cross_entropy(p,q):
    return entropy(p,q) + entropy(p) #KL-divergence + entropy

def single_entropy(p):
    return entropy(p)

#Mutual information score
def mis_score(p,q):
    return mis(p,q)

def gen_random_probability(num_actions = 25, epsilon = 0.001, random_action_range = list(range(25))):
    def assign(x,random_action_range):
        if x in random_action_range:
            return 1/len(random_action_range)
        else:
            return epsilon
    out = [assign(x,random_action_range) for x in range(num_actions)]
    out = np.array(out)/np.round(sum(out),3)

    assert(abs(sum(out)- 1) < 0.01 and len(out) == num_actions)
    return np.array(out)

def gen_single_action_probability(num_actions = 25, action_id = 0,epsilon = 0.001):
    out = np.ones(num_actions) * epsilon
    out[action_id] = 1 - (num_actions-1) * epsilon
    assert(sum(out) == 1 and len(out) == num_actions)
    return out

def log_likelihood(prob_actions, target_actions,avg = False ):
    out = 0
    #SANITY checks.
    assert(len(prob_actions) == len(target_actions))
    #assert(len(prob_actions[0]) == 25)

    for i in range(len(target_actions)):
        target_act = target_actions[i]
        candidate_act_prob = prob_actions[i]
        #pdb.set_trace()
        out += math.log(candidate_act_prob[int(target_act)])
    if avg :
        return out / len(target_actions)

    return out

def log_likelihood_no_act(target_acts_stoch, no_int_id,avg = False):
    if avg:
        return(np.mean([math.log(i[no_int_id] + 1e-3) for i in target_acts_stoch ]))

    return(sum([math.log(i[no_int_id] + 1e-3) for i in target_acts_stoch ]))

def test_code():
    a = [0.1,0.2,0.3,0.4]
    b = [0.1,0.2,0.3,0.4]
    c = [0.11, 0.21, 0.29, 0.39]
    d = [0.4,0.3,0.2,0.1]
    e = [0.25,0.25,0.25,0.25]

    print("KL(",a,",",b,") : ",KL_divergence(a,b))
    print("KL(",a,",",c,") : ",KL_divergence(a,c))
    print("KL(",a,",",d,") : ",KL_divergence(a,d))
    print("KL(",a,",",e,") : ",KL_divergence(a,e))

    print("CE(",a,",",b,") : ",cross_entropy(a,b))
    print("CE(",a,",",c,") : ",cross_entropy(a,c))
    print("CE(",a,",",d,") : ",cross_entropy(a,d))
    print("CE(",a,",",e,") : ",cross_entropy(a,e))

    assert(np.array_equal(gen_random_probability(), np.array([0.04 for i in range(25)])))
    assert(np.allclose(gen_random_probability(random_action_range= range(5)),
                          np.concatenate([np.array([0.2 for i in range(5)]),np.zeros(20)*0.001]),
                       atol = 0.01  ))

def sumzip(*items):
    return [sum(values) for values in zip(*items)]

def plot_KL(KL, save_path, plot_suffix, trial_num, iter_num, pi_name = 'IRL', show = True, test = True):
    KL_IRL = []
    KL_random = []
    KL_vaso_random = []
    KL_iv_random = []
    KL_no_int = []
    keys = list(KL.keys())
    for state in keys:
        KL_IRL.append(KL[state]["IRL"])
        KL_random.append(KL[state]["random"])
        KL_no_int.append(KL[state]["no_int_policy"])
        KL_vaso_random.append(KL[state]["vaso_only_random"])
        KL_iv_random.append(KL[state]["iv_only_random"])

    fig = plt.figure(figsize=(10, 10))
    data = np.transpose(np.matrix([KL_IRL, KL_random, KL_no_int, KL_vaso_random, KL_iv_random]))
    data_KL = pd.DataFrame(data)
    data_KL.columns = [pi_name, "Random", "No_Intervention", "Vaso Only Random", "IV Only Random"]

    columns = [None]*5
    d = np.argsort(data_KL.mean().tolist())
    columns[d[0]] = pi_name
    columns[d[1]] = 'No_intervention'
    columns[d[2]] = 'Vaso_only_random'
    columns[d[3]] = 'Random'
    columns[d[4]] = 'IV_only_random'
    data_KL.columns = columns
    sns.barplot(data=data_KL, estimator=mean)

    #plt.bar(keys,KL_IRL,color = 'b',label="IRL")
    #plt.bar(keys,KL_random,bottom = sumzip(KL_IRL), color = 'r', label = "Random")
    #plt.bar(keys,KL_no_int,bottom = sumzip(KL_IRL,KL_random), color = 'y', label = "No intervnetion")
    #plt.bar(keys,KL_vaso_random, bottom = sumzip(KL_IRL,KL_random,KL_no_int), color = 'g', label = "Vaso Only Random")
    #plt.bar(keys,KL_iv_random, bottom = sumzip(KL_IRL,KL_random,KL_no_int,KL_vaso_random), color = 'm', label = "IV Only Random" )
    #test_str = "train"
    #if test:
    #    test_str = "test"
    #plt.title("KL divergences with respect to physician policy in " + test_str + " data" )
    #plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.legend(loc='best', fontsize=FONT_SIZE)
    plt.xlabel('States', fontsize=FONT_SIZE)
    plt.ylabel('KL Divergerence', fontsize=FONT_SIZE)
    fig.savefig('{}{}_kl_t{}xi{}'.format(save_path, plot_suffix, trial_num, iter_num), ppi=300, bbox_inches='tight')
    if show:
        plt.show()
    else:
        return plt
    plt.close()


def plot_avg_LL(LL, save_path, plot_suffix, trial_num, iter_num, pi_name='IRL', show = True, test = True):
    keys = list(LL.keys())
    key_len = len(keys)

    NLL_IRL = []
    NLL_random = []
    NLL_no_int = []

    for p in range(key_len):
        NLL_IRL.append(-1 * LL[keys[p]]["IRL"])
        NLL_random.append(-1 * LL[keys[p]]["random"])
        NLL_no_int.append(-1 * LL[keys[p]]["no_int"])

    fig = plt.figure(figsize=(10, 10))
    data_NLL = pd.DataFrame(np.transpose(np.matrix([NLL_IRL,NLL_random,NLL_no_int])))
    columns = [None]*3
    d = np.argsort(data_NLL.mean().tolist())
    columns[d[0]] = pi_name
    columns[d[1]] = 'No_intervention'
    columns[d[2]] = 'Random'
    data_NLL.columns = columns
    # @refactor @hack
    sns.barplot(data=data_NLL, estimator=mean)
    plt.xlabel('Policies', fontsize=FONT_SIZE)
    plt.ylabel('Negative Log Likelihood', fontsize=FONT_SIZE)
    #plot.title("Plot showing average negative LL")
    if show:
        plt.show()
    fig.savefig('{}{}_ll_t{}xi{}'.format(save_path, plot_suffix, trial_num, iter_num), ppi=300, bbox_inches='tight')
    plt.close()


