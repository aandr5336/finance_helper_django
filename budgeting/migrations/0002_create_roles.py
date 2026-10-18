from django.db import migrations


def create_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ct, _ = ContentType.objects.get_or_create(app_label='budgeting', model='transaction')
    perm, _ = Permission.objects.get_or_create(
        codename='can_view_all_transactions',
        content_type=ct,
        defaults={'name': 'Може переглядати всі транзакції'},
    )
    Group.objects.get_or_create(name='users')
    analysts, _ = Group.objects.get_or_create(name='analysts')
    analysts.permissions.add(perm)


def remove_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['users', 'analysts']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('budgeting', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(create_roles, remove_roles),
    ]
