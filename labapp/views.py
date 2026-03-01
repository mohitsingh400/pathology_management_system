from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from .models import Service, Booking, Report, User, TestResult
from datetime import date, datetime, timedelta
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from django import forms
from .forms import ReportUploadForm  # Ensure you have created this form

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove password validation help texts
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        # Remove password validators
        self.fields['password1'].validators = []

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose a different one.')
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'patient'  # Set default role as patient
        if commit:
            user.save()
        return user

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_staff_or_admin(user):
    return user.is_authenticated and user.role in ['admin', 'staff']

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to our lab management system.')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    # Redirect if user is already logged in
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password')
            return render(request, 'login.html')
            
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Get the next URL from POST data first, then GET data
                next_url = request.POST.get('next') or request.GET.get('next')
                
                if next_url and next_url != '/logout/':
                    return redirect(next_url)
                    
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                return redirect('home')
            else:
                messages.error(request, 'Your account is disabled')
        else:
            messages.error(request, 'Invalid username or password')
        
        # If authentication fails, render login page with error
        return render(request, 'login.html', {
            'username': username,  # Preserve the username
            'next': request.GET.get('next', '')
        })
            
    return render(request, 'login.html', {
        'next': request.GET.get('next', '')
    })

@login_required
def home(request):
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    return render(request, 'home.html')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = timezone.now().date()
    context = {
        'total_patients': User.objects.filter(role='patient').count(),
        'today_appointments': Booking.objects.filter(date=today).count(),
        'pending_reports': Report.objects.filter(status='pending').count(),
        'recent_bookings': Booking.objects.all()[:5],
        'recent_reports': Report.objects.all()[:5],
    }
    return render(request, 'labapp/admin/dashboard.html', context)

@login_required
def service_list(request):
    query = request.GET.get('search', '')
    category = request.GET.get('category', '')
    
    services = Service.objects.filter(is_active=True)
    if query:
        services = services.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    if category:
        services = services.filter(category=category)
    
    
    return render(request, 'labapp/service_list.html', {
        'services': services,
        'search_query': query,
        'selected_category': category
    })

@login_required
def book_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        date_str = request.POST['date']
        time = request.POST['time']
        
        # Validate date and time
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if booking_date < date.today():
            messages.error(request, 'Cannot book appointments in the past')
            return redirect('book_service', service_id=service_id)
            
        # Create booking
        booking = Booking.objects.create(
            user=request.user,
            service=service,
            date=date_str,
            time=time,
            status='pending'
        )
        
        # Create empty report
        Report.objects.create(
            booking=booking,
            user=request.user,
            service=service,
            status='pending'
        )
        
        messages.success(request, 'Appointment booked successfully!')
        return redirect('my_bookings')
        
    return render(request, 'labapp/book_service.html', {
        'service': service,
        'today': date.today()
    })

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-date', '-time')
    return render(request, 'labapp/my_bookings.html', {'bookings': bookings})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        booking.status = 'cancelled'
        booking.cancellation_reason = reason
        booking.save()
        messages.success(request, 'Appointment cancelled successfully')
        return redirect('my_bookings')
    return render(request, 'labapp/cancel_booking.html', {'booking': booking})

@login_required
def reschedule_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if request.method == 'POST':
        new_date = request.POST['date']
        new_time = request.POST['time']
        
        # Create new booking
        new_booking = Booking.objects.create(
            user=request.user,
            service=booking.service,
            date=new_date,
            time=new_time,
            status='pending',
            previous_booking=booking
        )
        
        # Update old booking
        booking.status = 'rescheduled'
        booking.save()
        
        messages.success(request, 'Appointment rescheduled successfully')
        return redirect('my_bookings')
        
    return render(request, 'labapp/reschedule_booking.html', {
        'booking': booking,
        'today': date.today()
    })

@login_required
def view_reports(request):
    reports = Report.objects.filter(user=request.user).select_related('service', 'booking')
    return render(request, 'labapp/reports.html', {'reports': reports})

