# django imports
from django.core.cache import cache
from django.template import Library, Node, TemplateSyntaxError
from django.utils.translation import ugettext as _
import portlets.utils
from portlets.models import Slot
import lfs.core.utils
from lfs.catalog.models import Category

from django.conf import settings
register = Library()

class SlotsInformationNode(Node):
    """
    """
    def render(self, context):
        request = context.get("request")
        object = context.get("category") or context.get("product") or context.get("page")
        if object is None:
            object = lfs.core.utils.get_default_shop(request)

        slots = cache.get("slots")
        if slots is None:
            slots = Slot.objects.all()
            cache.set("slots", slots)

        for slot in slots:
            cache_key = "has-portlets-%s-%s-%s" % (object.__class__.__name__, object.id, slot.name)
            has_portlets = cache.get(cache_key)
            if has_portlets is None:
                has_portlets = portlets.utils.has_portlets(object, slot)
                cache.set(cache_key, has_portlets)

            context["Slot%s" % slot.name] = has_portlets

        cache_key = "content-class-%s-%s" % (object.__class__.__name__, object.id)
        content_class = cache.get(cache_key)
        if content_class is None:
            content_class = "col-md-12"
            if context.get("SlotLeft", None) and context.get("SlotRight", None):
                content_class = "col-md-6"
            elif context.get("SlotLeft", None):
                content_class = "col-md-9"
            elif context.get("SlotRight", None):
                content_class = "col-md-9"

            cache.set(cache_key, content_class)

        context["content_class"] = content_class
        return ''

def do_slots_information(parser, token):
    """Calculates some context variables based on displayed slots.
    """
    bits = token.contents.split()
    len_bits = len(bits)
    if len_bits != 1:
        raise TemplateSyntaxError(_('%s tag needs no argument') % bits[0])

    return SlotsInformationNode()

register.tag('slots_information', do_slots_information)


@register.inclusion_tag('lfs/mail/mail_html_footer.html', takes_context=True)
def email_html_footer(context):
    request = context.get('request', None)
    shop = lfs.core.utils.get_default_shop(request)
    return {
        "shop": shop
    }


@register.inclusion_tag('lfs/mail/mail_text_footer.html', takes_context=True)
def email_text_footer(context):
    request = context.get('request', None)
    shop = lfs.core.utils.get_default_shop(request)
    return {
        "shop": shop
    }

@register.inclusion_tag('lfs/catalog/top_level_categories.html', takes_context=True)
def menu_top_level_categories(context):
    """Displays the top level categories.
    """
    request = context.get("request")
    obj = context.get("product") or context.get("category")

    categories = []
    top_category = lfs.catalog.utils.get_current_top_category(request, obj)

    for category in Category.objects.filter(parent=None, exclude_from_navigation=False):

        if top_category:
            current = top_category.id == category.id
        else:
            current = False

        categories.append({
            "url": category.get_absolute_url(),
            "name": category.name,
            "current": current,
        })

    return {
        "categories": categories,
    }

@register.inclusion_tag('lfs/price_vat.html', takes_context=True)
def price_vat(context):
    """Displays the VAT
    """

    settings.SHOW_VAT = getattr(settings, 'SHOW_VAT', True)
    if settings.SHOW_VAT:
        return {'VAT': True}
    else:
        return {'VAT': False}

@register.inclusion_tag('lfs/toc.html', takes_context=True)
def toc_link(context):
    """ show toc checkbox """

    settings.TOC_PAGE_URL = getattr(settings, 'TOC_PAGE_URL', '/term-and-conditions')
    return {'url':settings.TOC_PAGE_URL}
    
