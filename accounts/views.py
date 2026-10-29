from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.db.models import Count
import json

from .forms import CandidateRegisterForm, RecruiterRegisterForm
from .models import User


def register_choice(request):
    """Landing page asking whether the user is registering as a Candidate or Recruiter."""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'accounts/register_choice.html')


def register_candidate(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CandidateRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to SmartRecruit AI! Your candidate account is ready.")
            return redirect('home')
    else:
        form = CandidateRegisterForm()

    return render(request, 'accounts/register_candidate.html', {'form': form})


def register_recruiter(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RecruiterRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to SmartRecruit AI! Your recruiter account is ready.")
            return redirect('home')
    else:
        form = RecruiterRegisterForm()

    return render(request, 'accounts/register_recruiter.html', {'form': form})


class SmartRecruitLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().first_name or form.get_user().username}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


@staff_member_required
def platform_admin_dashboard(request):
    """
    Custom platform-wide stats dashboard for staff/superusers - distinct from
    Django's built-in /admin/ (which is for record-level CRUD). This page is
    for at-a-glance platform health: totals, breakdowns, and recent activity.
    """
    from companies.models import Company
    from jobs.models import Job
    from applications.models import Application

    total_users = User.objects.count()
    candidates_count = User.objects.filter(role=User.Role.CANDIDATE).count()
    recruiters_count = User.objects.filter(role=User.Role.RECRUITER).count()
    active_users_count = User.objects.filter(is_active=True).count()

    companies_count = Company.objects.count()
    jobs_count = Job.objects.count()
    open_jobs_count = Job.objects.filter(status='open').count()
    closed_jobs_count = Job.objects.filter(status='closed').count()
    applications_count = Application.objects.count()

    # Application status breakdown (for a chart)
    status_counts = Application.objects.values('status').annotate(count=Count('id'))
    status_map = {row['status']: row['count'] for row in status_counts}
    status_labels = json.dumps([Application.Status(s).label for s in status_map.keys()])
    status_values = json.dumps(list(status_map.values()))

    # Job status breakdown (for a second chart)
    job_status_labels = json.dumps(['Open', 'Closed'])
    job_status_values = json.dumps([open_jobs_count, closed_jobs_count])

    recent_users = User.objects.order_by('-date_joined')[:8]
    recent_jobs = Job.objects.select_related('company').order_by('-created_at')[:8]
    recent_applications = Application.objects.select_related('candidate__user', 'job').order_by('-applied_at')[:8]

    context = {
        'total_users': total_users,
        'candidates_count': candidates_count,
        'recruiters_count': recruiters_count,
        'active_users_count': active_users_count,
        'companies_count': companies_count,
        'jobs_count': jobs_count,
        'open_jobs_count': open_jobs_count,
        'applications_count': applications_count,
        'status_labels': status_labels,
        'status_values': status_values,
        'job_status_labels': job_status_labels,
        'job_status_values': job_status_values,
        'has_applications': applications_count > 0,
        'recent_users': recent_users,
        'recent_jobs': recent_jobs,
        'recent_applications': recent_applications,
    }
    return render(request, 'accounts/admin_dashboard.html', context)
