import os
import json
import calendar
from audioop import reverse
from datetime import datetime
from django.conf import settings
from collections import OrderedDict
from django.db.models import Q, Sum, Max, Count
from collections import defaultdict
from django.utils.timezone import now
from django.db.models.functions import ExtractMonth, ExtractYear
from django.db.models.functions import TruncDate
from django.utils.dateparse import parse_date
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db.models.functions import Lower
from django.db import transaction, IntegrityError
from organizations.models import organizationlst
from class_setup.models import in_class
from exam_type.models import in_exam_type
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from registrations.models import in_registrations
from result_finalization.models import in_result_finalization, in_result_finalizationdtls
from django.contrib.auth import get_user_model
User = get_user_model()



@login_required()
def statisticsDashboardManagerAPI(request):
    
    examtypelist = in_exam_type.objects.filter(is_active=True).all()
    
    context = {
        'examtypelist': examtypelist,
    }
    
    return render(request, 'statistics/statistics.html', context)



@login_required()
def getStudentsAddressManagerAPI(request):
    addresses = (
        in_registrations.objects.filter(is_active=True)
        .exclude(address__isnull=True)
        .exclude(address__exact='')
        .annotate(normalized_address=Lower('address'))
        .values_list('normalized_address', flat=True)
        .distinct()
    )

    # Clean and sort
    address_list = sorted(set(addr.strip().replace('\n', ', ') for addr in addresses if addr))

    # Save to JSON file
    json_data = {'addresses': address_list}
    file_path = os.path.join(settings.MEDIA_ROOT, 'student_addresses.json')

    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=2)

    return JsonResponse({'success': True, 'message': 'Address list saved to JSON.', 'file_url': settings.MEDIA_URL + 'student_addresses.json'})


@login_required()
def getExamSMSSummaryStatusManagerAPI(request):
    org_id = request.GET.get('filter_org')
    branch_id = request.GET.get('filter_branch')
    class_id = request.GET.get('is_class')
    section_id = request.GET.get('is_section')
    shifts_id = request.GET.get('is_shifts')
    groups_id = request.GET.get('is_groups')
    subject_id = request.GET.get('is_subjects')
    exam_type_id = request.GET.get('exam_type')
    start_date = parse_date(request.GET.get('start_date'))
    end_date = parse_date(request.GET.get('end_date'))

    filters = Q()
    if org_id:
        filters &= Q(org_id=org_id)
    if branch_id:
        filters &= Q(branch_id=branch_id)
    if class_id:
        filters &= Q(class_id=class_id)
    if section_id:
        filters &= Q(section_id=section_id)
    if shifts_id:
        filters &= Q(shifts_id=shifts_id)
    if groups_id:
        filters &= Q(groups_id=groups_id)
    if subject_id:
        filters &= Q(subject_id=subject_id)
    if exam_type_id:
        filters &= Q(exam_type_id=exam_type_id)
    if start_date and end_date:
        filters &= Q(created_date__range=(start_date, end_date))  # Adjust your model's date field name

    finalizations = in_result_finalization.objects.filter(filters, is_approved=True)
    result_ids = finalizations.values_list('res_fin_id', flat=True)
    dtls_queryset = in_result_finalizationdtls.objects.filter(res_fin_id__in=result_ids)

    return JsonResponse({
        'total_students': dtls_queryset.count(),
        'sms_sent_count': dtls_queryset.filter(sms_status=True).count(),
        'sms_not_sent_count': dtls_queryset.filter(sms_status=False).count(),
        'absent_students': dtls_queryset.filter(
            is_cq_apval=False,
            is_mcq_apval=False,
            is_written_apval=False,
            is_practical_apval=False,
            is_oral_apval=False
        ).count()
    })


