import os
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.cluster import MiniBatchKMeans 
from sklearn import preprocessing 
from constants import *

def check_numerical_categorical(all_cols, categorical_cols, numerical_cols):
    check1 = (set(numerical_cols) - set(all_cols))
    #print(check1)
    check2 = (set(categorical_cols) - set(all_cols))
    #print(check2)
    check3 = (set(all_cols) - set(categorical_cols) - set(numerical_cols))
    #print(check3)
    return (check1 | check2 | check3) == set(ETC)


def load_data():
    # TODO: accept filepath to get train/test/vali
    if os.path.isfile(CLEANSED_DATA_FILEPATH):
        df = _load_data(FILEPATH)
        df_cleansed = _load_data(CLEANSED_DATA_FILEPATH)
        df_centroids = _load_data(CENTROIDS_DATA_FILEPATH)
    else:
        df = _load_data(FILEPATH)
        df_corrected = correct_data(df)
        df_norm = normalize_data(df_corrected)
        X, mu, y = separate_X_mu_y(df_norm, ALL_VALUES)
        X_centroids, X_clustered = clustering(X, k=num_states, batch_size=500, cols_to_exclude=COLS_NOT_FOR_CLUSTERING)
        X['state'] = pd.Series(X_clustered)
        df_cleansed = pd.concat([X, mu, y], axis=1)
        df_cleansed.to_csv(CLEANSED_DATA_FILEPATH, index=False)
        df_centroids = pd.DataFrame(X_centroids, columns=df_cleansed.columns)
        df_centroids.to_csv(CENTROIDS_DATA_FILEPATH, index=False)

    return df, df_cleansed, df_centroids

def _load_data(path):
    df = pd.read_csv(path)
    cols = df.columns
    valid_cols = list(set(INTEGER_COLS) & set(cols))
    df[valid_cols].astype(np.int)
    return df


def normalize_data(df):
    # divide cols: numerical, categorical, text data
    # logarithimic scale 
    df[COLS_TO_BE_NORMALIZED] -= np.mean(df[COLS_TO_BE_NORMALIZED], axis=0)
    df[COLS_TO_BE_NORMALIZED] /= np.std(df[COLS_TO_BE_NORMALIZED], axis=0)
    return df



def correct_data(df):
    # the logic is hard-coded. could be fixed...
    # TODO: vectorize this
    df['sedation'] = df['sedation'].clip(0.0)

    for i, c in enumerate(COLS_TO_BE_LOGGED):
        # ideally correct missing data or obviously wrong values
        stats = df[c].describe(percentiles=[.01, 0.99])
        min_val = stats['1%']
        max_val = stats['99%']
        df[c] = df[c].clip(min_val, max_val)
    for i, c in enumerate(COLS_TO_BE_LOGGED):
        # k means clustering assumes vars are normally distributed
        # to control the effect of outliers or a certain var
        # we artificially make the vars look more normal
        df[c] = np.log(df[c])
        finite_min = df[c][np.isfinite(df[c])].min()
        df[c] = df[c].clip(finite_min)
        stats = df[c].describe()
        #sns.distplot(df[c], color=palette[i])
        #plt.show()
    return df


def separate_X_mu_y(df, cols=None):
    mu = df[INTERVENTIONS]
    # TODO: fix the error here
    mu['action'], tev_bin_edges, vaso_bin_edges  = discretize_actions(mu['input_4hourly_tev'], mu['median_dose_vaso'])
    y = df[OUTCOMES]
    if cols is None:
        default_cols = set(ALL_VALUES) - set(OUTCOMES)
        X = df[list(default_cols)]
    else:
        observation_cols = set(cols) - set(OUTCOMES) - set(INTERVENTIONS)
        X = df[list(observation_cols)]
    return X, mu, y


def apply_pca(X):
    pca = PCA(n_components=2)
    pca.fit(X)
    X_pca = pca.transform(X)
    # explained variance of the first column is already 99%
    X_pca = pd.DataFrame(X_pca, columns=list('AB'))
    return X_pca

