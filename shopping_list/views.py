from apps.jinja_lib.views import JinjaTemplateMixin
from apps.reaktor_auth.views import ContextTokenMixin
from apps.reaktor_barrel.shopping_list.models import Preorderlist, PreorderlistItem
from apps.reaktor_shop.wishlist_models import WishList
from apps.reaktor_shop.wishlistentry_models import WishListEntry
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext, ungettext
from django.views.generic import TemplateView
import simplejson as json


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


class WishlistItemView(JinjaTemplateMixin, ContextTokenMixin, TemplateView):
    template_name = 'atoms/documents/wishlist_button.html'
    context_object_name = 'wishlist'

    def get(self, request, doc_id=None, action=None, *args, **kwargs):
        if doc_id is None:
            raise Http404()
        context = self.get_context_data(**kwargs)
        if action and doc_id:
            if action == 'remove':
                WishListEntry.objects.remove(document_id=doc_id)
            else:
                WishListEntry.objects.create(document_id = doc_id)
        context['wishlist'] = WishList.objects.get(token=context['token'])
        context['doc_id'] = doc_id
        context['is_ajax'] = request.is_ajax()
        context['is_in_wishlist'] = doc_id in [e.document.id for e in context['wishlist'].entries]
        context['clear_item_on_remove'] = 'wishlist' in request.META.get('HTTP_REFERER')
        return self.render_to_response(context)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(WishlistItemView, self).dispatch(*args, **kwargs)


class PreorderlistView(JinjaTemplateMixin, ContextTokenMixin, TemplateView):
    template_name = 'shopping_list/preorderlist.html'
    context_object_name = 'preorderlist'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['preorderlist'] = Preorderlist.get_by_token(context['token'])
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """Post a doc_id to remove an item from the preorder list."""
        context = self.get_context_data(**kwargs)
        doc_id = request.POST.get('doc_id')
        if doc_id:
            PreorderlistItem.remove_from_list(context['token'], doc_id)
            messages.success(request, ugettext('The document was removed from your pre-order list.'))
        context['preorderlist'] = Preorderlist.get_by_token(context['token'])
        return self.render_to_response(context)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PreorderlistView, self).dispatch(*args, **kwargs)
