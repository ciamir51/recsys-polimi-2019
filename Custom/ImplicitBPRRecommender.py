from Base.BaseRecommender import BaseRecommender
from Custom.ImplicitBaseRecommender import ImplicitBaseRecommender
from DataObject import DataObject
from Hybrid.Hybrid1CXXAlphaRecommender import Hybrid1CXXAlphaRecommender
import numpy as np
import implicit


class ImplicitBPRRecommender(ImplicitBaseRecommender):
    """ImplicitBPRRecommender recommender"""

    RECOMMENDER_NAME = "ImplicitBPRRecommender"

    def __init__(self, data : DataObject,factors=100, regularization=0.01, learning_rate=1e-3,
                                                        use_gpu=False, iterations=15, num_threads=0):

        super(ImplicitBPRRecommender, self).__init__(data.urm_train)
        self.data = data
        self.rec = implicit.bpr.BayesianPersonalizedRanking(factors=factors, regularization=regularization,
                                                            learning_rate=learning_rate,
                                                            use_gpu=use_gpu,
                                                            iterations=iterations,
                                                            num_threads=num_threads)

