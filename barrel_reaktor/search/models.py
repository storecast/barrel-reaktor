from barrel import Store, Field, FloatField, EmbeddedStoreField
from barrel.rpc import RpcMixin
from barrel_reaktor.document.models import Document
from . import get_search_sources


class Stat(Store):
    """The reaktor always passes in `name` as the value to use for the search
    facet. Since it's a value, let's rename it. Some fields also provide a
    label, which we keep untouched.
    """
    count = Field(target="count")
    value = Field(target="name")
    label = Field(target="label")


class CategoryStat(Store):
    """Category searching facet is inconsistent with other facets.
    This model is there as an attempt to normalize that.
    """
    count = Field(target="count")
    value = Field(target="id")
    label = Field(target="name")


class DocumentResult(Store):
    """Search result object wrapping search itemsalongside search info
    like pagination information.
    """
    class DocumentItem(Store):
        """Search result item wrapping a document alongside search info like
        item relevance.
        """
        document = EmbeddedStoreField(target="searchResult", store_class=Document)
        relevance = FloatField(target="relevance")

    class Stats(Store):
        """Represents stats about a search result, e.g. how many books for
        this language, how many books available as pdf, ...
        """
        category = EmbeddedStoreField(target="category", store_class=CategoryStat, is_array=True)
        collection_title = EmbeddedStoreField(target="collectionTitle", store_class=Stat, is_array=True)
        drm = EmbeddedStoreField(target="drmType", store_class=Stat, is_array=True)
        format = EmbeddedStoreField(target="format", store_class=Stat, is_array=True)
        language = EmbeddedStoreField(target="language", store_class=Stat, is_array=True)
        price = EmbeddedStoreField(target="price", store_class=Stat, is_array=True)
        pub_date = EmbeddedStoreField(target="publication_date", store_class=Stat, is_array=True)
        rating = EmbeddedStoreField(target="rating", store_class=Stat, is_array=True)
        source = EmbeddedStoreField(target="source", store_class=Stat, is_array=True)
        tag = EmbeddedStoreField(target="tag", store_class=Stat, is_array=True)

    # Without blocking search, other fields don't make sense anymore so there
    # they are just ignored.
    count = Field(target="numberOfResults")
    has_less = Field(target="hasLess")
    has_more = Field(target="hasMore")
    items = EmbeddedStoreField(target='results', store_class=DocumentItem, is_array=True)
    offset = Field(target="offset")
    stats = EmbeddedStoreField(target='relatedObjects', store_class=Stats)
    total_count = Field(target="totalNumberOfResults")


class Search(RpcMixin):
    """Interface to various API search endpoints. Beware that this one is not
    a `Store`, which means that when calling its class methods,
    expect different types.
    """
    interface = 'WSSearchDocument'

    @classmethod
    def documents(cls, token, search_string, offset, number_of_results, sort=None, direction=None, include_search_fields=None, source=None, related=None, options=None):
        """Returns documents for a given string."""
        invert = direction == 'desc'
        if not options:
            options = {'resultType': 'Object'}
        if source:
            sources = get_search_sources(source)
        return cls.signature(method='searchDocuments', data_converter=DocumentResult,
            args=[token, search_string, sources, offset, number_of_results, sort, invert, related, include_search_fields, options])

    @classmethod
    def suggestions(cls, token, search_string, number_of_results, sources=None, highlight=None):
        """Returns document suggestions for a given string."""
        args = [token, search_string, sources, number_of_results]
        method = 'getSuggestionObjects'
        if highlight:
            method = 'getSuggestionObjectsWithHighlights'
            args.append(highlight)
        return cls.signature(method=method, data_converter=Document, args=args)