@login_required()
def getStudentsTotalMarksManagerAPI(request):
    org_id = request.GET.get('filter_org')
    branch_id = request.GET.get('filter_branch')
    class_id = request.GET.get('is_class')
    section_id = request.GET.get('is_section')
    shifts_id = request.GET.get('is_shifts')
    groups_id = request.GET.get('is_groups')
    subject_id = request.GET.get('is_subjects')
    exam_type_id = request.GET.get('exam_type')
    start_date = parse_date(request.GET.get('start_date'))
    end_date = parse_date(request.GET.get('end_date'))

    filters = Q()
    if org_id:
        filters &= Q(org_id=org_id)
    if branch_id:
        filters &= Q(branch_id=branch_id)
    if class_id:
        filters &= Q(class_id=class_id)
    if section_id:
        filters &= Q(section_id=section_id)
    if shifts_id:
        filters &= Q(shifts_id=shifts_id)
    if groups_id:
        filters &= Q(groups_id=groups_id)
    if subject_id:
        filters &= Q(subject_id=subject_id)
    if exam_type_id:
        filters &= Q(exam_type_id=exam_type_id)
    if start_date and end_date:
        filters &= Q(created_date__range=(start_date, end_date))

    finalizations = in_result_finalization.objects.filter(filters, is_approved=True)
    result_ids = finalizations.values_list('res_fin_id', flat=True)

    dtls_queryset = (
        in_result_finalizationdtls.objects
        .filter(res_fin_id__in=result_ids)
        .select_related('reg_id', 'res_fin_id')
        .values(
            'reg_id__full_name',
            'res_fin_id__exam_date',
            'grand_total_marks'
        )
    )

    # Group data: {exam_date: {student_name: [marks_list]}}
    exam_date_map = defaultdict(dict)
    for row in dtls_queryset:
        student = row['reg_id__full_name']
        exam_date = row['res_fin_id__exam_date']
        if isinstance(exam_date, datetime):
            exam_date = exam_date.date()
        exam_date_str = exam_date.strftime('%Y-%m-%d') if exam_date else "Unknown"
        exam_date_map[exam_date_str][student] = row['grand_total_marks']

    # Build response structure
    all_students = sorted({student for scores in exam_date_map.values() for student in scores})
    all_dates = sorted(exam_date_map.keys())

    datasets = []
    for date in all_dates:
        marks = []
        for student in all_students:
            marks.append(exam_date_map[date].get(student, 0))
        datasets.append({
            'label': date,
            'data': marks,
        })

    return JsonResponse({
        'labels': all_students,
        'datasets': datasets
    })


@login_required()
def getStudentsParticularTopsMarksManagerAPI(request):
    org_id = request.GET.get('filter_org')
    branch_id = request.GET.get('filter_branch')
    class_id = request.GET.get('is_class')
    section_id = request.GET.get('is_section')
    shifts_id = request.GET.get('is_shifts')
    groups_id = request.GET.get('is_groups')
    subject_id = request.GET.get('is_subjects')
    exam_type_id = request.GET.get('exam_type')
    start_date = parse_date(request.GET.get('start_date'))
    end_date = parse_date(request.GET.get('end_date'))

    filters = Q()
    if org_id:
        filters &= Q(org_id=org_id)
    if branch_id:
        filters &= Q(branch_id=branch_id)
    if class_id:
        filters &= Q(class_id=class_id)
    if section_id:
        filters &= Q(section_id=section_id)
    if shifts_id:
        filters &= Q(shifts_id=shifts_id)
    if groups_id:
        filters &= Q(groups_id=groups_id)
    if subject_id:
        filters &= Q(subject_id=subject_id)
    if exam_type_id:
        filters &= Q(exam_type_id=exam_type_id)
    if start_date and end_date:
        filters &= Q(created_date__range=(start_date, end_date))

    finalizations = in_result_finalization.objects.filter(filters, is_approved=True)
    result_ids = finalizations.values_list('res_fin_id', flat=True)

    dtls_qs = in_result_finalizationdtls.objects.filter(res_fin_id__in=result_ids)

    top_marks = dtls_qs.aggregate(
        cq_top=Max('is_cq_marks'),
        mcq_top=Max('is_mcq_marks'),
        written_top=Max('is_written_marks'),
        practical_top=Max('is_practical_marks'),
        oral_top=Max('is_oral_marks'),
    )

    return JsonResponse(top_marks)


@login_required()
def getSectionWiseStudentInfoAPI(request):
    org_id = request.GET.get('filter_org')
    branch_id = request.GET.get('filter_branch')

    filters = {'is_active': True}
    if org_id:
        filters['org_id'] = org_id
    if branch_id:
        filters['branch_id'] = branch_id

    # Get relevant student registrations with class info
    registrations = in_registrations.objects.filter(**filters).select_related('class_id')

    # Get all unique section names
    all_section_names = (
        registrations
        .exclude(section_id__section_name__isnull=True)
        .values_list('section_id__section_name', flat=True)
        .distinct()
    )
    all_labels = list(all_section_names)

    result_data = {
        "labels": all_labels,
        "datasets": []
    }

    # Get class info ordered by class_no
    class_info_list = (
        in_class.objects
        .filter(class_id__in=registrations.values_list('class_id', flat=True).distinct())
        .order_by('class_no')
        .values('class_id', 'class_name')
    )

    for class_info in class_info_list:
        class_id = class_info['class_id']
        class_name = class_info['class_name'] or f"Class {class_id}"

        class_registrations = registrations.filter(class_id=class_id)
        class_data = {label: 0 for label in all_labels}  # Initialize all section counts to 0

        # Count students per section for this class
        section_counts = (
            class_registrations
            .exclude(section_id__section_name__isnull=True)
            .values('section_id__section_name')
            .annotate(count=Count('reg_id'))
        )
        for item in section_counts:
            section_name = item['section_id__section_name']
            class_data[section_name] = item['count']

        result_data["datasets"].append({
            "label": class_name,
            "data": class_data
        })

    return JsonResponse(result_data)


