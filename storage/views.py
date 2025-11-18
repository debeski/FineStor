#############################################################################
# Main Libraries
#############################################################################
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django_tables2 import RequestConfig 
from django.contrib.auth.decorators import login_required
from .models import Asset, AssetCategory, ImportRecord, ImportItem, ExportRecord, ExportItem, Committee
from .tables import AssetTable, AssetCategoryTable, ImportRecordTable, ExportRecordTable, InventoryReportTable, ExportReturnTable
from .forms import AssetForm, AssetCategoryForm, ImportRecordForm, ImportItemForm, ExportRecordForm, ExportItemForm, ReportForm, ReturnRecordForm
from core.models import Employee
from .filters import AssetFilter
from .genpdf import import_record_pdf, export_record_pdf, inventory_pdf
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.db.models import Q
import logging
from datetime import date
import os
import uuid
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, F
from datetime import timedelta
from django.utils import timezone
#############################################################################
logger = logging.getLogger('storage')
#############################################################################
# Asset Management Views
#############################################################################

@login_required
def manage_category(request, category_id=None):
    # Fetch all categories for display in the table
    categories = AssetCategory.objects.all()
    table = AssetCategoryTable(categories)
    RequestConfig(request).configure(table)

    # Handle editing a category
    if category_id:
        category = get_object_or_404(AssetCategory, id=category_id)
        form = AssetCategoryForm(instance=category)
    else:
        form = AssetCategoryForm()

    # Handle form submission for adding or editing
    if request.method == 'POST':
        if category_id:
            form = AssetCategoryForm(request.POST, instance=category)
        else:
            form = AssetCategoryForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('manage_category')

    return render(request, 'assetcats.html', {
        'table': table,
        'form': form,
        'editing': bool(category_id),  # Flag to determine if editing
    })

@login_required
def manage_assets(request):
    # Get all asset types for the tab view
    categories = AssetCategory.objects.all()
    categories_dict = {cat.id: cat.name for cat in categories}

    # Get category and id from query parameters
    category = request.GET.get('category')
    asset_id = request.GET.get('id')

    selected_cat = None
    if category:
        try:
            category = int(category)
            selected_cat = AssetCategory.objects.filter(id=category).first()
        except ValueError:
            pass

    asset = None
    if asset_id:
        try:
            asset_id = int(asset_id)
            asset = Asset.objects.filter(id=asset_id).first()
        except ValueError:
            pass

    # Handle form submission
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset, selected_cat=selected_cat)
        if form.is_valid():
            form.save()
            # Redirect to clear the form and stay on the same tab
            return redirect(f"{request.path}?category={selected_cat.id if selected_cat else ''}")
        else:
            print(form.errors)  # Debugging: Print form errors to the console
    else:
        form = AssetForm(instance=asset, selected_cat=selected_cat)


    # Check if a category was selected; otherwise, show all assets
    if selected_cat:
        assets = Asset.objects.filter(category=selected_cat)
    else:
        assets = Asset.objects.all()  # Show all assets by default

    asset_filter = AssetFilter(request.GET, queryset=assets)

    # Create the table
    table = AssetTable(asset_filter.qs)
    RequestConfig(request).configure(table)

    # Render the page with the table and tabs
    return render(request, 'assets.html', {
        'categories': categories_dict,
        'selected_cat': selected_cat,
        'table': table,
        'form': form,
        'ar_name': Asset._meta.verbose_name,
        'ar_names': Asset._meta.verbose_name_plural,
        'editing': bool(asset_id),  # Flag to determine if editing
        'filter': asset_filter,  # Pass the filter to the template
    })

#############################################################################
# Import Records Views
#############################################################################

@login_required
def import_records(request):
    # Clear any residual session data
    if 'import_items' in request.session:
        del request.session['import_items']

    query = Q()
    trans_id = request.GET.get('trans_id', '')
    items_or_company = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Apply filters based on user input
    if trans_id:
        query &= Q(trans_id__icontains=trans_id) | Q(assign_number__icontains=trans_id)
    if items_or_company:
        # Adjusting the filters to reference the related fields correctly
        query &= (
            Q(items__name__icontains=items_or_company) |  # Assuming items has a name field
            Q(company__name__icontains=items_or_company) |  # Assuming company is also a ForeignKey with a name field
            Q(assign_number__icontains=items_or_company)
        )

    if start_date and end_date:
        query &= Q(date__range=[start_date, end_date])
    elif start_date:
        query &= Q(date__gte=start_date)
    elif end_date:
        query &= Q(date__lte=end_date)

    # Fetch all ImportRecord entries
    records = ImportRecord.objects.filter(query).distinct().order_by('-date')
    table = ImportRecordTable(records)
    RequestConfig(request, paginate={'per_page': 10}).configure(table)

    return render(request, 'import.html', {'table': table})

