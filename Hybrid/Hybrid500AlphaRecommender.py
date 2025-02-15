from joblib import Parallel, delayed

from Base.BaseRecommender import BaseRecommender
from Base.NonPersonalizedRecommender import TopPop
from DataObject import DataObject
from Data_manager.DataReader import DataReader
from Data_manager.Splitter import Splitter
from GraphBased.P3alphaRecommender import P3alphaRecommender
from GraphBased.RP3betaRecommender import RP3betaRecommender
from Hybrid.Hybrid003AlphaRecommender import Hybrid003AlphaRecommender
from Hybrid.Hybrid1CXAlphaRecommender import Hybrid1CXAlphaRecommender
from Hybrid.Hybrid1CYAlphaRecommender import Hybrid1CYAlphaRecommender
from Hybrid.Hybrid1XXAlphaRecommender import Hybrid1XXAlphaRecommender
from KNN.ItemKNNCBFOnlyColdRecommender import ItemKNNCBFOnlyColdRecommender
from KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
from KNN.UserKNNCBFRecommender import UserKNNCBFRecommender
from SLIM_BPR.Cython.SLIM_BPR_Cython import SLIM_BPR_Cython
import numpy as np
import operator


def fib(n):
    if n == 0:
        return [0]
    elif n == 1:
        return [0, 1]
    else:
        lst = fib(n - 1)
        lst.append(lst[-1] + lst[-2])
        return lst


class par:
    def __init__(self, data: DataObject, leave_k_out=0, threshold=0, probability=0.2):
        self.data = data
        self.leave_k_out = leave_k_out
        self.threshold = threshold
        self.probability = probability

    def split_and_fit(self, random_seed):
        data = self.data
        new_urm_train = Splitter(data.urm_train)._split_train_test(random_seed=random_seed, threshold=self.threshold,
                                                                   probability=self.probability,
                                                                   k=self.leave_k_out)[0]
        rec = RP3betaRecommender(new_urm_train)
        rec.fit(topK=20, alpha=0.16, beta=0.24)
        rec.URM_train = data.urm_train

        return rec


class Hybrid500AlphaRecommender(BaseRecommender):
    """Hybrid500AlphaRecommender recommender"""

    RECOMMENDER_NAME = "Hybrid500AlphaRecommender"

    def __init__(self, data: DataObject, k: int, leave_k_out=0, threshold=0, probability=0.2):
        super(Hybrid500AlphaRecommender, self).__init__(data.urm_train)
        self.data = data
        self.max_cutoff = 30
        recs = Parallel(n_jobs=16)(
            delayed(par(data,
                        leave_k_out=leave_k_out,
                        threshold=threshold,
                        probability=probability).split_and_fit)
            (i)
            for i in range(k))
        self.hybrid_rec = Hybrid1CXAlphaRecommender(data, recommenders=recs,
                                                    recommended_users=data.ids_user, max_cutoff=self.max_cutoff)

    def recommend(self, user_id_array, cutoff=None, remove_seen_flag=True, items_to_compute=None,
                  remove_top_pop_flag=False, remove_CustomItems_flag=False, return_scores=False):
        return self.hybrid_rec.recommend(user_id_array, cutoff=cutoff)
