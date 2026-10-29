from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from .models import Notification
from .services import notify


class NotifyServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notify_user', email='notifyuser@test.com', password='pass12345', role=User.Role.CANDIDATE
        )

    def test_notify_creates_notification(self):
        note = notify(self.user, "Test message", notification_type=Notification.Type.GENERAL, link_url='/somewhere/')
        self.assertIsNotNone(note)
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 1)
        self.assertFalse(note.is_read)

    def test_notify_with_none_user_does_not_crash(self):
        result = notify(None, "Should not crash")
        self.assertIsNone(result)
        self.assertEqual(Notification.objects.count(), 0)

    def test_notify_swallows_unexpected_errors(self):
        """A failed notification should never break the calling flow (e.g. job application submission)."""
        from unittest.mock import patch
        with patch('notifications.services.Notification.objects.create', side_effect=Exception("db down")):
            result = notify(self.user, "This will fail internally")
        self.assertIsNone(result)


class NotificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='notify_view', email='notifyview@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        self.client.login(username='notify_view', password='pass12345')

    def test_notification_list_shows_own_notifications_only(self):
        other_user = User.objects.create_user(
            username='other_notify', email='othernotify@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        notify(self.user, "My notification")
        notify(other_user, "Someone else's notification")

        response = self.client.get(reverse('notifications:list'))
        self.assertContains(response, "My notification")
        self.assertNotContains(response, "Someone else's notification")

    def test_mark_read_updates_is_read(self):
        note = notify(self.user, "Unread message", link_url='/candidate/dashboard/')
        self.assertFalse(note.is_read)
        response = self.client.get(reverse('notifications:mark_read', args=[note.pk]))
        note.refresh_from_db()
        self.assertTrue(note.is_read)
        self.assertRedirects(response, '/candidate/dashboard/')

    def test_mark_all_read(self):
        notify(self.user, "First")
        notify(self.user, "Second")
        self.client.get(reverse('notifications:mark_all_read'))
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 0)

    def test_cannot_mark_others_notification_read(self):
        other_user = User.objects.create_user(
            username='other_notify2', email='othernotify2@test.com', password='pass12345', role=User.Role.CANDIDATE
        )
        note = notify(other_user, "Not yours")
        response = self.client.get(reverse('notifications:mark_read', args=[note.pk]))
        self.assertEqual(response.status_code, 404)

    def test_unread_count_context_processor(self):
        notify(self.user, "One")
        notify(self.user, "Two")
        response = self.client.get(reverse('candidates:dashboard'))
        self.assertEqual(response.context['unread_notification_count'], 2)