@login_required()
def getShiftWiseStudentInfoManagerAPI(request):
    org_id = request.GET.get('filter_org')
    branch_id = request.GET.get('filter_branch')

    filters = {'is_active': True}
    if org_id:
        filters['org_id'] = org_id
    if branch_id:
        filters['branch_id'] = branch_id

    registrations = in_registrations.objects.filter(**filters).select_related('class_id', 'shift_id')

    # Step 1: All unique class names for labels
    all_class_names = (
        registrations
        .exclude(class_id__class_name__isnull=True)
        .values_list('class_id__class_name', flat=True)
        .distinct()
    )
    all_labels = list(all_class_names)

    result_data = {
        "labels": all_labels,  # X-axis will show class names
        "datasets": []
    }

    # Step 2: All unique shifts (shift_name)
    shift_info_list = (
        in_shifts.objects
        .filter(shift_id__in=registrations.values_list('shift_id', flat=True).distinct())
        .values('shift_id', 'shift_name')
    )

    for shift_info in shift_info_list:
        shift_id = shift_info['shift_id']
        shift_name = shift_info['shift_name'] or f"Shift {shift_id}"

        shift_registrations = registrations.filter(shift_id=shift_id)
        shift_data = {label: 0 for label in all_labels}  # Initialize all class counts to 0

        # Count students per class under this shift
        class_counts = (
            shift_registrations
            .exclude(class_id__class_name__isnull=True)
            .values('class_id__class_name')
            .annotate(count=Count('reg_id'))
        )
        for item in class_counts:
            class_name = item['class_id__class_name']
            shift_data[class_name] = item['count']

        result_data["datasets"].append({
            "label": shift_name,  # Y-axis series label will be shift name
            "data": shift_data
        })

    return JsonResponse(result_data)

@login_required()
def getGroupWiseStudentInfoManagerAPI(request):
    org_id = request.GET.get('filter_org')
    branch_id = request.GET.get('filter_branch')

    filters = {'is_active': True}
    if org_id:
        filters['org_id'] = org_id
    if branch_id:
        filters['branch_id'] = branch_id

    registrations = in_registrations.objects.filter(**filters).select_related('class_id')

    # Step 1: Filter class_ids where allow_groups=True
    allowed_class_ids = in_class.objects.filter(
        class_id__in=registrations.values_list('class_id', flat=True).distinct(),
        allow_groups=True
    ).values_list('class_id', flat=True)

    # Step 2: Filter registrations based on allowed class_ids
    registrations = registrations.filter(class_id__in=allowed_class_ids)

    # Step 3: Get unique group names from filtered registrations
    all_group_names = (
        registrations
        .exclude(groups_id__groups_name__isnull=True)
        .values_list('groups_id__groups_name', flat=True)
        .distinct()
    )
    all_labels = list(all_group_names)

    result_data = {
        "labels": all_labels,
        "datasets": []
    }

    # Step 4: Get class info (only for allowed groups)
    class_info_list = (
        in_class.objects
        .filter(class_id__in=allowed_class_ids)
        .order_by('class_no')
        .values('class_id', 'class_name')
    )

    for class_info in class_info_list:
        class_id = class_info['class_id']
        class_name = class_info['class_name'] or f"Class {class_id}"

        class_registrations = registrations.filter(class_id=class_id)
        class_data = {label: 0 for label in all_labels}

        # Step 5: Count group-wise students for each allowed class
        group_counts = (
            class_registrations
            .exclude(groups_id__groups_name__isnull=True)
            .values('groups_id__groups_name')
            .annotate(count=Count('reg_id'))
        )
        for item in group_counts:
            group_name = item['groups_id__groups_name']
            class_data[group_name] = item['count']

        result_data["datasets"].append({
            "label": class_name,
            "data": class_data
        })

    return JsonResponse(result_data)

# @login_required()
# def getSectionShiftGroupsStudentInfoManagerAPI(request):
#     org_id = request.GET.get('filter_org')
#     branch_id = request.GET.get('filter_branch')

#     filters = {'is_active': True}
#     if org_id:
#         filters['org_id'] = org_id
#     if branch_id:
#         filters['branch_id'] = branch_id

#     registrations = in_registrations.objects.filter(**filters).select_related('class_id')

