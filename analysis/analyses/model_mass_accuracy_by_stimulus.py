#!/usr/bin/env python

"""
Computes average model probability of saying r=10 for "which is heavier?".
Produces a csv file with the following columns:

    likelihood (string)
        the likelihood name (e.g., ipe, ipe_cf, empirical, empirical_cf)
    counterfactual (bool)
        whether the counterfactual likelihood was used
    model (string)
        the model version (e.g., static, learning)
    fitted (bool)
        whether the model was fit to human responses
    version (string)
        experiment version
    kappa0 (float)
        true log mass ratio
    stimulus (string)
        stimulus name
    lower (float)
        lower bound of the 95% confidence interval
    median (float)
        median of the bootstrap distribution
    upper (float)
        upper bound of the 95% confidence interval
    N (int)
        how many samples the mean was computed over

"""

__depends__ = ["single_model_belief.csv"]
__random__ = True
__parallel__ = True

import os
import util
import pandas as pd
import numpy as np

from IPython.parallel import Client, require


def run(dest, results_path, seed, parallel):
    np.random.seed(seed)

    @require('numpy as np', 'pandas as pd', 'util')
    def bootstrap_mean(df, **kwargs):
        name, df = df
        df.name = name
        return util.bootstrap_mean(df, **kwargs)

    def as_df(x, index_names):
        df = pd.DataFrame(x)
        if len(index_names) == 1:
            df.index.name = index_names[0]
        else:
            df.index = pd.MultiIndex.from_tuples(df.index)
            df.index.names = index_names
        return df

    if parallel:
        rc = Client()
        dview = rc[:]
        mapfunc = dview.map_sync
    else:
        mapfunc = map

    model_belief = pd.read_csv(os.path.join(results_path, 'single_model_belief.csv'))
    cols = ['likelihood', 'counterfactual', 'model', 'fitted', 'version', 'kappa0', 'stimulus']

    results = mapfunc(bootstrap_mean, list(model_belief.groupby(cols)['p correct']))
    results = as_df(results, cols)
    results.to_csv(dest)


if __name__ == "__main__":
    parser = util.default_argparser(locals())
    args = parser.parse_args()
    run(args.to, args.results_path, args.seed, args.parallel)