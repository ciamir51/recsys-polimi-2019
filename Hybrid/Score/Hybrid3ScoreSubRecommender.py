from Base.BaseRecommender import BaseRecommender
from Base.NonPersonalizedRecommender import TopPop
from DataObject import DataObject
from Data_manager.DataReader import DataReader
from GraphBased.P3alphaRecommender import P3alphaRecommender
from GraphBased.RP3betaRecommender import RP3betaRecommender
from Hybrid.Hybrid1CXAlphaRecommender import Hybrid1CXAlphaRecommender
from Hybrid.Hybrid1XXAlphaRecommender import Hybrid1XXAlphaRecommender
from KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
from KNN.UserKNNCBFRecommender import UserKNNCBFRecommender
from MatrixFactorization.Cython.MatrixFactorization_Cython import MatrixFactorization_AsySVD_Cython
from SLIM_BPR.Cython.SLIM_BPR_Cython import SLIM_BPR_Cython
import numpy as np
import operator
import os
import scipy.sparse as sps

from SLIM_ElasticNet.SLIMElasticNetRecommender import SLIMElasticNetRecommender


class Hybrid3ScoreSubRecommender(BaseRecommender):
    """Hybrid3ScoreSubRecommender recommender"""

    RECOMMENDER_NAME = "Hybrid3ScoreRecommender"

    def __init__(self, data: DataObject):
        super(Hybrid3ScoreSubRecommender, self).__init__(data.urm_train)
        urm = sps.vstack([data.urm_train, data.icm_all_augmented.T])
        urm = urm.tocsr()
        self.slim = SLIMElasticNetRecommender(urm)
        self.rp3 = RP3betaRecommender(self.URM_train)
        self.itemcf = ItemKNNCFRecommender(self.URM_train)
        self.random_seed = data.random_seed



    def fit(self, alpha_beta_ratio=1, alpha_gamma_ratio=1):
        try:
            self.slim.load_model('stored_recommenders/slim_elastic_net/',
                                 f'with_icm_{self.random_seed}_topK=100_l1_ratio=0.04705_alpha=0.00115_positive_only=True_max_iter=35')
        except:
            self.slim.fit(topK=100, l1_ratio=0.04705, alpha=0.00115, positive_only=True, max_iter=35)
            self.slim.save_model('stored_recommenders/slim_elastic_net/',
                                 f'with_icm_{self.random_seed}_topK=100_l1_ratio=0.04705_alpha=0.00115_positive_only=True_max_iter=35')

        self.rp3.fit(topK=20, alpha=0.16, beta=0.24)
        self.itemcf.fit(topK=22, shrink=850, similarity='jaccard', feature_weighting='BM25')

        self.alpha = 1
        self.beta = alpha_beta_ratio
        self.gamma = alpha_gamma_ratio


    def _compute_item_score(self, user_id_array, items_to_compute = None):
        # ATTENTION!
        # THIS METHOD WORKS ONLY IF user_id_array IS A SCALAR AND NOT AN ARRAY
        # TODO

        scores_slim = self.slim._compute_item_score(user_id_array=user_id_array)
        scores_rp3 = self.rp3._compute_item_score(user_id_array=user_id_array)
        scores_itemcf = self.itemcf._compute_item_score(user_id_array=user_id_array)

        # normalization
        slim_max = scores_slim.max()
        rp3_max = scores_rp3.max()
        itemcf_max = scores_itemcf.max()

        if not slim_max == 0:
            scores_slim /= slim_max
        if not rp3_max == 0:
            scores_rp3 /= rp3_max
        if not itemcf_max == 0:
            scores_itemcf /= itemcf_max

        scores_total = self.alpha * scores_slim + self.beta * scores_rp3 + self.gamma * scores_itemcf

        return scores_total

