import re
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.views import PasswordResetDoneView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from budgeting.currency import fetch_exchange_rates

from .forms import ProfileEmailForm, ProfileSettingsForm, RegisterForm
from .models import UserProfile


def _latest_password_reset_link() -> str | None:
    """У DEBUG читаємо останній лист із EMAIL_FILE_PATH і витягуємо URL скидання."""
    mail_dir = Path(getattr(settings, 'EMAIL_FILE_PATH', '') or '')
    if not mail_dir.is_dir():
        return None
    files = sorted(mail_dir.glob('*'), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in files[:5]:
        try:
            text = path.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        match = re.search(r'https?://[^\s]+/accounts/reset/[^\s]+', text)
        if match:
            return match.group(0).rstrip('.)>')
    return None


class LocalPasswordResetDoneView(PasswordResetDoneView):
    """Після запиту показуємо лінк локально (немає реального SMTP)."""

    template_name = 'accounts/password_reset_done.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if settings.DEBUG:
            ctx['debug_reset_link'] = _latest_password_reset_link()
        return ctx



@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('budgeting:dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            users_group, _ = Group.objects.get_or_create(name='users')
            user.groups.add(users_group)
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, 'Реєстрацію завершено. Ласкаво просимо!')
            return redirect('budgeting:dashboard')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def _get_profile(user) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@login_required
@require_http_methods(['GET'])
def settings_page(request):
    profile = _get_profile(request.user)
    return render(request, 'accounts/settings_hub.html', {
        'profile': profile,
        'settings_section': 'hub',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def settings_profile(request):
    profile = _get_profile(request.user)
    email_form = ProfileEmailForm(instance=request.user)
    if request.method == 'POST':
        email_form = ProfileEmailForm(request.POST, instance=request.user)
        if email_form.is_valid():
            email_form.save()
            messages.success(request, 'Email оновлено.')
            return redirect('accounts:settings_profile')
    return render(request, 'accounts/settings_profile.html', {
        'profile': profile,
        'email_form': email_form,
        'settings_section': 'profile',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def settings_currency(request):
    profile = _get_profile(request.user)
    currency_form = ProfileSettingsForm(instance=profile)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'currency':
            currency_form = ProfileSettingsForm(request.POST, instance=profile)
            if currency_form.is_valid():
                currency_form.save()
                messages.success(request, 'Валюту відображення збережено.')
                return redirect('accounts:settings_currency')
        elif action == 'refresh_rates':
            from django.core.cache import cache
            from budgeting.currency import CACHE_KEY, STALE_KEY

            cache.delete(CACHE_KEY)
            cache.delete(STALE_KEY)
            payload = fetch_exchange_rates(force=True)
            messages.success(
                request,
                f'Курси оновлено ({payload.get("source", "—")}, {payload.get("fetched_at", "")}).',
            )
            return redirect('accounts:settings_currency')
    return render(request, 'accounts/settings_currency.html', {
        'profile': profile,
        'currency_form': currency_form,
        'settings_section': 'currency',
    })


@login_required
@require_http_methods(['GET'])
def settings_security(request):
    profile = _get_profile(request.user)
    return render(request, 'accounts/settings_security.html', {
        'profile': profile,
        'settings_section': 'security',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def settings_data(request):
    profile = _get_profile(request.user)
    return render(request, 'accounts/settings_data.html', {
        'profile': profile,
        'settings_section': 'data',
    })


@login_required
@require_POST
def dismiss_onboarding(request):
    profile = _get_profile(request.user)
    profile.onboarding_dismissed = True
    profile.save(update_fields=['onboarding_dismissed'])
    messages.info(request, 'Підказки старту приховано.')
    return redirect('budgeting:dashboard')


@login_required
@require_POST
def delete_account(request):
    user = request.user
    logout(request)
    user.delete()
    messages.success(request, 'Акаунт і всі пов’язані дані видалено.')
    return redirect('accounts:login')
