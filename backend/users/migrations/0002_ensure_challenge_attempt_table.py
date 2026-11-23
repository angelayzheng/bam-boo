from django.db import migrations


def ensure_challenge_attempt_table(apps, schema_editor):
    if 'users_challengeattempt' in schema_editor.connection.introspection.table_names():
        return
    ChallengeAttempt = apps.get_model('users', 'ChallengeAttempt')
    schema_editor.create_model(ChallengeAttempt)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ensure_challenge_attempt_table, migrations.RunPython.noop),
    ]