@login_required
def import_create(request):
    import_record_instance = None
    import_record_form = ImportRecordForm(request.POST or None, instance=import_record_instance)
    import_item_form = ImportItemForm()

    # Handle both form submissions and Cancel action
    if request.method == 'POST':

        # Finalize the import record submission
        if 'submit_record' in request.POST:
            print("Submitting import record form...")
            import_items = request.session.get('import_items', {})

            if not import_items:
                import_record_form.add_error(None, "يرجى اضافة صنف واحد على الاقل قبل محاولة حفظ الاذن.")

            if import_record_form.is_valid() and import_items:
                import_record = import_record_form.save()
                print("ImportRecord created successfully.")

                # Save all items from the session to the ImportItem Table in DB
                for asset_id, item_data in import_items.items():
                    print(f"Creating ImportItem with asset_id: {asset_id}, price and quantity: {item_data}")
                    asset = Asset.objects.get(id=asset_id)
                    asset.add_price(item_data['price'])
                    asset.stock += int(item_data['quantity'])
                    asset.save()
                    ImportItem.objects.create(
                        record=import_record,
                        asset_id=asset_id,
                        quantity=item_data['quantity'],
                        price=item_data['price']
                    )
                # Clear session data after submission
                if 'import_items' in request.session:
                    del request.session['import_items']
                print("Cleared import items from session data after record creation.")

                # Redirect to success or summary page
                messages.success(
                    request,
                    mark_safe(f'تم اضافة اذن استلام رقم: {import_record.trans_id} بنجاح. '
                              f'<a href="{reverse("gen_pdf", kwargs={"model": "import", "trans_id": import_record.trans_id})}" target="_blank">طباعة اذن الاستلام</a>')
                )
                return redirect('import_records')
            else:
                print("Import record form is invalid.")
                print(f"Form errors: {import_record_form.errors}")

    # Prepare items with asset names for display
    import_items = []
    for asset_id, item_data  in request.session.get('import_items', {}).items():
        asset = Asset.objects.get(id=asset_id)
        import_items.append({
            'id': asset_id,
            'name': asset.name,
            'quantity': item_data['quantity'],
            'unit': asset.get_unit_display(),
            'price': item_data['price'],
            'total': float(item_data['price']) * int(item_data['quantity']),
        })

    print(f"Rendering template with import_items: {import_items}")
    return render(request, 'invoice.html', {
        'import_record_form': import_record_form,
        'import_item_form': import_item_form,
        'import_items': import_items,
    })

@login_required
def import_item_add(request):

    # Asset fields for the ImportItemForm
    asset_id = request.GET.get('asset')
    quantity = request.GET.get('quantity')
    price = request.GET.get('price')

    if asset_id and price and quantity:
        items = request.session.get('import_items', {})
        items[asset_id] = {
            'quantity': quantity,
            'price': price,
        }
        request.session['import_items'] = items
        print(f"Added item to session: {asset_id} -> {quantity} -> {price}")
    else:
        print("Asset ID or price or quantity missing.")
        print(f"requested:  {asset_id} -> {quantity} -> {price}")

    # Redirect back to the form page
    return redirect('import_create')

@login_required
def import_item_delete(request, asset_id):

    # Convert asset_id to string to match the session keys
    asset_id = str(asset_id)

    # Check if the item exists in the session
    items = request.session.get('import_items', {})
    if asset_id in items:
        del items[asset_id]  # Remove the item
        request.session['import_items'] = items  # Update the session
        print(f"Item with asset_id {asset_id} removed successfully!")
    else:
        print(f"Item with asset_id {asset_id} not found in the session!")

    # Redirect back to the import_create page
    return redirect('import_create')