@login_required
def download_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    if report.user != request.user and not is_staff_or_admin(request.user):
        messages.error(request, 'Access denied')
        return redirect('view_reports')
        
    if not report.pdf_file:
        # Generate PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add content to PDF
        p.drawString(100, 750, f"Report for {report.service.name}")
        p.drawString(100, 700, f"Patient: {report.user.get_full_name()}")
        p.drawString(100, 650, f"Date: {report.generated_at.strftime('%Y-%m-%d')}")
        
        y = 600
        for result in report.test_results.all():
            p.drawString(100, y, f"{result.parameter}: {result.value} {result.unit}")
            p.drawString(100, y-15, f"Reference Range: {result.reference_range}")
            y -= 40
            
        p.save()
        
        # Save PDF to model
        report.pdf_file.save(
            f'report_{report.id}.pdf',
            BytesIO(buffer.getvalue())
        )
        
    # Serve the PDF
    response = HttpResponse(report.pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{report.id}.pdf"'
    return response

@login_required
@user_passes_test(is_staff_or_admin)
def update_test_results(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'POST':
        results_data = json.loads(request.POST['results'])
        
        # Update or create test results
        for result_data in results_data:
            TestResult.objects.update_or_create(
                report=report,
                parameter=result_data['parameter'],
                defaults={
                    'value': result_data['value'],
                    'unit': result_data['unit'],
                    'reference_range': result_data['reference_range'],
                    'is_abnormal': result_data['is_abnormal'],
                    'notes': result_data.get('notes', '')
                }
            )
            
        report.status = 'completed'
        report.reviewed_by = request.user
        report.save()
        
        # Delete existing PDF to regenerate with new results
        if report.pdf_file:
            report.pdf_file.delete()
            
        messages.success(request, 'Test results updated successfully')
        return redirect('admin_dashboard')
        
    return render(request, 'labapp/admin/update_results.html', {'report': report})

@login_required
@user_passes_test(is_admin)
def manage_services(request):
    services = Service.objects.all()
    return render(request, 'labapp/admin/manage_services.html', {'services': services})

@login_required
@user_passes_test(is_admin)
def edit_service(request, service_id=None):
    service = None if service_id is None else get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        # Handle service creation/update
        data = request.POST
        if service is None:
            service = Service.objects.create(
                name=data['name'],
                description=data['description'],
                price=data['price'],
                duration=data['duration'],
                category=data['category'],
                preparation_instructions=data['preparation_instructions'],
                is_active=data.get('is_active', False) == 'on'
            )
        else:
            service.name = data['name']
            service.description = data['description']
            service.price = data['price']
            service.duration = data['duration']
            service.category = data['category']
            service.preparation_instructions = data['preparation_instructions']
            service.is_active = data.get('is_active', False) == 'on'
            service.save()
            
        messages.success(request, 'Service saved successfully')
        return redirect('manage_services')
        
    return render(request, 'labapp/admin/edit_service.html', {'service': service})

@login_required
@user_passes_test(is_admin)
def generate_reports(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_type = request.GET.get('type', 'monthly')
    
    bookings = Booking.objects.all()
    if start_date and end_date:
        bookings = bookings.filter(date__range=[start_date, end_date])
    
    context = {
        'total_bookings': bookings.count(),
        'completed_bookings': bookings.filter(status='completed').count(),
        'cancelled_bookings': bookings.filter(status='cancelled').count(),
        'total_revenue': sum(b.service.price for b in bookings.filter(status='completed')),
        'bookings_by_service': bookings.values('service__name').annotate(count=Count('id')),
    }
    
    return render(request, 'labapp/admin/reports.html', context)

def user_logout(request):
    if request.method == 'POST' or request.method == 'GET':  # Allow both POST and GET
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

@login_required
def profile(request):
    return render(request, 'profile.html', {
        'user': request.user,
        'reports': Report.objects.filter(user=request.user).order_by('-generated_at')
    })

@login_required
def upload_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'POST':
        form = ReportUploadForm(request.POST, request.FILES, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, 'Report uploaded successfully.')
            return redirect('profile')  # Redirect to the profile or another page
    else:
        form = ReportUploadForm(instance=report)
    return render(request, 'labapp/upload_report.html', {'form': form, 'report': report})
