"""Abstractions for handling operations with reaktor `Basket` object. Mostly `WSShopMgmt` interface."""

from django.contrib import messages
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from apps.reaktor_auth.models import ReaktorProfile
from libs.own.holon.reaktor import ReaktorEntityError, ReaktorApiError

from apps.reaktor_barrel.basket.models import Basket, DocumentItem
from apps.reaktor_barrel.document.models import Document


def get_basket_from_request(request):
    """Returns the basket for the given request.
    If the basket id is not found in the request, creates a new  basket.
    Assumes that the user is either anonymous or logged in.
    Works with new API wrapper.
    """
    token = request.reaktor_user.token
    if request.reaktor_user.is_anonymous():
        # for anonymous user the basket id is stored in the session by a different key
        key = "anonymous_basket_id%s" % request.site.id
    else:
        key = 'basket_id'
    basket_id = request.REQUEST.get(key) or request.session.get(key)
    # if there is no basket id found in request, try to get one from ReaktorProfile
    if not basket_id and request.reaktor_user.is_authenticated():
        profile = ReaktorProfile.for_reaktor_user(request.reaktor_user)
        basket_id = profile.get_basket_id_for_marker(settings.BASKET_MARKER)
    # try to get the basket by its id
    if basket_id:
        try:
            basket = Basket.get_by_id(token, basket_id)
        # this basket is stale
        except ReaktorEntityError:
            if 'profile' not in locals():
                profile = ReaktorProfile.for_reaktor_user(request.reaktor_user)
            profile.remove_basket_id_for_marker(settings.BASKET_MARKER, basket_id)
            basket_id = None

    # create new basket if there is still no basket id
    if not basket_id:
        basket = Basket.create(token, settings.BASKET_MARKER)
        request.session[key] = basket.id
        # add the newly created basket id to the user's reaktor profile
        if request.reaktor_user.is_authenticated():
            if 'profile' not in locals():
                profile = ReaktorProfile.for_reaktor_user(request.reaktor_user)
            profile.append_basket_id_for_marker(settings.BASKET_MARKER, basket.id)
            profile.save()

    return basket


def update_basket_for_request(request, basket):
    """Updates the basket for the given request.
    Returns the tuple (updated basket, new item if any, was basket updated or not).
    Works with new API wrapper.
    """
    item_id = request.POST.get('item_id')
    item_type = request.POST.get('item_type')
    item_action = request.POST.get('item_action')
    token = request.reaktor_user.token
    updated = False
    document = None
    add_to_basket = request.site.siteconf.add_to_basket
    if item_type == 'DOCUMENT':
        if item_action == 'add':
            already_in = False
            # check if the item is not in the basket already
            for doc in basket.documents:
                if doc.id == item_id:
                    already_in = True
                    break
            # add an item to basket if needed
            if not already_in:
                if not add_to_basket:
                    Basket.clear(token, basket.id)
                # Basket error handling
                #TODO (Iurii Kudriavtsev): improve this to handle ajax `Add to Basket` properly
                try:
                    DocumentItem.add_to_basket(token, basket.id, item_id)
                except ReaktorApiError as err:
                    # In case of ajax, adding to messages doesn't make so much sense.
                    # Reraise and let the view handle it.
                    if request.is_ajax():
                        raise err
                    messages.add_message(request, messages.ERROR, err.message)
                else:
                    document = Document.get_by_id(token, item_id)
                    updated = True
        elif item_action == 'remove':
            # Basket error handling
            #TODO (Iurii Kudriavtsev): improve this to handle ajax `Add to Basket` properly
            try:
                DocumentItem.remove_from_basket(token, basket.id, item_id)
            except ReaktorApiError as err:
                messages.add_message(request, messages.ERROR, err.message)
            else:
                updated = True
    elif item_type == 'VOUCHER':
        #TODO (Iurii Kudriavtsev): handle `VOUCHER` item type
        pass
    # get the updated basket
    #FIXME (Iurii Kudriavtsev): should find a way to update the basket object without making a reaktor call
    basket = Basket.get_by_id(token, basket.id)

    return basket, document, updated


def get_checkout_steps(request, basket):
    """Old checkout support.
    Works with new API wrapper.
    """
    CHECKOUT_STEPS = {
        0: ('your cart', _("Your Cart"),),
        1: ('login', _("Login"),),
        2: ('billing address', _("Billing Address"),),
        3: ('payment details', _("Payment Details"),),
        4: ('fetch books', _("Fetch your books"),),
        5: ('your purchase', _("Your Purchase"),),
    }

    if request.reaktor_user.is_authenticated():
        # remove the 'login' step
        CHECKOUT_STEPS.pop(1)

    # basket is empty
    if not len(basket.items):
        CHECKOUT_STEPS.pop(2)
        CHECKOUT_STEPS.pop(3)
        CHECKOUT_STEPS.pop(4)
        CHECKOUT_STEPS.pop(5)
    # basket is not empty, but is free
    elif not basket.total.amount:
        CHECKOUT_STEPS.pop(2)
        CHECKOUT_STEPS.pop(3)
    else:
        CHECKOUT_STEPS.pop(4)

    return [ CHECKOUT_STEPS[step] for step in xrange(6) if step in CHECKOUT_STEPS ]