def fetch_import_record_data(trans_id):
    # Fetch the import record based on trans_id
    import_record = get_object_or_404(ImportRecord, trans_id=trans_id)
    # Prepare the record details
    record_info = {
        'trans_id': import_record.trans_id,
        'date': import_record.date.strftime("%d-%m-%Y") if import_record.date else "N/A",
        'company': import_record.company.name if import_record.company else "N/A",
        'phone': import_record.company.phone if import_record.company else "N/A",
        'address': import_record.company.address if import_record.company else "N/A",
        'assign_id': import_record.assign_number or "N/A",
        'assign_date': import_record.assign_date.strftime("%d-%m-%Y") if import_record.assign_date else "N/A",
        'notes': import_record.notes or "N/A",
    }

    # Fetch related items
    items = ImportItem.objects.filter(record=import_record)
    item_details = []
    for item in items:
        item_details.append({
            'name': str(item.asset.name),
            'brand': str(item.asset.brand+' '+item.asset.brand_en),
            'quantity': item.quantity,
            'unit': str(item.asset.get_unit_display()),  # Fetch unit display from asset
            'price': item.price,
            'total_price': item.price * item.quantity,
        })

    record_info['items'] = item_details
    print(f'fetched record info for Import Record No {trans_id} successfully')
    return record_info

@login_required
def import_details(request, trans_id):
    # Fetch data for the record by trans_id
    record_info = fetch_import_record_data(trans_id)
    grand_total = sum([item['total_price'] for item in record_info['items']])
    context = {
        'record': record_info,
        'grand_total': grand_total,
    }
    return render(request, 'import_details.html', context)

#############################################################################
# Shared Views
#############################################################################

@login_required
def get_assets(request, category_id):
    assets = Asset.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse({'assets': list(assets)})

@login_required
def get_ex_assets(request, category_id):
    assets = Asset.objects.filter(category_id=category_id, stock__gt=0).values('id', 'name')
    return JsonResponse({'assets': list(assets)})


@login_required
def gen_pdf(request, model, trans_id):
    if model == 'import':
        record_info = fetch_import_record_data(trans_id)
        pdf_data = import_record_pdf(trans_id, record_info)
    elif model == 'export':
        record_info = fetch_export_record_data(trans_id)
        pdf_data = export_record_pdf(trans_id, record_info)
    else:
        return HttpResponse("Invalid model type", status=400)

    # Return the PDF as an HTTP response
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{model}_record_{trans_id}.pdf"'

    return response


def content_type_search(search_term, relevant_types):
    """
    Function to dynamically build a query for searching across related models using GenericForeignKey.

    Args:
        search_term (str): The search term to be used for filtering related models.
        relevant_types (list): List of relevant content type model names (like 'department', 'subaffiliate', 'employee').

    Returns:
        Q: A Django Q object containing the built search queries for `GenericForeignKey`.
    """
    # Create a Q object for searching across all related models
    search_queries = Q()
    
    # Get all ContentTypes related to the relevant models
    content_types = ContentType.objects.filter(model__in=relevant_types)
    
    # Loop over content types and dynamically build search queries
    for content_type in content_types:
        model_class = content_type.model_class()  # Get the model class from content type
        print(f"Processing content type: {content_type.model}")

        # Check if the model has the 'name' or 'subname' field for searching
        if model_class and hasattr(model_class, 'name'):
            related_ids = model_class.objects.filter(name__icontains=search_term).values_list('id', flat=True)
        elif model_class and hasattr(model_class, 'subname'):  # For SubAffiliate
            related_ids = model_class.objects.filter(subname__icontains=search_term).values_list('id', flat=True)
        
        # Dynamically build the query for each model type based on entity_selection and entity_type
        search_queries |= Q(entity_type=content_type) & Q(entity_id__in=related_ids)

    return search_queries

#############################################################################
# Export Records Views
#############################################################################

