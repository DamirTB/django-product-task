from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

REGISTER_URL = reverse('auth-register')
LOGIN_URL = reverse('rest_login')
LOGOUT_URL = reverse('rest_logout')
USER_URL = reverse('rest_user_details')
PASSWORD_CHANGE_URL = reverse('rest_password_change')
TOKEN_REFRESH_URL = reverse('token_refresh')


def make_user(**kwargs) -> User:
    defaults = {
        'email': 'user@example.com',
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User',
        'password': 'StrongPass123!',
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


VALID_REGISTER_DATA = {
    'email': 'newuser@example.com',
    'username': 'newuser',
    'first_name': 'New',
    'last_name': 'User',
    'password': 'StrongPass123!',
    'password_confirm': 'StrongPass123!',
}


class RegisterViewTests(APITestCase):

    def test_successful_registration_returns_201(self):
        response = self.client.post(REGISTER_URL, VALID_REGISTER_DATA)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_successful_registration_returns_tokens(self):
        response = self.client.post(REGISTER_URL, VALID_REGISTER_DATA)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_successful_registration_returns_user_data(self):
        response = self.client.post(REGISTER_URL, VALID_REGISTER_DATA)
        user = response.data['user']
        self.assertEqual(user['email'], VALID_REGISTER_DATA['email'])
        self.assertEqual(user['username'], VALID_REGISTER_DATA['username'])

    def test_duplicate_email_returns_400(self):
        make_user(email='newuser@example.com', username='existing')
        response = self.client.post(REGISTER_URL, VALID_REGISTER_DATA)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_username_returns_400(self):
        make_user(email='other@example.com', username='newuser')
        response = self.client.post(REGISTER_URL, VALID_REGISTER_DATA)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mismatched_passwords_returns_400(self):
        data = {**VALID_REGISTER_DATA, 'password_confirm': 'DifferentPass!'}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_email_returns_400(self):
        data = {k: v for k, v in VALID_REGISTER_DATA.items() if k != 'email'}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_returns_400(self):
        data = {**VALID_REGISTER_DATA, 'password': '123', 'password_confirm': '123'}
        response = self.client.post(REGISTER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTests(APITestCase):

    def setUp(self):
        self.user = make_user()

    def test_successful_login_returns_200(self):
        response = self.client.post(LOGIN_URL, {'email': 'user@example.com', 'password': 'StrongPass123!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_successful_login_returns_tokens(self):
        response = self.client.post(LOGIN_URL, {'email': 'user@example.com', 'password': 'StrongPass123!'})
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_wrong_password_returns_400(self):
        response = self.client.post(LOGIN_URL, {'email': 'user@example.com', 'password': 'WrongPass!'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_email_returns_400(self):
        response = self.client.post(LOGIN_URL, {'email': 'nobody@example.com', 'password': 'StrongPass123!'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_credentials_returns_400(self):
        response = self.client.post(LOGIN_URL, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        login = self.client.post(LOGIN_URL, {'email': 'user@example.com', 'password': 'StrongPass123!'})
        self.access = login.data['access']
        self.refresh = login.data['refresh']

    def test_logout_requires_authentication(self):
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful_logout_returns_200(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')
        response = self.client.post(LOGOUT_URL, {'refresh': self.refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_blacklisted_refresh_token_cannot_be_reused(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')
        self.client.post(LOGOUT_URL, {'refresh': self.refresh})
        response = self.client.post(TOKEN_REFRESH_URL, {'refresh': self.refresh})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserDetailsViewTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        login = self.client.post(LOGIN_URL, {'email': 'user@example.com', 'password': 'StrongPass123!'})
        self.access = login.data['access']

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(USER_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_gets_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')
        response = self.client.get(USER_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_authenticated_user_can_update_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')
        response = self.client.patch(USER_URL, {'first_name': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')


class PasswordChangeViewTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        login = self.client.post(LOGIN_URL, {'email': 'user@example.com', 'password': 'StrongPass123!'})
        self.access = login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')

    def test_unauthenticated_request_returns_401(self):
        self.client.credentials()
        response = self.client.post(PASSWORD_CHANGE_URL, {
            'new_password1': 'NewPass456!',
            'new_password2': 'NewPass456!',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful_password_change_returns_200(self):
        response = self.client.post(PASSWORD_CHANGE_URL, {
            'new_password1': 'NewPass456!',
            'new_password2': 'NewPass456!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mismatched_new_passwords_returns_400(self):
        response = self.client.post(PASSWORD_CHANGE_URL, {
            'new_password1': 'NewPass456!',
            'new_password2': 'DifferentPass789!',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_changed_password_works_on_next_login(self):
        self.client.post(PASSWORD_CHANGE_URL, {
            'new_password1': 'NewPass456!',
            'new_password2': 'NewPass456!',
        })
        self.client.credentials()
        response = self.client.post(LOGIN_URL, {'email': 'user@example.com', 'password': 'NewPass456!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TokenRefreshViewTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        login = self.client.post(LOGIN_URL, {'email': 'user@example.com', 'password': 'StrongPass123!'})
        self.refresh = login.data['refresh']

    def test_valid_refresh_token_returns_new_access_token(self):
        response = self.client.post(TOKEN_REFRESH_URL, {'refresh': self.refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_invalid_refresh_token_returns_401(self):
        response = self.client.post(TOKEN_REFRESH_URL, {'refresh': 'invalid.token.here'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_refresh_token_returns_4xx(self):
        response = self.client.post(TOKEN_REFRESH_URL, {})
        self.assertIn(response.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED))
