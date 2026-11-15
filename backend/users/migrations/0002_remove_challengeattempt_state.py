from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("challenge_attempts", "0001_move_challenge_attempt"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[migrations.DeleteModel(name="ChallengeAttempt")],
        ),
    ]
