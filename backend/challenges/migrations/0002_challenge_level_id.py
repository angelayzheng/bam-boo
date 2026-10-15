from django.db import migrations, models


def assign_level_ids(apps, schema_editor):
    Challenge = apps.get_model("challenges", "Challenge")
    for challenge in Challenge.objects.using(schema_editor.connection.alias).all():
        # Older demo seeds used the installation date. Give every copy the
        # canonical package ID, without changing its existing database PK.
        challenge.level_id = (
            "2026-10-15-forgot-password-x3"
            if challenge.slug == "forgot-password-x3"
            else f"{challenge.challenge_date}-{challenge.slug}"
        )
        challenge.save(update_fields=["level_id"])


class Migration(migrations.Migration):
    dependencies = [("challenges", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="challenge",
            name="level_id",
            field=models.SlugField(
                max_length=160, null=True, unique=True, editable=False
            ),
        ),
        migrations.RunPython(assign_level_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="challenge",
            name="level_id",
            field=models.SlugField(max_length=160, unique=True, editable=False),
        ),
    ]