def clustering(X, k=2000, batch_size=100, cols_to_exclude=[]):
    # pick only numerical columns that make sense
    X = X.drop(cols_to_exclude, axis=1)
    mbk = MiniBatchKMeans(n_clusters=k, batch_size=batch_size, init_size=k*3)
    mbk.fit(X)
    X_centroids = mbk.cluster_centers_
    X_clustered = mbk.predict(X)
    return X_centroids, X_clustered

def discretize_actions(
        input_4hourly__sequence__continuous,
        median_dose_vaso__sequence__continuous,
        bins_num = 5):
    # IV fluids discretization
    input_4hourly__sequence__continuous__no_zeros = input_4hourly__sequence__continuous[ \
        input_4hourly__sequence__continuous > 0]
    input_4hourly__sequence__discretized__no_zeros, input_4hourly__bin_bounds = \
        pd.qcut( input_4hourly__sequence__continuous__no_zeros, \
                 bins_num - 1, labels = False, retbins = True)
    input_4hourly__sequence__discretized = \
        (input_4hourly__sequence__continuous > 0).astype(int)
    input_4hourly__sequence__discretized[ input_4hourly__sequence__discretized == 1 ] = \
        input_4hourly__sequence__discretized__no_zeros + 1
        
    # Vaopressors discretization
    median_dose_vaso__sequence__continuous__no_zeros = median_dose_vaso__sequence__continuous[ \
        median_dose_vaso__sequence__continuous > 0]
    median_dose_vaso__sequence__discretized__no_zeros, median_dose_vaso__bin_bounds = \
        pd.qcut( median_dose_vaso__sequence__continuous__no_zeros, \
                 bins_num - 1, labels = False, retbins = True)
    median_dose_vaso__sequence__discretized = \
        (median_dose_vaso__sequence__continuous > 0).astype(int)
    median_dose_vaso__sequence__discretized[ median_dose_vaso__sequence__discretized == 1 ] = \
        median_dose_vaso__sequence__discretized__no_zeros + 1
        
    # Combine both actions discretizations
    actions_sequence = median_dose_vaso__sequence__discretized * bins_num + \
        input_4hourly__sequence__discretized
    
    # Calculate for IV fluids quartiles the median dose given in that quartile
    input_4hourly__conversion_from_binned_to_continuous = np.zeros(bins_num)
    for bin_ind in range(1, bins_num):
        input_4hourly__conversion_from_binned_to_continuous[bin_ind] = \
        np.median(input_4hourly__sequence__continuous__no_zeros[ \
                  input_4hourly__sequence__discretized__no_zeros == bin_ind - 1] )
    
    # Calculate for vasopressors quartiles the median dose given in that quartile
    median_dose_vaso__conversion_from_binned_to_continuous = np.zeros(bins_num)
    for bin_ind in range(1, bins_num):
        median_dose_vaso__conversion_from_binned_to_continuous[bin_ind] = \
        np.median(median_dose_vaso__sequence__continuous__no_zeros[ \
                  median_dose_vaso__sequence__discretized__no_zeros == bin_ind - 1] )
    
    return actions_sequence, \
        input_4hourly__conversion_from_binned_to_continuous, \
        median_dose_vaso__conversion_from_binned_to_continuous


def get_physician_policy(states_sequence, actions_sequence, state_count, action_count):
    # S x A count table
    sa_count_table = np.zeros((state_count, action_count))
    physician_policy = np.zeros((state_count))
    for state in range(state_count):
        ind = np.where(states_sequence == state)[0]
        for action in range(action_count):
            sa_count_table[state, action] += sum(actions_sequence[ind] == action)
        physician_policy[state] = np.argmax(sa_count_table[state,:])
    # when tie, smallest index returned
    return physician_policy


def is_terminal_state(s):
    return s >= (NUM_STATES - NUM_TERMINAL_STATES)
