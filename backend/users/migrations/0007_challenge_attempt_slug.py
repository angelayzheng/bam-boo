import django.db.models.deletion
from django.db import migrations, models


def _challenge_slugs(apps, schema_editor):
    Challenge = apps.get_model("challenges", "Challenge")
    database = schema_editor.connection.alias
    return dict(Challenge.objects.using(database).values_list("pk", "slug"))


def _convert_attempts_to_slugs(apps, schema_editor):
    ChallengeAttempt = apps.get_model("users", "ChallengeAttempt")
    database = schema_editor.connection.alias
    slug_by_pk = _challenge_slugs(apps, schema_editor)
    for attempt in ChallengeAttempt.objects.using(database).iterator():
        slug = slug_by_pk.get(attempt.challenge_id)
        if slug is None:
            raise RuntimeError(
                f"Challenge {attempt.challenge_id} for attempt "
                f"{attempt.submission_id} no longer exists."
            )
        attempt.challenge_slug_id = slug
        attempt.save(using=database, update_fields=["challenge_slug"])


def _convert_attempts_to_ids(apps, schema_editor):
    ChallengeAttempt = apps.get_model("users", "ChallengeAttempt")
    database = schema_editor.connection.alias
    pk_by_slug = {
        slug: pk for pk, slug in _challenge_slugs(apps, schema_editor).items()
    }
    for attempt in ChallengeAttempt.objects.using(database).iterator():
        challenge_pk = pk_by_slug.get(attempt.challenge_slug_id)
        if challenge_pk is None:
            raise RuntimeError(
                f"Challenge {attempt.challenge_slug_id!r} for attempt "
                f"{attempt.submission_id} no longer exists."
            )
        attempt.challenge_id = challenge_pk
        attempt.save(using=database, update_fields=["challenge"])


def _convert_scores_to_slugs(apps, schema_editor):
    UserProfile = apps.get_model("users", "UserProfile")
    database = schema_editor.connection.alias
    slug_by_pk = _challenge_slugs(apps, schema_editor)
    known_slugs = set(slug_by_pk.values())
    for profile in UserProfile.objects.using(database).iterator():
        scores = {}
        for key, score in profile.scores.items():
            if key in known_slugs:
                slug = key
            else:
                try:
                    slug = slug_by_pk.get(int(key))
                except TypeError, ValueError:
                    slug = None
            if slug is not None:
                scores[slug] = max(scores.get(slug, 0), score)
        profile.scores = scores
        profile.total_score = sum(scores.values())
        profile.save(using=database, update_fields=["scores", "total_score"])


def _convert_scores_to_ids(apps, schema_editor):
    UserProfile = apps.get_model("users", "UserProfile")
    database = schema_editor.connection.alias
    slug_by_pk = _challenge_slugs(apps, schema_editor)
    pk_by_slug = {slug: challenge_pk for challenge_pk, slug in slug_by_pk.items()}
    known_ids = {str(challenge_pk) for challenge_pk in slug_by_pk}
    for profile in UserProfile.objects.using(database).iterator():
        scores = {}
        for key, score in profile.scores.items():
            if key in pk_by_slug:
                numeric_key = str(pk_by_slug[key])
            elif key in known_ids:
                numeric_key = key
            else:
                continue
            scores[numeric_key] = max(scores.get(numeric_key, 0), score)
        profile.scores = scores
        profile.total_score = sum(scores.values())
        profile.save(using=database, update_fields=["scores", "total_score"])


class Migration(migrations.Migration):
    dependencies = [
        ("challenges", "0004_remove_challenge_id"),
        ("users", "0006_score_points"),
    ]

    operations = [
        migrations.AlterField(
            model_name="challengeattempt",
            name="challenge",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attempts",
                to="challenges.challenge",
            ),
        ),
        migrations.AddField(
            model_name="challengeattempt",
            name="challenge_slug",
            field=models.ForeignKey(
                db_column="challenge_slug",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="slug_attempts",
                to="challenges.challenge",
                to_field="slug",
            ),
        ),
        migrations.RunPython(_convert_attempts_to_slugs, _convert_attempts_to_ids),
        migrations.RunPython(_convert_scores_to_slugs, _convert_scores_to_ids),
        migrations.RemoveField(
            model_name="challengeattempt",
            name="challenge",
        ),
        migrations.RenameField(
            model_name="challengeattempt",
            old_name="challenge_slug",
            new_name="challenge",
        ),
        migrations.AlterField(
            model_name="challengeattempt",
            name="challenge",
            field=models.ForeignKey(
                db_column="challenge_slug",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attempts",
                to="challenges.challenge",
                to_field="slug",
            ),
        ),
    ]