@login_required
def export_records(request):
    if 'export_items' in request.session:
        del request.session['export_items']
    # Fetch export types (e.g., from a database model)
    export_types = ExportRecord._meta.get_field('export_type').choices
    export_types_dict = {choice[0]: choice[1] for choice in export_types}

    # Get the selected export type from query parameters
    selected_export_type = request.GET.get('export_type')
    relevant_types = ['department', 'subaffiliate', 'employee']  # Add your model names here

    
    # Generate tables for each export type
    export_tables = {}
    combined_records = ExportRecord.objects.none()  # Empty queryset to start with

    for export_type_value, export_type_label in export_types:
        query = Q(export_type=export_type_value)

        if request.GET.get('trans_id'):
            query &= Q(trans_id__icontains=request.GET['trans_id'])

        # Check if there is a search term
        if request.GET.get('search'):
            search_term = request.GET.get('search', '')
            # Call the reusable function to build the search query
            search_queries = content_type_search(search_term, relevant_types)
            other_fields = Q(items__name__icontains=search_term)
            query &= (search_queries | other_fields)

        if request.GET.get('start_date') and request.GET.get('end_date'):
            query &= Q(date__range=[request.GET['start_date'], request.GET['end_date']])
        elif request.GET.get('start_date'):
            query &= Q(date__gte=request.GET['start_date'])
        elif request.GET.get('end_date'):
            query &= Q(date__lte=request.GET['end_date'])

        records = ExportRecord.objects.filter(query).distinct()

        # Only add the table if the export type matches the selected type or if no type is selected
        if selected_export_type is None:
            combined_records = combined_records | records  # Add to the combined queryset
        elif selected_export_type == export_type_value:
            table = ExportRecordTable(records)
            RequestConfig(request, paginate={'per_page': 10}).configure(table)
            export_tables[export_type_label] = table

    # If no specific type is selected, create a single table for all records
    if selected_export_type is None:
        all_table = ExportRecordTable(combined_records)
        RequestConfig(request, paginate={'per_page': 10}).configure(all_table)
        export_tables['None'] = all_table

    return render(request, 'export.html', {
        'export_types': export_types_dict,
        'export_tables': export_tables,
        'export_type': selected_export_type,  # Pass the selected export type to the template
    })

@login_required
def export_create(request, export_type=None):
    print(f"Entered export_create with export_type: {export_type}")

    # Initialize the export record and forms
    export_record_instance = None
    export_record_form = ExportRecordForm(request.POST or None, instance=export_record_instance, export_type=export_type)
    export_item_form = ExportItemForm()
    export_types = ExportRecord._meta.get_field('export_type').choices
    export_types_dict = {choice[0]: choice[1] for choice in export_types}

    # Define valid export types from the ExportRecord model choices
    valid_export_types = [choice[0] for choice in ExportRecord.export_type.field.choices]

    # Redirect to the first valid export type if export_type is None
    if export_type is None or export_type not in valid_export_types:
        print(f"Invalid or missing export_type: {export_type}. Redirecting to the first valid export type...")
        first_export_type = valid_export_types[0]  # Default to the first export type
        return redirect('export_create', export_type=first_export_type)
    
    # Handle form submission
    if request.method == 'POST':
        # Finalize the export record submission
        if 'submit_record' in request.POST:
            print(f"Submitting export record form for {export_type}...")

            export_items = request.session.get('export_items', {})
            print(f"Export items from session: {export_items}")

            if not export_items:
                print("No export items found in session.")
                export_record_form.add_error(None, "يرجى اضافة صنف واحد على الاقل قبل محاولة حفظ الاذن.")
            
            if export_record_form.is_valid() and export_items:
                export_record = export_record_form.save(commit=False)
                export_record.export_type = export_type  # Associate the export type with the record
                export_record.save()
                print(f"ExportRecord created successfully with trans_id: {export_record.trans_id}")

                # Save all items from the session to the ExportItem Table in DB
                for item_id, item_data in export_items.items():
                    print(f"Creating ExportItem with asset_id: {item_id}, price: {item_data['price']}, quantity: {item_data['quantity']}")
                    asset = Asset.objects.get(id=item_data['asset_id'])
                    asset.stock -= int(item_data['quantity'])
                    asset.save()
                    ExportItem.objects.create(
                        record=export_record,
                        asset_id=item_data['asset_id'],
                        quantity=item_data['quantity'],
                    )

                # Clear session data after submission
                if 'export_items' in request.session:
                    del request.session['export_items']
                print("Cleared export items from session data after record creation.")

                # Redirect to success or summary page
                success_msg = f'تم اضافة اذن تصدير رقم: {export_record.trans_id} بنجاح. ' \
                              f'<a href="{reverse("gen_pdf", kwargs={"model": "export", "trans_id": export_record.trans_id})}" target="_blank">طباعة اذن التصدير</a>'
                print(f"Success message: {success_msg}")
                messages.success(request, mark_safe(success_msg))
                return redirect('export_records')
            else:
                print("Export record form is invalid.")
                print(f"Form errors: {export_record_form.errors}")

    # Prepare items with asset names for display
    export_items = []
    for item_id, item_data in request.session.get('export_items', {}).items():
        asset = Asset.objects.get(id=item_data['asset_id'])
        export_items.append({
            'id': item_id,
            'name': asset.name,
            'quantity': item_data['quantity'],
            'unit': asset.get_unit_display(),
            'price': item_data['price'],
            'total': float(item_data['price']) * int(item_data['quantity']),
        })

    print(f"Rendering template with export_items: {export_items}")
    return render(request, 'xinvoice.html', {
        'export_record_form': export_record_form,
        'export_item_form': export_item_form,
        'export_items': export_items,
        'export_type': export_type,
        'export_types': export_types_dict,
    })

