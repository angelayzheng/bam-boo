from django.core.validators import MaxValueValidator
from django.db import migrations, models


def points_from_percentage(score):
    return round(float(score) * 3 / 100)


def percentage_from_points(score):
    return round(score * 100 / 3)


def convert_scores(apps, schema_editor, converter):
    UserProfile = apps.get_model("users", "UserProfile")
    ChallengeAttempt = apps.get_model("users", "ChallengeAttempt")
    database = schema_editor.connection.alias

    for profile in UserProfile.objects.using(database).iterator():
        profile.scores = {
            challenge_id: converter(score)
            for challenge_id, score in profile.scores.items()
        }
        profile.total_score = sum(profile.scores.values())
        profile.save(using=database, update_fields=["scores", "total_score"])

    for attempt in ChallengeAttempt.objects.using(database).iterator():
        attempt.score = converter(attempt.score)
        attempt.save(using=database, update_fields=["score"])


def convert_to_points(apps, schema_editor):
    convert_scores(apps, schema_editor, points_from_percentage)


def convert_to_percentages(apps, schema_editor):
    convert_scores(apps, schema_editor, percentage_from_points)


class Migration(migrations.Migration):
    dependencies = [("users", "0005_alter_userprofile_group")]

    operations = [
        migrations.RunPython(convert_to_points, convert_to_percentages),
        migrations.AlterField(
            model_name="userprofile",
            name="total_score",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="challengeattempt",
            name="score",
            field=models.PositiveSmallIntegerField(
                validators=[MaxValueValidator(3)]
            ),
        ),
    ]
