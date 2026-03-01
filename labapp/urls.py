from django.urls import path
from . import views
from .views import upload_report, download_report

urlpatterns = [
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('accounts/logout/', views.user_logout, name='account_logout'),
    
    # Common URLs
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('services/', views.service_list, name='service_list'),
    
    # Patient URLs
    path('book/<int:service_id>/', views.book_service, name='book_service'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('booking/<int:booking_id>/reschedule/', views.reschedule_booking, name='reschedule_booking'),
    path('reports/', views.view_reports, name='view_reports'),
    path('report/<int:report_id>/download/', views.download_report, name='download_report'),
    path('upload-report/<int:report_id>/', upload_report, name='upload_report'),
    path('download-report/<int:report_id>/', download_report, name='download_report'),
    
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/services/', views.manage_services, name='manage_services'),
    path('admin/service/new/', views.edit_service, name='new_service'),
    path('admin/service/<int:service_id>/edit/', views.edit_service, name='edit_service'),
    path('admin/reports/', views.generate_reports, name='generate_reports'),
    path('admin/report/<int:report_id>/update/', views.update_test_results, name='update_test_results'),
]