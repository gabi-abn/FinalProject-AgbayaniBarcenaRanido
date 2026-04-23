from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import IntegrityError

from .models import Employee, Payslip
from .forms  import EmployeeForm
import calendar


def employees(request):
    all_employees = Employee.objects.all()
    context = {'employees': all_employees}
    return render(request, 'payroll_app/employees.html', context)


def create_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            try:
                employee = form.save(commit=False)
                employee.allowance = employee.allowance or 0
                employee.overtime_pay = 0
                employee.save()
                messages.success(request, f'Employee "{employee.name}" created successfully.')
                return redirect('employees')
            except IntegrityError:
                messages.error(request, 'An employee with that ID number already exists.')
    else:
        form = EmployeeForm()
    return render(request, 'payroll_app/create_employee.html', {'form': form})


def update_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            try:
                updated = form.save(commit=False)
                updated.allowance = updated.allowance or 0
                updated.save()
                messages.success(request, f'Employee "{updated.name}" updated successfully.')
                return redirect('employees')
            except IntegrityError:
                messages.error(request, 'An employee with that ID number already exists.')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'payroll_app/update_employee.html', {'form': form, 'employee': employee})


def delete_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    name = employee.name
    employee.delete()
    messages.success(request, f'Employee "{name}" has been deleted.')
    return redirect('employees')


def add_overtime(request, pk):
    if request.method == 'POST':
        employee = get_object_or_404(Employee, pk=pk)
        try:
            overtime_hours = float(request.POST.get('overtime_hours', 0))
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid number of overtime hours.')
            return redirect('employees')
        if overtime_hours <= 0:
            messages.error(request, 'Overtime hours must be greater than 0.')
            return redirect('employees')
        overtime_earned = (employee.rate / 160) * 1.5 * overtime_hours
        current_overtime = employee.overtime_pay if employee.overtime_pay is not None else 0
        employee.overtime_pay = current_overtime + overtime_earned
        employee.save()
        messages.success(request, f'Added PHP {overtime_earned:.2f} overtime to {employee.name}.')
    return redirect('employees')


def payslips(request):
    all_payslips = Payslip.objects.all().order_by('-pk')
    all_employees = Employee.objects.all()
    context = {
        'payslips'  : all_payslips,
        'employees' : all_employees,
    }
    return render(request, 'payroll_app/payslips.html', context)


def create_payroll(request):
    employees = Employee.objects.all()
    payslipes = Payslip.objects.all().order_by('-id')

    if request.method == 'POST':
        payroll_for = request.POST.get('payroll_for')
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))
        cycle = int(request.POST.get('cycle'))

        # determine which employees to process
        if payroll_for == 'all':
            targets = employees
        else:
            targets = Employee.objects.filter(id=payroll_for)

        # date range label
        month_name = calendar.month_name[month]
        if cycle == 1:
            date_range = f"{month_name} 1-15, {year}"
        else:
            last_day = calendar.monthrange(year, month)[1]
            date_range = f"{month_name} 16-{last_day}, {year}"

        for e in targets:
            # check if payslip already exists
            if Payslip.objects.filter(employee=e, month=month, year=year, cycle=cycle).exists():
                messages.error(request, f"Payslip for {emp.id_number} (Cycle {cycle}) already exists.")
                continue

            overtime = e.overtime
            base = e.rate / 2
            allowance = e.allowance or 0

            if cycle == 1:
                # pag-ibig flat fee = 100
                pagibig = 100
                tax = (base + allowance + overtime - pagibig) * 0.2
                total_pay = (base + allowance + overtime - pagibig) - tax
            else:
                # philhealth = 4% of rate; SSS = 4.5% of rate
                philhealth = e.rate * 0.04
                sss = e.rate * 0.045
                tax = (base + allowance + overtime - philhealth - sss) * 0.2
                total_pay = (base + allowance + overtime - philhealth - sss) - tax

        Payslip.objects.create(
            employee=e,
            month=month,
            year=year,
            cycle=cycle,
            date_range=date_range,
            total_pay=round(total_pay, 2),
        )

        # reset overtime to 0
        e.overtime = 0
        e.save()

        return redirect('create_payroll')

    return render(request, 'payroll_app/create_payroll.html', {
        'employees': employees,
        'payslips': payslips,
    })