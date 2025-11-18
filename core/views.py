from django.shortcuts import render, redirect, get_object_or_404
import logging
from django.utils import timezone
from .forms import CompanyForm, DepartmentForm, AffiliateForm, SubAffiliateForm, EmployeeForm
from .models import Company, Department, Affiliate, SubAffiliate, Employee
from .tables import CompanyTable, DepartmentTable, AffiliateTable, SubAffiliateTable, EmployeeTable
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django_tables2 import RequestConfig 
# from django.http import JsonResponse
# from django.contrib.auth import authenticate, login
# from django.contrib import messages


logger = logging.getLogger('main')


# Function that handles the sidebar toggle and state
def toggle_sidebar(request):
    if request.method == "POST":
        collapsed = request.POST.get("collapsed") == "true"
        request.session["sidebarCollapsed"] = collapsed
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)


# Logger initiation Function:
def log_action(action, model, object_id=None):
    timestamp = timezone.now()
    message = f"{timestamp} - Performed {action} on {model.__name__} (ID: {object_id})"
    logger.info(message)


# Function to gather Core Model, Form, Table Classes and Arabic Names based on the model_name
def get_core_models(model_name=None):

    model_mapping = {
        'company': Company,
        'department': Department,
        'affiliate': Affiliate,
        'sub_affiliate': SubAffiliate,
        'employee': Employee,
    }

    form_mapping = {
        'company': CompanyForm,
        'department': DepartmentForm,
        'affiliate': AffiliateForm,
        'sub_affiliate': SubAffiliateForm,
        'employee': EmployeeForm,
    }

    table_mapping = {
        'company': CompanyTable,
        'department': DepartmentTable,
        'affiliate': AffiliateTable,
        'sub_affiliate': SubAffiliateTable,
        'employee': EmployeeTable,
    }

    if model_name:
        model_class = model_mapping.get(model_name.lower())
        form_class = form_mapping.get(model_name.lower())
        table_class = table_mapping.get(model_name.lower())
        if not model_class:
        # Return None if model_name is not recognized
            return None, None
    else:
        # Return all models and forms if model_name is not provided
        return list(model_mapping.values()), None
    
    ar_name = model_class._meta.verbose_name
    ar_names = model_class._meta.verbose_name_plural

    return model_class, form_class, table_class, ar_name, ar_names


# Index view
def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        return render(request, 'base.html')
    

# Manage sections view
@login_required
def manage_sections(request, model_name):
    model_class, form_class, table_class, ar_name, ar_names = get_core_models(model_name)

    # Validate the model_class
    if not model_class or not form_class or not table_class:
        return render(request, 'manage_sections.html', {
            'model_name': model_name,
            'error': 'هناك خطأ في اسم المودل.',
        })

    # Handle document editing
    document_id = request.GET.get('id')
    instance = None
    if document_id:
        instance = get_object_or_404(model_class, id=document_id)

    form = form_class(request.POST or None, instance=instance)
    edited = True if document_id else False
    in_name = instance.name if instance else None

    # Handle form submission
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('manage_sections', model_name=model_name)

    # Fetch objects and create the table
    objects = model_class.objects.all()
    table = table_class(objects, model_name=model_name)  # Ensure model_name is passed here
    RequestConfig(request, paginate={'per_page': 10}).configure(table)

    return render(request, 'manage_sections.html', {
        'model_name': model_name,
        'form': form,
        'table': table,
        'edited': edited,
        'ar_name': ar_name,
        'ar_names': ar_names,
        'id': in_name,
    })

@login_required
def sub_affiliate_view(request, affiliate_id, sub_id=None):
    # Fetch the affiliate and its sub-affiliates
    affiliate = get_object_or_404(Affiliate, id=affiliate_id)
    sub_affiliates = SubAffiliate.objects.filter(affiliate=affiliate)

    sub_id = request.GET.get('id')
    instance = None
    if sub_id:
        instance = get_object_or_404(SubAffiliate, id=sub_id, affiliate=affiliate)
    
    # Prepare the table for sub-affiliates
    table = SubAffiliateTable(sub_affiliates, affiliate_id=affiliate_id)
    form = SubAffiliateForm(request.POST or None, instance=instance, affiliate_id=affiliate_id)
    edited = bool(sub_id)
    in_name = instance.subname if instance else None
    if request.method == 'POST':
        if form.is_valid():
            # Save the form and ensure affiliate linkage
            new_sub = form.save(commit=False)
            new_sub.affiliate = affiliate  # Maintain foreign key relationship
            new_sub.save()
            return redirect('sub_affiliate_view', affiliate_id=affiliate_id)
    
    return render(request, 'manage_sections.html', {
        'model_name': 'sub_affiliate',  # Set a model name for rendering
        'table': table,
        'form': form,
        'ar_name': 'تقسيم اداري بـ' + affiliate.name,  # Dynamic AR name
        'ar_names': 'التقسيمات الادارية بـ' + affiliate.name,
        'edited': edited,
        'id': in_name,
    })


# def clear_login_modal_flag(request):
#     """ Clear the session flag to prevent the modal from showing again. """
#     if request.method == 'POST':  # We expect a POST request to clear the session flag
#         if 'show_login_modal' in request.session:
#             del request.session['show_login_modal']
#         return JsonResponse({'message': 'Login modal flag cleared'})
#     else:
#         return JsonResponse({'message': 'Invalid request method'}, status=405)
