from apps.barrel import Store, Field, DateField, IntField
from apps.barrel.rpc import RpcMixin


class List(Store, RpcMixin):
    interface = 'WSListMgmt'

    tracked_fields = ["document_ids"]

    id = Field(target='ID')
    count = IntField(target='count')
    creation_date = DateField(target='creationTime', default='')
    description = Field(target='description')
    document_ids = Field(target='documentIDs', default=[])
    # global_id = Field(target='globalID')
    name = Field(target='name')
    offset = IntField(target='offset')
    owner = Field(target='owner')
    total_count = IntField(target='size')

    @classmethod
    def delete_by_id(cls, token, list_id, delete_documents=False):
        return cls.signature(method='deleteList', args=[token, list_id, delete_documents])

    @classmethod
    def _get_by_id(cls, token, list_id, offset, number_of_results):
        return cls.signature(method='getList', args=[token, list_id, offset, number_of_results])

    @classmethod
    def _get_constrained_by_id(cls, token, list_id, search_string, offset, number_of_results):
        if not ':' in search_string:
            search_string = '*%s*' % search_string
        return cls.signature(method='getListConstrained', args=[token, list_id, search_string, offset, number_of_results])

    @classmethod
    def _change_sorting(cls, token, list_id, sort, direction):
        # That would be nice, but unfortunately, it's not the case.
        # sort = cls.fields[sort].target
        invert = direction == 'desc'
        return cls.signature(method='changeListSorting', args=[token, list_id, sort, invert])

    @classmethod
    def get_by_ids(cls, token, list_ids):
        return cls.signature(method='getLists', args=[token, list_ids])

    @classmethod
    def filter(cls, token, list_id, search_string=None, offset=0, number_of_results=-1, sort='creationDate', direction='desc'):
        cls._change_sorting(token, list_id, sort, direction)
        if search_string:
            return cls._get_constrained_by_id(token, list_id, search_string, offset, number_of_results)
        else:
            return cls._get_by_id(token, list_id, offset, number_of_results)

    @classmethod
    def get_by_doc_ids(cls, token, document_ids):
        return cls.signature(method='getListsWithDocumentList', args=[token, document_ids], data_converter=lambda d: d)

    @classmethod
    def _get_by_type(cls, token, type, offset, number_of_results):
        return cls.signature(method='getSpecialList', args=[token, type, offset, number_of_results])

    @classmethod
    def get_inbox(cls, token, offset=0, number_of_results=-1):
        return cls._get_by_type(token, 'INBOX', offset, number_of_results)

    @classmethod
    def get_trash(cls, token, offset=0, number_of_results=-1):
        return cls._get_by_type(token, 'TRASH', offset, number_of_results)

    @classmethod
    def get_user_list_ids(cls, token):
        return cls.signature(method='getListList', args=[token], data_converter=lambda d: d)

    @classmethod
    def create(cls, token, name, description=''):
        def converter(data):
            return cls({'ID': data, 'name': name, 'description':description})
        return cls.signature(method='createList', args=[token, name, description], data_converter=converter)

    @classmethod
    def add_documents(cls, token, list_id, document_ids, index=0):
        return cls.signature(method='addDocumentsToList', args=[token, list_id, document_ids, index])

    @classmethod
    def remove_documents(cls, token, list_id, document_ids):
        return cls.signature(method='removeDocumentsFromList', args=[token, list_id, document_ids])

    @classmethod
    def empty(cls, token, list_id):
        # `keepDocumentsInOtherLists` is always True, since reaktor does not support False (cfr. api doc).
        # Note that since moving a document to trash removes other labels, the expected result
        # is still reached.
        return cls.signature(interface='WSDocMgmt', method='removeDocumentsInList', args=[token, list_id, True])

    @property
    def is_inbox(self):
        return self.name.startswith('INBOX-')

    @property
    def is_trash(self):
        return self.name.startswith('TRASH-')

    def __len__(self):
        return self.count

    def __nonzero__(self):
        return self.total_count