@login_required
def export_item_add(request, export_type):
    # Asset fields for the ExportItemForm
    asset_id = request.GET.get('asset')
    quantity = request.GET.get('quantity')

    # Fetch asset details
    if asset_id:
        try:
            asset = Asset.objects.get(id=asset_id)
            price = asset.average_price()  # Use the average price from the Asset model
        except Asset.DoesNotExist:
            print(f"Asset with ID {asset_id} does not exist.")
            return redirect('export_create', export_type=export_type)
    else:
        print("Asset ID is missing.")
        return redirect('export_create', export_type=export_type)

    if price is None:
        print(f"Asset with ID {asset_id} does not have an average price.")
        return redirect('export_create', export_type=export_type)

    if quantity:
        
        # Retrieve existing items or initialize
        items = request.session.get('export_items', {})
        item_id = max([int(key) for key in items.keys()], default=0) + 1
        # Add the new item with a unique ID
        items[item_id] = {
            'asset_id': asset_id,
            'quantity': quantity,
            'price': str(price),
        }
        
        # Save back to session
        request.session['export_items'] = items
        print(f"Added item to session: {item_id} -> {asset_id} -> {quantity} -> {price}")
    else:
        print("Quantity is missing.")
        print(f"Requested: {asset_id} -> {quantity} -> {price}")

    # Redirect back to the form page
    return redirect('export_create', export_type=export_type)

@login_required
def export_item_delete(request, export_type, item_id):
    # Check if the item exists in the session
    items = request.session.get('export_items', {})
    if item_id in items:
        del items[item_id]  # Remove the item
        request.session['export_items'] = items  # Update the session
        print(f"Item with ID {item_id} removed successfully!")
    else:
        print(f"Item with ID {item_id} not found in the session!")

    # Redirect back to the export_create page
    return redirect('export_create', export_type=export_type)


def fetch_export_record_data(trans_id):
    # Fetch the import record based on trans_id
    export_record = get_object_or_404(ExportRecord, trans_id=trans_id)
    # Prepare the record details
    record_info = {
        'trans_id': export_record.trans_id,
        'date': export_record.date.strftime("%d-%m-%Y") if export_record.date else "N/A",
        'entity': export_record.entity_selection.name if export_record.entity_selection else "N/A",
        'notes': export_record.notes or "N/A",
        'export_type': export_record.get_export_type_display(),
        'xp_type': export_record.export_type
    }

    # Fetch related items
    items = ExportItem.objects.filter(record=export_record)
    item_details = []
    for item in items:
        item_details.append({
            'id': item.id,
            'name': str(item.asset.name),
            'brand': str(item.asset.brand+' '+item.asset.brand_en),
            'quantity': item.quantity,
            'unit': str(item.asset.get_unit_display()),  # Fetch unit display from asset
            'price': item.asset.average_price(),
            'total_price': item.asset.average_price() * item.quantity,
        })

    record_info['items'] = item_details
    print(f'fetched record info for Export Record No {trans_id} successfully')
    return record_info

@login_required
def export_details(request, trans_id):
    # Fetch data for the record by trans_id
    record_info = fetch_export_record_data(trans_id)
    grand_total = sum([item['total_price'] for item in record_info['items']])
    context = {
        'record': record_info,
        'grand_total': grand_total,
    }
    return render(request, 'export_details.html', context)

# @login_required
# def export_return(request, trans_id):
#     # Fetch the export record by trans_id
#     record_info = fetch_export_record_data(trans_id)
#     form = ReturnExportForm(request.POST or None)
#     # Create a list to hold selected items for return
#     selected_items = []

#     if request.method == 'POST':
#         # Step 1: User submits selected items
#         if 'item_ids' in request.POST and 'return_purpose' not in request.POST:
#             # Get selected item IDs from the POST data
#             selected_items_ids = request.POST.getlist('item_ids')
#             print(f"Selected items for return: {selected_items_ids}")
#             # Fetch the selected items
#             selected_items = ExportItem.objects.filter(id__in=selected_items_ids)
#         # Step 2: User submits return fields
#         elif 'return_purpose' in request.POST:
#             # Iterate over selected items and update their fields
#             selected_items_ids = request.POST.getlist('item_ids')
#             print(f"Processing returns for items: {selected_items_ids}")

