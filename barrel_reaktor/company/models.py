from barrel import Store, Field, BooleanField, EmbeddedStoreField, IntField, SplitField
from barrel.rpc import RpcMixin


class PasswordPolicy(Store):
    min_length = IntField(target='minimumLength', default=5)
    number_char_classes = IntField(target='requiredNumberOfCharacterClasses', default=0)
    supported_char_classes = SplitField(target='supportedCharacterClasses', default=[])
    rules = SplitField(target='rules', default=[])


class Nature(Store, RpcMixin):
    interface = 'WSReaktorMgmt'

    class AddressFormat(Store):
        fmt = Field(target='fmt')
        require = Field(target='require')
        zip = Field(target='zip')

    name = Field(target='name')
    account_deletion_confirmation = BooleanField(target='enableAccountDeletionConfirmation')
    address_format = EmbeddedStoreField(target='addressFormat',
                                        store_class=AddressFormat)
    auth_hash_method = Field(target='authenticationHashAlgorithm')
    available_in_multistore_app = BooleanField(target='availableInMultistoreApp')
    email_change_confirmation = BooleanField(target='enableEmailChangeConfirmation')
    facebook_key = Field(target='facebookConfiguration:applicationKey')
    facebook_permissions = Field(target='facebookConfiguration:profilePermissions')
    home_country = Field(target='homeCountry')
    lockout_attempts = IntField(target='loginAttemptsBeforeLockout')
    lockout_duration = IntField(target='lockoutPeriodMinutes')
    mobi_conversion = Field(target='mobiConversionEnabled')
    password_policy = EmbeddedStoreField(target='passwordPolicy',
                                         store_class=PasswordPolicy)
    shop_currency = Field(target='shopCurrency')
    shop_url = Field(target='shopUrl')
    vendor_id_enabled = Field(target='vendorIdEnabled')

    @classmethod
    def get_by_name(cls, name):
        return cls.signature(method='getNature', args=[name])


class Company(Store, RpcMixin):
    interface = 'WSReaktorMgmt'

    name = Field(target='name')
    natures = EmbeddedStoreField(target='natures', store_class=Nature,
                                 is_array=True)

    @classmethod
    def get_by_name(cls, name):
        return cls.signature(method='getCompany', args=[name])
