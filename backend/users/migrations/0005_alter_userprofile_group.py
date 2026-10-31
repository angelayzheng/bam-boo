import django.db.models.deletion
from django.db import migrations, models


def link_existing_groups(apps, schema_editor):
    Profile = apps.get_model("users", "UserProfile")
    Group = apps.get_model("auth", "Group")
    database = schema_editor.connection.alias
    for profile in Profile.objects.using(database).exclude(group_name="").iterator():
        group, _ = Group.objects.using(database).get_or_create(name=profile.group_name)
        profile.group_id = group.pk
        profile.save(using=database, update_fields=["group"])


def restore_group_names(apps, schema_editor):
    Profile = apps.get_model("users", "UserProfile")
    database = schema_editor.connection.alias
    for profile in Profile.objects.using(database).select_related("group").all().iterator():
        profile.group_name = profile.group.name if profile.group_id is not None else ""
        profile.save(using=database, update_fields=["group_name"])


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("users", "0004_userprofile_group"),
    ]

    operations = [
        migrations.RenameField(model_name="userprofile", old_name="group", new_name="group_name"),
        migrations.AddField(
            model_name="userprofile", name="group",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="profiles", to="auth.group"),
        ),
        migrations.RunPython(link_existing_groups, restore_group_names),
        migrations.RemoveField(model_name="userprofile", name="group_name"),
    ]
