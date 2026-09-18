from dataclasses import replace
import hashlib
from .generator import HardDEpisode

def rename_twin(ep:HardDEpisode)->HardDEpisode:
    eid=hashlib.sha256((ep.episode_id+':rename').encode()).hexdigest()[:32]
    return replace(ep,episode_id=eid,candidates=tuple(replace(c,name='renamed_'+c.name) for c in ep.candidates))
