AVAILABLE_SOURCES = {
    'commercial': ('com.bookpac.archive.search.sources.local.commercial', ),
    'community': ('com.bookpac.archive.search.sources.local.community', ),
    'free_external': ('com.bookpac.archive.search.sources.external.free', ),
    'free_local': ('com.bookpac.archive.search.sources.local.free', ),
    'own': ('com.bookpac.archive.search.sources.local.own', ),
    'shop': ('com.bookpac.archive.search.sources.local.shop', ),
    # compound sources
    'free': ('com.bookpac.archive.search.sources.local.free',
             'com.bookpac.archive.search.sources.external.free', ),
    'local': ('com.bookpac.archive.search.sources.local.shop',
              'com.bookpac.archive.search.sources.local.community',
              'com.bookpac.archive.search.sources.local.own', ),
}


def get_search_sources(source=None):
    if source is None:
        return AVAILABLE_SOURCES
    return AVAILABLE_SOURCES[source]
