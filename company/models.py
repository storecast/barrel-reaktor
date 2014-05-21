from apps.barrel import Store, Field, BooleanField, EmbeddedStoreField, IntField, SplitField
from apps.barrel.rpc import RpcMixin
from apps.barrel.cache import cache


class PasswordPolicy(Store):
    min_length = IntField(target='minimumLength', default=5)
    number_char_classes = IntField(target='requiredNumberOfCharacterClasses', default=0)
    supported_char_classes = SplitField(target='supportedCharacterClasses', default=[])
    rules = SplitField(target='rules', default=[])


class Nature(Store, RpcMixin):
    interface = 'WSReaktorMgmt'

    name = Field(target='name')
    account_deletion_confirmation = BooleanField(target='enableAccountDeletionConfirmation')
    auth_hash_method = Field(target='authenticationHashAlgorithm')
    email_change_confirmation = BooleanField(target='enableEmailChangeConfirmation')
    facebook_key = Field(target='facebookConfiguration:applicationKey')
    facebook_permissions = Field(target='facebookConfiguration:profilePermissions')
    home_country = Field(target='homeCountry')
    lockout_attempts = IntField(target='loginAttemptsBeforeLockout')
    lockout_duration = IntField(target='lockoutPeriodMinutes')
    shop_currency = Field(target='shopCurrency')
    shop_url = Field(target='shopUrl')
    password_policy = EmbeddedStoreField(target='passwordPolicy', store_class=PasswordPolicy)

    @classmethod
    def get_by_name(cls, name):
        return cls.signature(method='getNature', args=[name])


class Company(Store, RpcMixin):
    interface = 'WSReaktorMgmt'

    name = Field(target='name')
    natures = EmbeddedStoreField(target='natures', store_class=Nature, is_array=True)

    @classmethod
    @cache(duration=3600*8)
    def get_by_name(cls, name):
        return cls.signature(method='getCompany', args=[name])
