from barrel import Store
from barrel.rpc import RpcMixin
from barrel.cache import cache, sliced_call_args
from barrel_reaktor.document.models import Document


class ContentPresentation(Store, RpcMixin):
    interface = 'WSFeaturedContentMgmt'

    @classmethod
    @cache(keygen=sliced_call_args(i=1), need_cache=lambda docs: False)  # ready to be enabled
    def get_documents(cls, token, presentation_id, affiliate=None, offset=0, number_of_results=-1, sort=None, direction='asc'):
        invert = direction == 'desc'
        return cls.signature(method='getContentPresentationDocuments',
                             args=[token, affiliate, presentation_id, offset, number_of_results, sort, invert],
                             data_converter=Document)
