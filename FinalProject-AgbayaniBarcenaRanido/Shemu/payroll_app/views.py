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
        form = EmployeeForm(request.POST) #EmployeeForm from forms.py; fills the form with submitted data
        if form.is_valid():
            try:
                employee = form.save(commit=False) #creates Employee object but not save to DB yet
                employee.allowance = employee.allowance or 0 #if allowance is empty/None, default it to 0
                employee.overtime_pay = 0 #new employees always start with 0 overtime
                employee.save() #now save the Employee object to the database
                messages.success(request, f'Employee "{employee.name}" created successfully.') #shows a success message on the next page
                return redirect('employees')
            except IntegrityError: #catches a DB error if the id_number already exists
                messages.error(request, 'An employee with that ID number already exists.')
    else:
        form = EmployeeForm() #if it's a GET request, show a blank empty form
    return render(request, 'payroll_app/create_employee.html', {'form': form})


def update_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk) #fetch the Employee with the given pk from DB, return 404 if not found
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee) #fills the form with submitted data, tied to the existing employee record
        if form.is_valid(): #validates submitted data based on rules in forms.py
            try:
                updated = form.save(commit=False) #creates updated Employee object but does not save to DB yet
                updated.allowance = updated.allowance or 0 #if allowance is empty/None, default to 0
                updated.save() #now save the updated Employee object to DB
                messages.success(request, f'Employee "{updated.name}" updated successfully.') #shows success message on next page
                return redirect('employees')
            except IntegrityError: #catches DB error
                messages.error(request, 'An employee with that ID number already exists.')
    else:
        form = EmployeeForm(instance=employee) #if GET request, pre-fill the form with existing Employee details
    return render(request, 'payroll_app/update_employee.html', {'form': form, 'employee': employee})


def delete_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk) #fetch Employee with the given pk, return 404 if not found
    name = employee.name #stores employee's name in a variable before deleting, since we can't access it after deletion
    employee.delete() #permanently delete Employee's record from DB
    messages.success(request, f'Employee "{name}" has been deleted.') #shows success message using saved name variable
    return redirect('employees')


def add_overtime(request, pk):
    if request.method == 'POST':
        employee = get_object_or_404(Employee, pk=pk) 
        try:
            overtime_hours = float(request.POST.get('overtime_hours', 0)) #gets the overtime hours input from the form (in name attribute of input field in employees.html) and converts it to a float; defaults to 0 if empty
        except (ValueError, TypeError): #catches error if input is not a valid number
            messages.error(request, 'Please enter a valid number of overtime hours.')
            return redirect('employees')
        if overtime_hours <= 0: #validates that overtime hours is a positive number
            messages.error(request, 'Overtime hours must be greater than 0.')
            return redirect('employees')
        overtime_earned = (employee.rate / 160) * 1.5 * overtime_hours
        current_overtime = employee.overtime_pay if employee.overtime_pay is not None else 0
        employee.overtime_pay = current_overtime + overtime_earned
        employee.save()
        messages.success(request, f'Added PHP {overtime_earned:.2f} overtime to {employee.name}.')
    return redirect('employees')


def payslips(request):
    all_payslips = Payslip.objects.all().order_by('-pk') #fetches all payslip records from DB, ordered by newest first
    all_employees = Employee.objects.all() #fetches all Employee records
    context = {
        'payslips'  : all_payslips,
        'employees' : all_employees,
    }
    return render(request, 'payroll_app/payslips.html', context)

def create_payroll(request):
    employees = Employee.objects.all() #fetch all Employee records from DB
    payslips = Payslip.objects.all().order_by('-id') #fetch all Payslip records from DB, ordered by newest first

    if request.method == 'POST': # if payroll creation form was submitted
        payroll_for = request.POST.get('payroll_for') # get the selected employee id or 'all' from dropdown
        month_str = request.POST.get('month') # get the selected month
        year_str = request.POST.get('year') # get the typed year
        cycle_str = request.POST.get('cycle') # get the selected cycle (1 or 2)

        if not all([payroll_for, month_str, year_str, cycle_str]): # check if any of the 4 fields are empty
            messages.error(request, "Please fill in all fields.") # show error message
            return render(request, 'payroll_app/payslips.html', { # re-render payslip page with error message
                'employees': employees,
                'payslips': payslips,
            })

        month = int(month_str) # convert month string to integer for calculations 
        year = int(year_str) 
        cycle = int(cycle_str)

        # determine which employees to process
        if payroll_for == 'all':
            targets = Employee.objects.all()
        else:
            targets = Employee.objects.filter(id=payroll_for)

        # date range label
        month_name = calendar.month_name[month]
        if cycle == 1:
            date_range = f"{month_name} 1-15, {year}" # cycle 1 always covers the first half of the month
        else:
            last_day = calendar.monthrange(year, month)[1] # gets the last day of the given month (accounts for leap years)
            date_range = f"{month_name} 16-{last_day}, {year}" # cycle 2 covers the second half of the month

        for e in targets: # loops through each employee to be processed
            if Payslip.objects.filter(employee_id_number=e, month=month, year=year, pay_cycle=cycle).exists(): # checks if a payslip already exists for this employee, month, year, cycle
                messages.error(request, f"Payslip for {e.id_number} (Cycle {cycle}) already exists.") # show error message if duplicate payslip is found
                continue

            overtime = e.overtime_pay or 0
            base = e.rate / 2
            allowance = e.allowance or 0

            if cycle == 1: # cycle 1 only deducts pagibig flat 100
                pagibig = 100
                sss = 0
                health = 0
                tax = (base + allowance + overtime - pagibig) * 0.2
                total_pay = (base + allowance + overtime - pagibig) - tax
            else:
                pagibig = 0
                health = e.rate * 0.04
                sss = e.rate * 0.045
                tax = (base + allowance + overtime - health - sss) * 0.2
                total_pay = (base + allowance + overtime - health - sss) - tax

            Payslip.objects.create( # creates and saves a new Payslip record in DB 
                employee_id_number=e,
                month=month,
                year=year,
                pay_cycle=cycle,
                date_range=date_range,
                rate=e.rate,
                earnings_allowance=allowance,
                overtime=overtime,
                deductions_tax=round(tax, 2),
                deductions_health=round(health, 2),
                pag_ibig=pagibig,
                sss=round(sss, 2),
                total_pay=round(total_pay, 2),
            )

            e.overtime_pay = 0 # reset employee's overtime pay to 0 after payslip generation
            e.save() # save the reset overtime back to DB

        return render(request, 'payroll_app/payslips.html', {
            'employees': employees, 'payslips': payslips,
        })
            
def view_payslip(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk) # fetch the Payslip with the given pk from DB, return 404 if not found
    gross_pay = (payslip.rate / 2) + payslip.earnings_allowance + payslip.overtime
    return render(request, 'payroll_app/view_payslip.html', {
        'payslip': payslip,
        'gross_pay': gross_pay,
    })