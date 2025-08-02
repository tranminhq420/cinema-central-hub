# cinemas/admin_views.py (create this file)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .forms import CustomUserCreationForm
from django import forms
import json

# Check if user is admin/staff


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',
                  'email', 'is_active', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class AdminUserCreationForm(forms.ModelForm):
    """Extended user creation form that allows setting admin status"""
    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={'class': 'form-input'}))
    first_name = forms.CharField(
        max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(
        attrs={'class': 'form-input'}))
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
        help_text='Enter a strong password.'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
        help_text='Enter the same password as before, for verification.'
    )
    is_staff = forms.BooleanField(
        required=False,
        label='Admin Access',
        help_text='Designates whether the user can access admin areas.',
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label='Active',
        help_text='Designates whether this user should be treated as active.',
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email",
                  "password1", "password2", "is_staff", "is_active")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add placeholders
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last Name'
        self.fields['email'].widget.attrs['placeholder'] = 'Email Address'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_staff = self.cleaned_data.get("is_staff", False)
        user.is_active = self.cleaned_data.get("is_active", True)
        if commit:
            user.save()
        return user


@login_required
# @user_passes_test(is_admin)
def admin_dashboard(request):
    """Main admin dashboard with user statistics"""
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    staff_users = User.objects.filter(is_staff=True).count()

    recent_users = User.objects.order_by('-date_joined')[:5]

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'staff_users': staff_users,
        'recent_users': recent_users,
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
# @user_passes_test(is_admin)
def user_list(request):
    """List all users with search and pagination"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')

    users = User.objects.all().order_by('-date_joined')

    # Apply search filter
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Apply status filter
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'staff':
        users = users.filter(is_staff=True)

    # Pagination
    paginator = Paginator(users, 20)  # Show 20 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_users': users.count(),
    }
    return render(request, 'admin/user_list.html', context)


@login_required
# @user_passes_test(is_admin)
def user_detail(request, user_id):
    """View detailed information about a specific user"""
    user = get_object_or_404(User, id=user_id)

    context = {
        'user_detail': user,
    }
    return render(request, 'admin/user_detail.html', context)


@login_required
# @user_passes_test(is_admin)
def user_create(request):
    """Create a new user"""
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, f'User "{user.username}" created successfully!')
            return redirect('user_admin:user_detail', user_id=user.id)
    else:
        form = AdminUserCreationForm()

    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'admin/user_form.html', context)


@login_required
# @user_passes_test(is_admin)
def user_edit(request, user_id):
    """Edit an existing user"""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'User "{user.username}" updated successfully!')
            return redirect('user_admin:user_detail', user_id=user.id)
    else:
        form = UserEditForm(instance=user)

    context = {
        'form': form,
        'user_detail': user,
        'action': 'Edit',
    }
    return render(request, 'admin/user_form.html', context)


@login_required
# @user_passes_test(is_admin)
@require_POST
def user_delete(request, user_id):
    """Delete a user"""
    user = get_object_or_404(User, id=user_id)

    # Prevent deletion of superusers and self
    if user.is_superuser:
        messages.error(request, 'Cannot delete superuser accounts.')
        return redirect('user_admin:user_detail', user_id=user.id)

    if user == request.user:
        messages.error(request, 'Cannot delete your own account.')
        return redirect('user_admin:user_detail', user_id=user.id)

    username = user.username
    user.delete()
    messages.success(request, f'User "{username}" deleted successfully!')
    return redirect('user_admin:user_list')


@login_required
# @user_passes_test(is_admin)
@require_POST
def user_toggle_status(request, user_id):
    """Toggle user active status via AJAX"""
    user = get_object_or_404(User, id=user_id)

    # Prevent deactivating superusers and self
    if user.is_superuser and user.is_active:
        return JsonResponse({
            'success': False,
            'message': 'Cannot deactivate superuser accounts.'
        })

    if user == request.user and user.is_active:
        return JsonResponse({
            'success': False,
            'message': 'Cannot deactivate your own account.'
        })

    user.is_active = not user.is_active
    user.save()

    status = 'activated' if user.is_active else 'deactivated'
    return JsonResponse({
        'success': True,
        'message': f'User "{user.username}" {status} successfully!',
        'is_active': user.is_active
    })


@login_required
# @user_passes_test(is_admin)
def bulk_actions(request):
    """Handle bulk actions on users"""
    if request.method == 'POST':
        action = request.POST.get('action')
        user_ids = request.POST.getlist('selected_users')

        if not user_ids:
            messages.warning(request, 'No users selected.')
            return redirect('user_admin:user_list')

        users = User.objects.filter(id__in=user_ids)

        if action == 'activate':
            users.update(is_active=True)
            messages.success(request, f'{users.count()} users activated.')
        elif action == 'deactivate':
            # Exclude superusers and current user
            users = users.exclude(is_superuser=True).exclude(
                id=request.user.id)
            users.update(is_active=False)
            messages.success(request, f'{users.count()} users deactivated.')
        elif action == 'delete':
            # Exclude superusers and current user
            users = users.exclude(is_superuser=True).exclude(
                id=request.user.id)
            count = users.count()
            users.delete()
            messages.success(request, f'{count} users deleted.')

    return redirect('admin:user_list')
