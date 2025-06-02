from django.shortcuts import render, redirect
from .forms import EmployeeLoginForm
from employee.models import Employee
from django.db.models import Count, Sum
from supplier.models import Supplier
from product.models import Product
from inventory.models import Inventory
from order.models import PurchaseOrder
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.functions import TruncDate
from main.decorators import employee_login_required



def get_logged_employee(request):
    emp_id = request.session.get('employee_id')
    if emp_id:
        try:
            return Employee.objects.get(id=emp_id)
        except Employee.DoesNotExist:
            return None
    return None

def employee_login_view(request):
    if request.method == 'POST':
        form = EmployeeLoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            try:
                employee = Employee.objects.get(phone=phone)
                if employee.check_password(password):
                    request.session['employee_id'] = employee.id
                    return redirect('dashboard')
                else:
                    form.add_error(None, "Parol noto‘g‘ri")
            except Employee.DoesNotExist:
                form.add_error('phone', "Bunday telefon raqamli foydalanuvchi topilmadi")
    else:
        form = EmployeeLoginForm()
    return render(request, 'employee_login.html', {'form': form})

def employee_logout_view(request):
    if 'employee_id' in request.session:
        del request.session['employee_id']
    return redirect('login')



def dashboard(request):
    employee = get_logged_employee(request)
    if not employee:
        return redirect('login')

    total_suppliers = Supplier.objects.count()
    total_products = Product.objects.count()
    total_inventory_items = Inventory.objects.count()
    total_orders = PurchaseOrder.objects.count()

# linegraph: orders in the last 7 days
    today    = now().date()
    week_ago = today - timedelta(days=6)

    # 1) Bazadan order_date ro'yxatini oqlaymiz
    dates_qs = (PurchaseOrder.objects
                .filter(order_date__range=(week_ago, today))
                .values_list('order_date', flat=True))
    # 2) Python’da sanaymiz
    date_counts = {}
    for d in dates_qs:
        d_date = d if isinstance(d, type(today)) else d.date()
        date_counts[d_date] = date_counts.get(d_date, 0) + 1

    sparkline_orders = []
    for i in range(7):
        day = week_ago + timedelta(days=i)
        sparkline_orders.append(date_counts.get(day, 0))

    received = PurchaseOrder.objects.aggregate(total_received=Sum('items__quantity_received'))['total_received'] or 0
    ordered = PurchaseOrder.objects.aggregate(total_ordered=Sum('items__quantity_ordered'))['total_ordered'] or 1
    percent_received = int(received / ordered * 100)


    # PIE CHART: product count by supplier
    supplier_counts = Product.objects.values('supplier__name').annotate(count=Count('id'))
    pie_data = ','.join(str(s['count']) for s in supplier_counts) or '0,1,5'

    # DONUT CHART: inventory by quantity level
    full_qty = Inventory.objects.filter(quantity__gt=10).count()
    low_qty = Inventory.objects.filter(quantity__lte=10).count()
    donut_data = f"{full_qty},{low_qty}"

    context = {
        'employee': employee,
        'total_suppliers': total_suppliers,
        'total_products': total_products,
        'total_inventory_items': total_inventory_items,
        'total_orders': total_orders,
        'sparkline_orders': sparkline_orders,
        'percent_received': percent_received,
        'pie_data': pie_data,
        'donut_data': donut_data,
    }
    return render(request, 'dashboard.html', context)