#     # Get all unique labels across all data
#     all_section_names = (
#         registrations
#         .exclude(section_id__section_name__isnull=True)
#         .values_list('section_id__section_name', flat=True)
#         .distinct()
#     )
#     all_shift_names = (
#         registrations
#         .exclude(shift_id__shift_name__isnull=True)
#         .values_list('shift_id__shift_name', flat=True)
#         .distinct()
#     )
#     all_group_names = (
#         registrations
#         .exclude(groups_id__groups_name__isnull=True)
#         .values_list('groups_id__groups_name', flat=True)
#         .distinct()
#     )

#     # Combine and make a unique label list
#     all_labels = list(dict.fromkeys(list(all_section_names) + list(all_shift_names) + list(all_group_names)))

#     result_data = {
#         "labels": ["Section", "Shifts", "Groups"],
#         "datasets": []
#     }

#     # Get class info ordered by class_no
#     class_info_list = (
#         in_class.objects
#         .filter(class_id__in=registrations.values_list('class_id', flat=True).distinct())
#         .order_by('class_no')
#         .values('class_id', 'class_name')
#     )

#     for class_info in class_info_list:
#         class_id = class_info['class_id']
#         class_name = class_info['class_name'] or f"Class {class_id}"

#         class_registrations = registrations.filter(class_id=class_id)
#         class_data = {label: 0 for label in all_labels}  # Initialize all to 0

#         # Fill actual section counts
#         section_counts = (
#             class_registrations
#             .exclude(section_id__section_name__isnull=True)
#             .values('section_id__section_name')
#             .annotate(count=Count('reg_id'))
#         )
#         for item in section_counts:
#             class_data[item['section_id__section_name']] = item['count']

#         # Fill actual shift counts
#         shift_counts = (
#             class_registrations
#             .exclude(shift_id__shift_name__isnull=True)
#             .values('shift_id__shift_name')
#             .annotate(count=Count('reg_id'))
#         )
#         for item in shift_counts:
#             class_data[item['shift_id__shift_name']] = item['count']

#         # Fill actual group counts
#         group_counts = (
#             class_registrations
#             .exclude(groups_id__groups_name__isnull=True)
#             .values('groups_id__groups_name')
#             .annotate(count=Count('reg_id'))
#         )
#         for item in group_counts:
#             class_data[item['groups_id__groups_name']] = item['count']

#         result_data["datasets"].append({
#             "label": class_name,
#             "data": class_data
#         })

#     return JsonResponse(result_data)


@login_required()
def getClasswiseStudentSummaryManagerAPI(request):
    org_id = request.GET.get('filter_org')
    branch_id = request.GET.get('filter_branch')

    filters = {'is_active': True}
    if org_id:
        filters['org_id'] = org_id
    if branch_id:
        filters['branch_id'] = branch_id

    queryset = in_registrations.objects.filter(**filters)

    total_count = queryset.count()

    classwise_counts = queryset.values('class_id__class_name').annotate(
        total=Count('class_id')
    ).order_by('class_id__class_name')

    class_data = {}
    for item in classwise_counts:
        class_name = item['class_id__class_name']
        class_data[class_name] = item['total']

    # Include "Total" as a separate pie slice
    chart_data = {'Total Students': total_count}
    chart_data.update(class_data)

    return JsonResponse({'classes': chart_data})


@login_required()
def getYearlyMonthWiseSMSStatusManagerAPI(request):
    org_id = request.GET.get('filter_org')
    branch_id = request.GET.get('filter_branch')

    filters = Q()
    if org_id:
        filters &= Q(org_id=org_id)
    if branch_id:
        filters &= Q(branch_id=branch_id)

    current_year = now().year

    # Filter approved finalizations using filters (no need to check date here)
    finalizations = in_result_finalization.objects.filter(
        filters,
        is_approved=True
    )

    result_ids = finalizations.values_list('res_fin_id', flat=True)

    # Get month-wise SMS count using sms_send_date
    sms_data = (
        in_result_finalizationdtls.objects
        .filter(
            res_fin_id__in=result_ids,
            sms_status=True,
            sms_send_date__year=current_year  # updated from created_date
        )
        .annotate(month=ExtractMonth('sms_send_date'))  # updated
        .values('month')
        .annotate(count=Count('res_findtl_id'))
        .order_by('month')
    )

    # Ensure all months are present
    month_names = [calendar.month_name[m] for m in range(1, 13)]
    sms_counts = OrderedDict((calendar.month_name[m], 0) for m in range(1, 13))

    for entry in sms_data:
        month_name = calendar.month_name[entry['month']]
        sms_counts[month_name] = entry['count']

    return JsonResponse({
        "labels": list(sms_counts.keys()),
        "datasets": [{
            "label": "SMS Sent",
            "data": list(sms_counts.values())
        }]
    })