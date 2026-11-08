from django.contrib.auth.models import Group, Permission, User
from django.test import Client, TestCase

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
