from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)
    if created:
        # стартові категорії, щоб форма транзакції не була порожньою
        from budgeting.defaults import ensure_default_categories

        ensure_default_categories(instance)
