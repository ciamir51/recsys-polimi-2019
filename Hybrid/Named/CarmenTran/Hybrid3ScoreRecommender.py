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


class Hybrid3ScoreRecommender(BaseRecommender):
    """Hybrid3ScoreRecommender recommender"""

    RECOMMENDER_NAME = "Hybrid3ScoreRecommender"

    def __init__(self, data: DataObject, random_seed: int, alpha=1):
        super(Hybrid3ScoreRecommender, self).__init__(data.urm_train)
        self.random_seed = random_seed
        urm = sps.vstack([data.urm_train, data.icm_all_augmented.T])
        urm = urm.tocsr()
        self.slim = SLIMElasticNetRecommender(urm)
        self.rp3 = RP3betaRecommender(urm)
        self.itemcf = ItemKNNCFRecommender(urm)
        self.alpha = alpha

    def fit(self, alpha_beta_ratio=1, alpha_gamma_ratio=1):
        try:
            self.slim.load_model('stored_recommenders/slim_elastic_net/',
                                 f'with_icm_{self.random_seed}_topK=100_l1_ratio=0.04705_alpha=0.00115_positive_only=True_max_iter=35')
        except:
            self.slim.fit(topK=100, l1_ratio=0.04705, alpha=0.00115, positive_only=True, max_iter=35)
            self.slim.save_model('stored_recommenders/slim_elastic_net/',
                                 f'with_icm_{self.random_seed}_topK=100_l1_ratio=0.04705_alpha=0.00115_positive_only=True_max_iter=35')
        try:
            self.rp3.load_model('stored_recommenders/rp3_beta/',
                                f'with_icm_{self.random_seed}_topK=40_alpha=0.4_beta=0.2')
        except:
            self.rp3.fit(topK=40, alpha=0.4, beta=0.2)
            self.rp3.save_model('stored_recommenders/rp3_beta/',
                                f'with_icm_{self.random_seed}_topK=40_alpha=0.4_beta=0.2')

        try:
            self.itemcf.load_model('stored_recommenders/item_cf/',
                                   f'with_icm_{self.random_seed}_topK=5_shrink=800_similarity=cosine_feature_weighting=TF-IDF')
        except:
            self.itemcf.fit(topK=5, shrink=800, similarity='cosine', feature_weighting='TF-IDF')
            self.itemcf.save_model('stored_recommenders/item_cf/',
                                   f'with_icm_{self.random_seed}_topK=5_shrink=800_similarity=cosine_feature_weighting=TF-IDF')

        # self.alpha = 1
        self.beta = self.alpha * alpha_beta_ratio
        self.gamma = self.alpha * alpha_gamma_ratio

    def _compute_item_score(self, user_id_array, items_to_compute=None):
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
