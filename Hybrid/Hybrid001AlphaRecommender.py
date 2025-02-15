from Base.BaseRecommender import BaseRecommender
from KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
from KNN.UserKNNCBFRecommender import UserKNNCBFRecommender
from SLIM_BPR.Cython.SLIM_BPR_Cython import SLIM_BPR_Cython


class Hybrid001AlphaRecommender(BaseRecommender):
    """Hybrid001AlphaRecommender recommender"""

    RECOMMENDER_NAME = "Hybrid001AlphaRecommender"

    def __init__(self, URM_train, UCM, cold_users, warm_users):
        super(Hybrid001AlphaRecommender, self).__init__(URM_train)
        self.warm_recommender = ItemKNNCFRecommender(URM_train)
        self.cold_recommender = UserKNNCBFRecommender(UCM, URM_train)
        self.cold_users = cold_users
        self.warm_users = warm_users


    def fit(self):
        self.warm_recommender.fit(topK=12, shrink=16)
        self.cold_recommender.fit(topK=11000, shrink=2)


    def recommend(self, user_id_array, cutoff = None, remove_seen_flag=True, items_to_compute = None,
                  remove_top_pop_flag = False, remove_CustomItems_flag = False, return_scores = False):
        if user_id_array in self.warm_users:
            return self.warm_recommender.recommend(user_id_array, cutoff=cutoff)
        if user_id_array in self.cold_users:
            return self.cold_recommender.recommend(user_id_array, cutoff=cutoff)