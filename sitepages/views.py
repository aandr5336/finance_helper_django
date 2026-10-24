from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods


def _page(request, template, title, **extra):
    ctx = {'page_title': title, **extra}
    return render(request, template, ctx)


@require_GET
def about(request):
    return _page(request, 'sitepages/about.html', 'Про нас')


@require_GET
def faq(request):
    return _page(request, 'sitepages/faq.html', 'FAQ')


@require_GET
def privacy(request):
    return _page(request, 'sitepages/privacy.html', 'Політика конфіденційності')


@require_GET
def terms(request):
    return _page(request, 'sitepages/terms.html', 'Умови використання')


@require_GET
def pricing(request):
    return _page(request, 'sitepages/pricing.html', 'Тарифи')


@require_GET
def changelog(request):
    return _page(request, 'sitepages/changelog.html', 'Що нового')


@require_http_methods(['GET', 'POST'])
def contact(request):
    sent = False
    if request.method == 'POST':
        # без зовнішнього email — зберігаємо як повідомлення користувачу
        sent = True
    return _page(request, 'sitepages/contact.html', 'Контакти', contact_sent=sent)
