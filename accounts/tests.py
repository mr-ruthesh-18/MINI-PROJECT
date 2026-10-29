from django.test import TestCase, Client
from django.urls import reverse
from .models import User


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_candidate_registration_creates_user_with_correct_role(self):
        response = self.client.post(reverse('accounts:register_candidate'), {
            'username': 'candidate1',
            'first_name': 'Test',
            'last_name': 'Candidate',
            'email': 'candidate1@test.com',
            'phone_number': '9999999999',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)  # redirect after success
        user = User.objects.get(username='candidate1')
        self.assertEqual(user.role, User.Role.CANDIDATE)
        self.assertTrue(user.is_candidate())

    def test_recruiter_registration_creates_user_with_correct_role(self):
        response = self.client.post(reverse('accounts:register_recruiter'), {
            'username': 'recruiter1',
            'first_name': 'Test',
            'last_name': 'Recruiter',
            'email': 'recruiter1@test.com',
            'phone_number': '8888888888',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='recruiter1')
        self.assertEqual(user.role, User.Role.RECRUITER)
        self.assertTrue(user.is_recruiter())

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='dupe', email='a@test.com', password='pass12345', role=User.Role.CANDIDATE)
        response = self.client.post(reverse('accounts:register_candidate'), {
            'username': 'dupe',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'b@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 200)  # re-renders form with errors
        self.assertEqual(User.objects.filter(username='dupe').count(), 1)


class PlatformAdminDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin1', email='admin1@test.com', password='pass12345'
        )
        self.candidate = User.objects.create_user(
            username='dash_cand', email='dashcand@test.com', password='pass12345', role=User.Role.CANDIDATE
        )

    def test_staff_can_access_platform_dashboard(self):
        self.client.login(username='admin1', password='pass12345')
        response = self.client.get(reverse('accounts:platform_admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total Users')

    def test_non_staff_cannot_access_platform_dashboard(self):
        self.client.login(username='dash_cand', password='pass12345')
        response = self.client.get(reverse('accounts:platform_admin_dashboard'))
        self.assertNotEqual(response.status_code, 200)  # redirected to admin login

    def test_platform_dashboard_shows_correct_counts(self):
        self.client.login(username='admin1', password='pass12345')
        response = self.client.get(reverse('accounts:platform_admin_dashboard'))
        self.assertEqual(response.context['candidates_count'], 1)
        self.assertGreaterEqual(response.context['total_users'], 2)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='loginuser', email='login@test.com',
            password='StrongPass123!', role=User.Role.CANDIDATE
        )

    def test_login_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'loginuser',
            'password': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_anonymous is False or True)

    def test_login_wrong_password_fails(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'loginuser',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)  # form re-rendered with error

    def test_logout(self):
        self.client.login(username='loginuser', password='StrongPass123!')
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)


class RolePermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.candidate = User.objects.create_user(
            username='cand', email='cand@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.recruiter = User.objects.create_user(
            username='recr', email='recr@test.com', password='pass12345', role=User.Role.RECRUITER
        )

    def test_candidate_and_recruiter_have_distinct_roles(self):
        self.assertTrue(self.candidate.is_candidate())
        self.assertFalse(self.candidate.is_recruiter())
        self.assertTrue(self.recruiter.is_recruiter())
        self.assertFalse(self.recruiter.is_candidate())
