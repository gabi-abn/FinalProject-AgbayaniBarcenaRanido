from django.urls import path
from . import views
 
urlpatterns = [
    path('',                           views.employees,       name='employees'),
    path('employee/create/',           views.create_employee, name='create_employee'),
    path('employee/update/<int:pk>/',  views.update_employee, name='update_employee'),
    path('employee/delete/<int:pk>/',  views.delete_employee, name='delete_employee'),
    path('employee/overtime/<int:pk>/',views.add_overtime,    name='add_overtime'),
    path('payslips/',                  views.payslips,        name='payslips'),
    path('payroll/create/',            views.create_payroll,  name='create_payroll'),
    path('payslip/<int:pk>/',          views.view_payslip,    name='view_payslip'),
]