from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Order creation
    path('create-order/', views.create_order, name='create_order'),
    
    # Payment verification
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    
    # Subscription management
    path('subscription/status/', views.subscription_status, name='subscription_status'),
    path('subscription/config/', views.subscription_config, name='subscription_config'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    
    # Payment history
    path('history/', views.payment_history, name='payment_history'),
]