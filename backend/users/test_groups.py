from django.contrib.auth.models import Group, Permission, User
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase

from .models import UserProfile


class SignupGroupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.zeta = Group.objects.create(name="Zeta team")
        cls.alpha = Group.objects.create(name="Alpha team")
        cls.alpha.permissions.add(Permission.objects.first())

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def signup(self, **extra):
        token = self.client.get("/api/users/auth/csrf/").json()["csrfToken"]
        return self.client.post(
            "/api/users/auth/signup/",
            data={"username": "ada", "password": "Group!Maple7River", **extra},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

    def test_group_choices_are_public_sorted_and_hide_permissions(self):
        response = self.client.get("/api/users/groups/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "groups": [
                    {"id": self.alpha.pk, "name": "Alpha team"},
                    {"id": self.zeta.pk, "name": "Zeta team"},
                ]
            },
        )
        self.assertIn("no-store", response.headers["Cache-Control"])
        token = self.client.get("/api/users/auth/csrf/").json()["csrfToken"]
        self.assertEqual(
            self.client.post("/api/users/groups/", HTTP_X_CSRFTOKEN=token).status_code,
            405,
        )

    def test_signup_links_profile_without_granting_permission_membership(self):
        self.assertEqual(self.signup(group_id=self.alpha.pk).status_code, 201)
        user = User.objects.get(username="ada")
        self.assertEqual(user.profile.group, self.alpha)
        self.assertEqual(
            list(self.alpha.profiles.values_list("user_id", flat=True)), [user.pk]
        )
        self.assertFalse(user.groups.exists())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_optional_group_and_empty_choices(self):
        Group.objects.all().delete()
        self.assertEqual(self.client.get("/api/users/groups/").json(), {"groups": []})
        for username, extra in (("ada", {}), ("grace", {"group_id": None})):
            self.assertEqual(self.signup(username=username, **extra).status_code, 201)
            self.assertIsNone(User.objects.get(username=username).profile.group_id)
        self.assertIsNone(
            User.objects.create_user(username="existing").profile.group_id
        )

    def test_invalid_group_does_not_create_an_account(self):
        for group_id in (999999, -1, 0, True, "1", [], {}):
            with self.subTest(group_id=group_id):
                response = self.signup(group_id=group_id)
                self.assertEqual(response.status_code, 400)
                self.assertIn("group_id", response.json()["errors"])
                self.assertFalse(User.objects.exists())
                self.assertFalse(UserProfile.objects.exists())

    def test_group_stays_out_of_other_response_schemas(self):
        response = self.signup(group_id=self.alpha.pk)
        user = User.objects.get(username="ada")
        self.assertEqual(set(response.json()["user"]), {"id", "username", "email"})
        self.assertNotIn("group", self.client.get("/api/users/auth/me/").json()["user"])
        profile = self.client.get(f"/api/users/{user.pk}/profile/").json()
        self.assertNotIn("group", profile)
        self.assertNotIn("group_id", profile)
        leader = self.client.get("/api/users/leaderboard/").json()["leaderboard"][0]
        self.assertNotIn("group", leader)
        self.assertNotIn("group_id", leader)

    def test_deleting_group_preserves_user_and_profile(self):
        self.signup(group_id=self.alpha.pk)
        user = User.objects.get(username="ada")
        self.alpha.delete()
        self.assertIsNone(UserProfile.objects.get(user=user).group_id)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())


class ProfileGroupMigrationTests(TransactionTestCase):
    def test_existing_names_link_to_groups_and_can_be_restored(self):
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        previous = [("users", "0004_userprofile_group")]
        try:
            executor.migrate(previous)
            old = executor.loader.project_state(previous).apps
            OldUser = old.get_model("auth", "User")
            OldGroup = old.get_model("auth", "Group")
            OldProfile = old.get_model("users", "UserProfile")
            group = OldGroup.objects.create(name="Existing team")
            profile_ids = []
            for index, name in enumerate(("Existing team", "New team", "New team", "")):
                user = OldUser.objects.create(username=f"migration-{index}")
                profile = OldProfile.objects.create(
                    user_id=user.pk, group=name, scores={"42": 67}, total_score=67
                )
                profile_ids.append(profile.pk)
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            current = executor.loader.project_state(latest).apps
            Profile = current.get_model("users", "UserProfile")
            CurrentGroup = current.get_model("auth", "Group")
            profiles = [Profile.objects.get(pk=pk) for pk in profile_ids]
            self.assertEqual(profiles[0].group_id, group.pk)
            self.assertEqual(profiles[1].group_id, profiles[2].group_id)
            self.assertEqual(profiles[1].group.name, "New team")
            self.assertIsNone(profiles[3].group_id)
            self.assertEqual(CurrentGroup.objects.count(), 2)
            self.assertEqual(profiles[0].scores, {"42": 67})
            self.assertEqual(profiles[0].total_score, 67)
            self.assertEqual(
                current.get_model("auth", "User").groups.through.objects.count(), 0
            )
            executor = MigrationExecutor(connection)
            executor.migrate(previous)
            restored = executor.loader.project_state(previous).apps.get_model(
                "users", "UserProfile"
            )
            self.assertEqual(
                [restored.objects.get(pk=pk).group for pk in profile_ids],
                ["Existing team", "New team", "New team", ""],
            )
        finally:
            MigrationExecutor(connection).migrate(latest)
