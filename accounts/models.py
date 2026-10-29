from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for SmartRecruit AI.

    Admin access is handled through Django's built-in is_staff / is_superuser
    flags (via the standard Django admin), not through the `role` field.
    `role` only distinguishes the two platform-facing user types.
    """

    class Role(models.TextChoices):
        CANDIDATE = 'candidate', 'Candidate'
        RECRUITER = 'recruiter', 'Recruiter'

    role = models.CharField(max_length=20, choices=Role.choices)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_candidate(self):
        return self.role == self.Role.CANDIDATE

    def is_recruiter(self):
        return self.role == self.Role.RECRUITER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
