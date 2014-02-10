from django.utils.translation import ungettext
from django.http import HttpResponse
import simplejson as json

from apps.reaktor_shop.wishlist_models import WishList
from apps.reaktor_shop.wishlistentry_models import WishListEntry


def wishlist_status(request):
    wishlist_status = dict()
    if not request.user.is_anonymous():
        wishlist_status["status"] = "NOT_ON_WISHLIST"
        wishlist_status["csrfmiddlewaretoken"] = request.META.get("CSRF_COOKIE", "")

        document_id = request.GET.get("documentid", None)
        if document_id :
            token = request.reaktor_user.token
            wishlist = WishList.objects.get(token=token)
            for entry in wishlist.entries:
                if entry.document.document_id == document_id:
                    wishlist_status["status"] = "ON_WISHLIST"

    return HttpResponse(json.dumps(wishlist_status), content_type="application/json")


def wishlist_add(request):
    wishlist_update = dict()
    wishlist_update["status"] = "NOT_UPDATED"

    document_id = request.POST.get("documentid")
    if document_id:
        wishlistentry = WishListEntry.objects.create(document_id = document_id)
        if wishlistentry:
            wishlist_update["status"] = "UPDATED"

    wishlist = WishList.objects.get(token=request.reaktor_user.token)
    wishlist_update["count_short"] = len(wishlist.entries)

    return HttpResponse(json.dumps(wishlist_update), content_type="application/json")


def wishlist_remove(request):
    wishlist_update = dict()
    wishlist_update["status"] = "NOT_UPDATED"

    document_id = request.POST.get("documentid")
    if document_id:
        WishListEntry.objects.remove(document_id = document_id)
        wishlist_update["status"] = "UPDATED"
        # get the wishlist so we can update the UI properly
        token = request.reaktor_user.token
        wishlist = WishList.objects.get(token=token)
        wishlist_length = len(wishlist.entries)
        wishlist_update["count_short"] = wishlist_length
        wishlist_update["count_long"] = ungettext(
            '%(count)d book',
            '%(count)d books',
        wishlist_length) % {
            'count': wishlist_length,
        }
        #ungettext('%(num)d book', '%(num)d books', num) % {'num': wishlist_length,}

    return HttpResponse(json.dumps(wishlist_update), content_type="application/json")
