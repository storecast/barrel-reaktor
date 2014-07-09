from barrel import Store
from barrel.rpc import RpcMixin


class Vote(Store, RpcMixin):
    interface = 'WSDiscussionMgmt'

    @classmethod
    def for_doc_id(cls, token, doc_id, stars):
        return cls.signature(method='postVoteForDocument', args=[token, doc_id, {'stars': stars}])
