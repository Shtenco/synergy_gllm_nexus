class MemoryAdmission:
    def __init__(self,cache_threshold=.65,promote_threshold=.9):
        self.cache_threshold=cache_threshold; self.promote_threshold=promote_threshold
    def classify(self,trust_score:float,independent_corroboration:bool)->str:
        if trust_score>=self.promote_threshold and independent_corroboration:return 'promoted'
        if trust_score>=self.cache_threshold:return 'cache'
        return 'session'