#             for item_id in selected_items_ids:
#                 try:
#                     item = ExportItem.objects.get(id=item_id)
#                     # Update return fields from the form
#                     item.return_purpose = request.POST.get('return_purpose')
#                     item.return_condition = request.POST.get('return_condition')
#                     item.return_at = request.POST.get('return_at')
#                     item.save()
#                 except ExportItem.DoesNotExist:
#                     print(f"Selected Item with ID {item_id} does not exist.")
#                     continue

#             # Redirect to the export details page after saving
#             return redirect('export_details', trans_id=trans_id)

#     context = {
#         'record': record_info,
#         'selected_items': selected_items,
#         'form': form,
#     }
#     return render(request, 'return.html', context)

#############################################################################
# Return Views
#############################################################################

@login_required
def return_records(request):
    
    # Define the return types
    return_types_dict = {
        'export': 'اذونات الصرف',
        'import': 'اذونات الاستلام',
    }

    # Get the selected return type (default to 'asset')
    selected_type = request.GET.get('return_type', 'export')
    
    # Apply filtering conditions
    query = Q(return_at__isnull=False)  # Only include records with a return_at value
    trans_id = request.GET.get('trans_id', '')
    asset_name = request.GET.get('asset_name', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Filter by transaction ID
    if trans_id:
        query &= Q(record__trans_id__icontains=trans_id)

    # Filter by asset name
    if asset_name:
        query &= Q(asset__name__icontains=asset_name)

    # Filter by date range
    if start_date and end_date:
        query &= Q(return_at__range=[start_date, end_date])
    elif start_date:
        query &= Q(return_at__gte=start_date)
    elif end_date:
        query &= Q(return_at__lte=end_date)

    # Fetch the filtered ExportItem records
    returned_items = ExportItem.objects.filter(query).distinct().order_by('-return_at')
    table = ExportReturnTable(returned_items)
    RequestConfig(request, paginate={'per_page': 10}).configure(table)

    return render(request, 'returns.html', {
        'table': table,
        'return_types': return_types_dict,
        'selected_type': selected_type,
        })

@login_required
def return_create(request, return_type=None):
    return_record_instance = None
    return_record_form = ReturnRecordForm(request.POST or None, instance=return_record_instance, return_type=return_type)
    return_item_form = ReturnItemForm()
    return_types_dict = {
        'export': 'اذونات الصرف',
        'import': 'اذونات الاستلام',
    }
    
    # Get the last used return_id across both ExportItem and ImportItem
    last_export_return_id = ExportItem.objects.filter(return_at__isnull=False).order_by('-return_id').first()
    last_import_return_id = ImportItem.objects.filter(return_at__isnull=False).order_by('-return_id').first()

    last_return_id = max(
        last_export_return_id.return_id if last_export_return_id else 0,
        last_import_return_id.return_id if last_import_return_id else 0
    )
    
    new_return_id = last_return_id + 1  # Increment the return_id for the new return record

    # Handle form submission
    if request.method == 'POST' and return_type in ['export', 'import']:
        if 'submit_record' in request.POST:
            print(f"Submitting return record form for {return_type}...")

            return_items = request.session.get('return_items', {})
            print(f"Return items from session: {return_items}")

            if not return_items:
                print("No return items found in session.")
                return_record_form.add_error(None, "يرجى اضافة صنف واحد على الاقل قبل محاولة حفظ الاذن.")

            if return_record_form.is_valid() and return_items:
                return_record = return_record_form.save(commit=False)
                return_record.return_type = return_type
                return_record.return_id = new_return_id  # Set the new return_id
                return_record.save()
                print(f"ReturnRecord created successfully with trans_id: {return_record.trans_id}")

                # Dynamically choose the model (ExportItem or ImportItem)
                model = ExportItem if return_type == 'export' else ImportItem
                
                # Save return items to the database
                for item_id, item_data in return_items.items():
                    model = ExportItem if return_type == 'export' else ImportItem
                    print(f"Updating {model.__name__} with ID {item_id}, marking it as returned.")
                    item = model.objects.get(id=item_id)
                    item.return_at = timezone.now()
                    item.return_purpose = item_data['purpose']
                    item.return_condition = item_data['condition']
                    item.return_id = new_return_id  # Assign the same return_id to the returned items
                    item.save()

                # Clear session data after submission
                if 'return_items' in request.session:
                    del request.session['return_items']
                print("Cleared return items from session data after record creation.")

                # Redirect with success message
                success_msg = f'تم اضافة اذن ارجاع رقم: {return_record.trans_id} بنجاح.'
                print(f"Success message: {success_msg}")
                messages.success(request, mark_safe(success_msg))
                return redirect('return_records')

    # Prepare return items for display
    return_items = []
    model = ExportItem if return_type == 'export' else ImportItem
    for item_id, item_data in request.session.get('return_items', {}).items():
        try:
            item = model.objects.get(id=item_id)
            return_items.append({
                'id': item_id,
                'name': item.asset.name,
                'quantity': item.quantity,
                'purpose': item_data['purpose'],
                'condition': item_data['condition'],
            })
        except model.DoesNotExist:
            print(f"{model.__name__} with ID {item_id} does not exist, skipping.")

    print(f"Rendering template with return_items: {return_items}")
    return render(request, 'return_create.html', {
        'return_record_form': return_record_form,
        'return_item_form': return_item_form,
        'return_items': return_items,
        'return_type': return_type,
        'return_types': return_types_dict,
    })


@login_required
def return_item_add(request, return_type):
    item_id = request.GET.get('item_id')
    purpose = request.GET.get('purpose')
    condition = request.GET.get('condition')

    if not item_id:
        print("Item ID is missing.")
        return redirect('return_create', return_type=return_type)

    try:
        export_item = ExportItem.objects.get(id=item_id)
    except ExportItem.DoesNotExist:
        print(f"ExportItem with ID {item_id} does not exist.")
        return redirect('return_create', return_type=return_type)

    # Update session data with the new return item
    items = request.session.get('return_items', {})
    items[item_id] = {
        'purpose': purpose or "N/A",
        'condition': condition or "N/A",
    }
    request.session['return_items'] = items
    print(f"Added return item to session: {item_id} -> {items[item_id]}")

    return redirect('return_create', return_type=return_type)

@login_required
def return_item_delete(request, return_type, item_id):
    items = request.session.get('return_items', {})
    if item_id in items:
        del items[item_id]  # Remove the item from session
        request.session['return_items'] = items
        print(f"Removed return item with ID {item_id} from session.")
    else:
        print(f"Return item with ID {item_id} not found in session.")

    return redirect('return_create', return_type=return_type)

#############################################################################
# Report Views
#############################################################################


@login_required
def report_view(request):
    # Get the selected report type from the request (either from URL or session)
    selected_type = request.GET.get('report_type', 'inventory')  # Default to 'inventory' if none selected
    # Initialize the form with the selected report_type if available
    form = ReportForm(request.POST or None)
    # Get the available report types to display as tabs in the template
    report_types_dict = {
        'inventory': 'الجرد العام',
        'department': 'العهد الادارية',
        'personal': 'العهد الشخصية',
        'loan':'الاعارات',
        'cars': 'السيارات',
        'damaged': 'التوالف',
        'consumed': 'المستهلكات'
    }
    # Handle form submissions
    if request.method == 'POST' and 'report_initial' in request.POST:
        year = request.POST.get('year')
        end_date = date(int(year), 12, 31)
        # Handle the initial report generation logic
        if selected_type == "inventory":
            # Generate report data
            report_data = report_inventory(end_date)
            table = InventoryReportTable(report_data)
            request.session['report_data'] = report_data
            # Check if a committee already exists for the selected year
            committee_instance = Committee.objects.filter(year=year).first()
            if committee_instance:
                # Pass the instance to the form for pre-filling
                form = ReportForm(instance=committee_instance)
            else:
                # Create a blank form if no committee exists
                form = ReportForm(initial={'year': year})
            # Render the report view with the form and the table
            return render(request, 'report.html', {
                'form': form,
                'table': table,
                'comm': bool(committee_instance),
                'selected_type': selected_type,
                'year': year,
                'report_types': report_types_dict,  # Pass available report types to the template for tabs
            })
    elif request.method == 'POST' and 'report_confirm' in request.POST:
        # Handle the final confirmation and saving committee members
        year = request.POST.get('year')
        president_id = request.POST.get('president')
        members_id = request.POST.getlist('members')
        # Retrieve report_data from session
        report_data = request.session.get('report_data')
        if not report_data:
            messages.error(request, "No report data available. Please generate the report first.")
            return redirect(request.path)
        # Check if a committee for the selected year already exists
        committee_instance = Committee.objects.filter(year=year).first()
        if committee_instance:
            # If the committee exists, update it
            form = ReportForm(request.POST, instance=committee_instance)
        else:
            # If no committee exists, create a new one
            form = ReportForm(request.POST)
        # Save or update the committee instance
        if form.is_valid():
            form.save()
            messages.success(request, f"Report for {year} was bgenerated successfully.")
            members = Employee.objects.filter(id__in=members_id)
            president = Employee.objects.get(id=president_id)
            final_report_data = {
                "type": "inventory",
                "year": year,
                "president": president.name,
                "members": [member.name for member in members],
                "items": report_data,
            }
            request.session['final_report_data'] = final_report_data
            print('Storage Report Successfully Generated.')
            # Redirect or add a success message
            return redirect(report_pdf)  # Reload the page
        else:
            messages.error(request, "Please fill out the form correctly.")
    # If form is not yet submitted or invalid, just render the initial form
    return render(request, 'report.html', {
        'form': form,
        'report_types': report_types_dict,  # Pass report types for tab navigation
        'selected_type': selected_type,  # Keep track of selected report type
    })


def report_inventory(end_date):
    # Initialize an empty list to store asset data
    assets_data = []

    # Fetch all assets
    assets = Asset.objects.all()

    for asset in assets:
        # Initialize the asset data dictionary
        asset_data = {
            'id': asset.id,
            'category': asset.category.name,
            'name': asset.name,
            'brand': f"{asset.brand} {asset.brand_en}",  # Combine brand and brand_en
            'unit': asset.unit,
            'stock': asset.stock,
            'average_price': asset.average_price(),  # Apply the average_price method
            'net_quantity': 0,  # Will be calculated
            'differences': [],  # To store differences over time
        }

        # Fetch related import records with date filtering
        import_items = ImportItem.objects.filter(asset=asset, record__date__lte=end_date).select_related('record')
        export_items = ExportItem.objects.filter(asset=asset, record__date__lte=end_date).select_related('record')

        # Combine imports and exports into a timeline
        timeline = []

        for import_item in import_items:
            timeline.append({
                'type': 'import',
                'date': import_item.record.date.strftime('%Y-%m-%d'),  # Convert date to string
                'quantity': import_item.quantity,
            })
        for export_item in export_items:
            timeline.append({
                'type': 'export',
                'date': export_item.record.date.strftime('%Y-%m-%d'),  # Convert date to string
                'quantity': export_item.quantity,
            })
        # Sort the timeline by date
        timeline.sort(key=lambda x: x['date'])

        # Calculate differences over time
        running_total = 0
        for entry in timeline:
            if entry['type'] == 'import':
                running_total += entry['quantity']
            elif entry['type'] == 'export':
                running_total -= entry['quantity']
            # Record the difference at each step
            asset_data['differences'].append({
                'date': entry['date'],
                'type': entry['type'],
                'quantity': entry['quantity'],
                'running_total': running_total,
            })

        # Calculate total imports, exports, and net quantity
        total_imports = sum(item.quantity for item in import_items)
        total_exports = sum(item.quantity for item in export_items)
        asset_data['net_quantity'] = total_imports - total_exports

        # Add the asset data to the list
        assets_data.append(asset_data)

    sorted_assets_data = sorted(assets_data, key=lambda x: (x['category'], x['id']))

    return sorted_assets_data


@login_required
def report_pdf(request):
    final_report_data = request.session.get('final_report_data')

    if final_report_data['type'] == 'inventory':
        pdf_data = inventory_pdf(final_report_data)

    elif final_report_data['type'] == 'department':
        pdf_data = department_pdf(final_report_data)

    elif final_report_data['type'] == 'personal':
        pdf_data = personal_pdf(final_report_data)

    elif final_report_data['type'] == 'loan':
        pdf_data = loan_pdf(final_report_data)

    elif final_report_data['type'] == 'cars':
        pdf_data = cars_pdf(final_report_data)

    elif final_report_data['type'] == 'damaged':
        pdf_data = damaged_pdf(final_report_data)

    elif final_report_data['type'] == 'consumed':
        pdf_data = consumed_pdf(final_report_data)

    else:
        return HttpResponse("Invalid report type", status=400)

    # Return the PDF as an HTTP response
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f"inline; filename='{final_report_data['type']}_report_{final_report_data['year']}.pdf'"

    return response

