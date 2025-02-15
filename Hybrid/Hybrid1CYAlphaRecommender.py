import copy

from joblib import Parallel, delayed

from Base.BaseRecommender import BaseRecommender
from DataObject import DataObject
from Data_manager.DataReader import DataReader
from GraphBased.P3alphaRecommender import P3alphaRecommender
from KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
from KNN.UserKNNCBFRecommender import UserKNNCBFRecommender
from SLIM_BPR.Cython.SLIM_BPR_Cython import SLIM_BPR_Cython
import numpy as np
import operator

def get_cached_recommendation(rec, recommended_users, max_cutoff):
    cached_recommendation = {}
    for user_id in recommended_users:
        recommended_items = rec.recommend(user_id, cutoff=max_cutoff)
        cached_recommendation[user_id] = recommended_items
    return cached_recommendation

class Hybrid1CYAlphaRecommender(BaseRecommender):
    """Hybrid1CYAlphaRecommender recommender"""

    RECOMMENDER_NAME = "Hybrid1CYAlphaRecommender"

    def __init__(self, data: DataObject, recommenders, recommended_users, max_cutoff=50):
        super(Hybrid1CYAlphaRecommender, self).__init__(data.urm_train)
        self.data = data
        self.weights = np.zeros(shape=(len(recommenders), max_cutoff))
        self.max_cutoff = max_cutoff
        self.cached_recommendation_all = []
        # for rec in recommenders:
        #     cached_recommendation = {}
        #     for user_id in recommended_users:
        #         recommended_items = rec.recommend(user_id, cutoff=max_cutoff)
        #         cached_recommendation[user_id] = recommended_items
        #     self.cached_recommendation_all.append(cached_recommendation)
        self.cached_recommendation_all = Parallel(n_jobs=2)(
            delayed(get_cached_recommendation)
            (copy.deepcopy(rec), copy.deepcopy(recommended_users), max_cutoff)
            for rec in recommenders)
        sum_all_weights = 0
        for i in range(len(recommenders)):
            for user_id in recommended_users:
                recommended_items = self.cached_recommendation_all[i][user_id]
                relevant_items = self.data.urm_test[user_id].indices
                is_relevant = np.in1d(recommended_items, relevant_items, assume_unique=True) * 1
                is_relevant = np.pad(is_relevant, (0, max_cutoff - is_relevant.shape[0]), 'constant', constant_values=False)
                self.weights[i] = self.weights[i] + is_relevant
                sum_all_weights += np.cumsum(is_relevant)
        # self.weights = self.weights / sum_all_weights
    def fit(self):
        pass

    def recommend(self, user_id_array, cutoff=None, remove_seen_flag=True, items_to_compute=None,
                  remove_top_pop_flag=False, remove_CustomItems_flag=False, return_scores=False):
        recommended_items = []
        weighted_item = {}
        limit = int(self.max_cutoff)
        for cached_recommendation in self.cached_recommendation_all:
            recommended_items.append(cached_recommendation[user_id_array])
        for i in range(0, len(recommended_items)):
            for j in range(0, len(recommended_items[i])):
                if j < limit:
                    weighted_item[recommended_items[i][j]] =\
                        weighted_item.get(recommended_items[i][j], 0) - self.weights[i][j]
        result = np.array(sorted(weighted_item.items(), key=operator.itemgetter(1), reverse=False))
        max_size = min(result.shape[0], cutoff)
        if max_size > 0:
            return [int(x) for x in result[:max_size, [0]].squeeze(axis=1).tolist()]
        else:
            return np.array([])

    def clone(self):
        clone_of_this = copy.copy(self)
        # clone_of_this.cached_recommendation_all = copy.deepcopy(self.cached_recommendation_all)
        return clone_of_this
