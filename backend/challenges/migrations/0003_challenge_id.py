from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("challenges", "0002_challenge_level_id")]

    operations = [
        migrations.RenameField(
            model_name="challenge",
            old_name="level_id",
            new_name="challenge_id",
        ),
    ]
