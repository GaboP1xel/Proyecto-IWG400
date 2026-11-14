from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AuthenticationViewsTests(TestCase):
    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Iniciar sesión")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_login_with_valid_credentials(self):
        User.objects.create_user(username="ana", password="S0lid!Passphrase_9")

        response = self.client.post(
            reverse("login"),
            {"username": "ana", "password": "S0lid!Passphrase_9"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_invalid_credentials_shows_spanish_error(self):
        response = self.client.post(
            reverse("login"),
            {"username": "ana", "password": "incorrecta"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El nombre de usuario o la contraseña no son correctos.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_ends_authenticated_session(self):
        User.objects.create_user(username="ana", password="S0lid!Passphrase_9")
        self.client.login(username="ana", password="S0lid!Passphrase_9")

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_registration_page_loads(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crear cuenta")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_registration_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("register"),
            {"username": "ana", "password": "S0lid!Passphrase_9"},
            follow=True,
        )

        user = User.objects.get(username="ana")
        self.assertTrue(user.check_password("S0lid!Passphrase_9"))
        self.assertRedirects(response, reverse("login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "Tu cuenta fue creada. Ya puedes iniciar sesión.")

    def test_registration_rejects_duplicate_username(self):
        User.objects.create_user(username="ana", password="S0lid!Passphrase_9")

        response = self.client.post(
            reverse("register"),
            {"username": "ana", "password": "D1fferent!Passphrase_8"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este nombre de usuario ya está registrado.")
        self.assertEqual(User.objects.filter(username="ana").count(), 1)

    def test_registration_rejects_invalid_password(self):
        response = self.client.post(
            reverse("register"),
            {"username": "ana", "password": "abc"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "La contraseña debe tener al menos 8 caracteres.")
        self.assertFalse(User.objects.filter(username="ana").exists())
