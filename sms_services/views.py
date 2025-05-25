import sys
import json
import requests # type: ignore
import urllib.parse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime
from django.db.models import Max
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q, F, Sum, ExpressionWrapper, fields, FloatField, Count
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from exam_type.models import in_exam_type
from subject_setup.models import in_subjects
from defaults_exam_mode.models import in_exam_modes
from registrations.models import in_registrations
from result_finalization.models import in_result_finalization, in_result_finalizationdtls
from user_setup.models import access_list
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def smsListManagerAPI(request):
    user = request.user

    if user.is_superuser:
        # If the user is a superuser, retrieve all organizations
        org_list = organizationlst.objects.filter(is_active=True).all()
    elif user.org_id is not None:
        # If the user has an associated organization, retrieve only that organization
        org_list = organizationlst.objects.filter(
            is_active=True, org_id=user.org_id).all()
    else:
        # If neither a superuser nor associated with an organization, set organizations to an empty list or handle as needed
        org_list = []

    classlist = in_class.objects.filter(is_active=True).all()
    sectionlist = in_section.objects.filter(is_active=True).all()
    shiftslist = in_shifts.objects.filter(is_active=True).all()
    groupslist = in_groups.objects.filter(is_active=True).all()
    examtypelist = in_exam_type.objects.filter(is_active=True).all()

    context = {
        'org_list': org_list,
        'classlist': classlist,
        'sectionlist': sectionlist,
        'shiftslist': shiftslist,
        'groupslist': groupslist,
        'examtypelist': examtypelist,
    }
    return render(request, 'sms_services/send_sms_manager.html', context)


@login_required()
def getSMSSendListManagerAPI(request):
    filter_org = request.GET.get('filter_org')
    filter_branch = request.GET.get('filter_branch')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shift = request.GET.get('filter_shift')
    filter_groups = request.GET.get('filter_groups')
    filter_subjects = request.GET.get('filter_subjects')
    filter_examtype = request.GET.get('filter_examtype')

    filter_kwargs = Q()

    if filter_org:
        filter_kwargs &= Q(org_id=filter_org)
    if filter_branch:
        filter_kwargs &= Q(branch_id=filter_branch)
    if filter_class:
        filter_kwargs &= Q(class_id=filter_class)
    if filter_section:
        filter_kwargs &= Q(section_id=filter_section)
    if filter_shift:
        filter_kwargs &= Q(shifts_id=filter_shift)
    if filter_groups:
        filter_kwargs &= Q(groups_id=filter_groups)
    if filter_subjects:
        filter_kwargs &= Q(subject_id=filter_subjects)
    if filter_examtype:
        filter_kwargs &= Q(exam_type_id=filter_examtype)

    # Annotate total students, success and failed SMS counts
    smsdata = in_result_finalization.objects.filter(
        filter_kwargs, is_approved=True
    ).annotate(
        total_students=Count(
            'res_fin_id2in_res_finaldtl__reg_id', distinct=True),
        sms_success=Count('res_fin_id2in_res_finaldtl', filter=Q(
            res_fin_id2in_res_finaldtl__sms_status=True)),
        sms_fail=Count('res_fin_id2in_res_finaldtl', filter=Q(
            res_fin_id2in_res_finaldtl__sms_status=False)),
    )

    data = []
    for sms in smsdata:

        total_students = sms.total_students
        sms_success = sms.sms_success
        sms_fail = sms.sms_fail

        if total_students > sms_success:
            data.append({
                'res_fin_id': sms.res_fin_id,
                'created_date': sms.created_date,
                'exam_date': sms.exam_date,
                'names_of_exam': sms.names_of_exam or '',
                'class_name': getattr(sms.class_id, 'class_name', ''),
                'section_name': getattr(sms.section_id, 'section_name', ''),
                'shift_name': getattr(sms.shifts_id, 'shift_name', ''),
                'group_name': getattr(sms.groups_id, 'groups_name', ''),
                'exam_type_name': getattr(sms.exam_type_id, 'exam_type_name', ''),
                'total_students': total_students,
                'sms_success': sms_success,
                'sms_fail': sms_fail,
            })

    return JsonResponse({'data': data})


@login_required()
def getSMSCompleteListManagerAPI(request):
    filter_org = request.GET.get('filter_org')
    filter_branch = request.GET.get('filter_branch')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shift = request.GET.get('filter_shift')
    filter_groups = request.GET.get('filter_groups')
    filter_subjects = request.GET.get('filter_subjects')
    filter_examtype = request.GET.get('filter_examtype')

    filter_kwargs = Q()

    if filter_org:
        filter_kwargs &= Q(org_id=filter_org)
    if filter_branch:
        filter_kwargs &= Q(branch_id=filter_branch)
    if filter_class:
        filter_kwargs &= Q(class_id=filter_class)
    if filter_section:
        filter_kwargs &= Q(section_id=filter_section)
    if filter_shift:
        filter_kwargs &= Q(shifts_id=filter_shift)
    if filter_groups:
        filter_kwargs &= Q(groups_id=filter_groups)
    if filter_subjects:
        filter_kwargs &= Q(subject_id=filter_subjects)
    if filter_examtype:
        filter_kwargs &= Q(exam_type_id=filter_examtype)

    # Annotate total students, success and failed SMS counts
    smsdata = in_result_finalization.objects.filter(
        filter_kwargs, is_approved=True
    ).annotate(
        total_students=Count(
            'res_fin_id2in_res_finaldtl__reg_id', distinct=True),
        sms_success=Count('res_fin_id2in_res_finaldtl', filter=Q(
            res_fin_id2in_res_finaldtl__sms_status=True)),
        sms_fail=Count('res_fin_id2in_res_finaldtl', filter=Q(
            res_fin_id2in_res_finaldtl__sms_status=False)),
    )

    data = []
    for sms in smsdata:

        total_students = sms.total_students
        sms_success = sms.sms_success
        sms_fail = sms.sms_fail

        if total_students == sms_success:
            data.append({
                'res_fin_id': sms.res_fin_id,
                'created_date': sms.created_date,
                'exam_date': sms.exam_date,
                'names_of_exam': sms.names_of_exam or '',
                'class_name': getattr(sms.class_id, 'class_name', ''),
                'section_name': getattr(sms.section_id, 'section_name', ''),
                'shift_name': getattr(sms.shifts_id, 'shift_name', ''),
                'group_name': getattr(sms.groups_id, 'groups_name', ''),
                'exam_type_name': getattr(sms.exam_type_id, 'exam_type_name', ''),
                'total_students': total_students,
                'sms_success': sms_success,
                'sms_fail': sms_fail,
            })

    return JsonResponse({'data': data})


@login_required()
def sendSMSManagerAPI(request):
    res_fin_id = request.GET.get('id')
    sendSms = in_result_finalization.objects.filter(res_fin_id=res_fin_id).first()

    listdata = []
    if sendSms:
        final_dtls_qs = in_result_finalizationdtls.objects.filter(res_fin_id=sendSms, sms_status=False)

        # Step 1: Get highest grand total mark
        highest_marks = final_dtls_qs.aggregate(Max('grand_total_marks'))['grand_total_marks__max'] or 0

        for dtl in final_dtls_qs:
            registration = dtl.reg_id  # FK to in_registrations

            # Step 2: Absent check
            components_status = {
                'cq': dtl.is_cq_apval,
                'mcq': dtl.is_mcq_apval,
                'written': dtl.is_written_apval,
                'practical': dtl.is_practical_apval,
                'oral': dtl.is_oral_apval,
            }

            is_absent = not any(components_status.values())

            # Step 3: Mark breakdown
            exam_components = []
            if dtl.is_cq_apval and dtl.is_cq_marks is not None:
                exam_components.append(f"CQ-{dtl.is_cq_marks}")
            if dtl.is_mcq_apval and dtl.is_mcq_marks is not None:
                exam_components.append(f"MCQ-{dtl.is_mcq_marks}")
            if dtl.is_written_apval and dtl.is_written_marks is not None:
                exam_components.append(f"Written-{dtl.is_written_marks}")
            if dtl.is_practical_apval and dtl.is_practical_marks is not None:
                exam_components.append(f"Practical-{dtl.is_practical_marks}")
            if dtl.is_oral_apval and dtl.is_oral_marks is not None:
                exam_components.append(f"Oral-{dtl.is_oral_marks}")

            # Step 4: Message generation
            if is_absent:
                message = (
                    f"Dear Parents,\n"
                    f"{getattr(registration, 'full_name', 'Student')} was absent from school on {sendSms.exam_date.strftime('%d-%m-%Y')} and "
                    f"missed the {getattr(sendSms.exam_type_id, 'exam_type_name', '')}.\n"
                    f"Please ensure your child's presence in the next exam.\n"
                    f"SHKSC, EV"
                )
            else:
                components_text = ", ".join(exam_components)
                message = (
                    f"Dear {getattr(registration, 'full_name', 'Student')},\n"
                    f"Class: {getattr(sendSms.class_id, 'class_name', '')}, "
                    f"Exam Type: {getattr(sendSms.exam_type_id, 'exam_type_name', '')}, "
                    f"Date: {sendSms.exam_date.strftime('%d-%m-%Y')}, "
                    f"Subject: {getattr(sendSms.subject_id, 'subjects_name', '')}\n"
                    f"{components_text}, Obtained Mark: {dtl.grand_total_marks}, Highest: {highest_marks}\n"
                    f"SHKSC, EV"
                )

            listdata.append({
                'res_fin_id': sendSms.res_fin_id,
                'names_of_exam': sendSms.names_of_exam or '',
                'org_name': getattr(sendSms.org_id, 'org_name', ''),
                'branch_name': getattr(sendSms.branch_id, 'branch_name', ''),
                'exam_date': sendSms.exam_date,
                'class_name': getattr(sendSms.class_id, 'class_name', ''),
                'section_name': getattr(sendSms.section_id, 'section_name', ''),
                'shift_name': getattr(sendSms.shifts_id, 'shift_name', ''),
                'group_name': getattr(sendSms.groups_id, 'groups_name', ''),
                'subjects_name': getattr(sendSms.subject_id, 'subjects_name', ''),
                'exam_type_name': getattr(sendSms.exam_type_id, 'exam_type_name', ''),
                'res_findtl_id': dtl.res_findtl_id,
                'roll_no': dtl.roll_no or '',
                'dtls_class_name': dtl.class_name or '',
                'dtls_section_name': dtl.section_name or '',
                'dtls_shift_name': dtl.shift_name or '',
                'dtls_groups_name': dtl.groups_name or '',
                'grand_total_marks': dtl.grand_total_marks or 0,
                'student_name': getattr(registration, 'full_name', ''),
                'mobile_number': getattr(registration, 'mobile_number', ''),
                'messages': message,
                'sms_status': dtl.sms_status,
            })

    return render(request, 'sms_services/send_sms_services.html', {'listdata': listdata})



@login_required()
def sendSMSCompletedManagerAPI(request):
    res_fin_id = request.GET.get('res_fin_id')
    sendSms = in_result_finalization.objects.filter(res_fin_id=res_fin_id).first()

    listcomdata = []
    if sendSms:
        final_dtls_qs = in_result_finalizationdtls.objects.filter(res_fin_id=sendSms, sms_status=True)

        highest_marks = final_dtls_qs.aggregate(Max('grand_total_marks'))['grand_total_marks__max'] or 0

        for dtl in final_dtls_qs:
            registration = dtl.reg_id

            components_status = {
                'cq': dtl.is_cq_apval,
                'mcq': dtl.is_mcq_apval,
                'written': dtl.is_written_apval,
                'practical': dtl.is_practical_apval,
                'oral': dtl.is_oral_apval,
            }

            is_absent = not any(components_status.values())

            exam_components = []
            if dtl.is_cq_apval and dtl.is_cq_marks is not None:
                exam_components.append(f"CQ-{dtl.is_cq_marks}")
            if dtl.is_mcq_apval and dtl.is_mcq_marks is not None:
                exam_components.append(f"MCQ-{dtl.is_mcq_marks}")
            if dtl.is_written_apval and dtl.is_written_marks is not None:
                exam_components.append(f"Written-{dtl.is_written_marks}")
            if dtl.is_practical_apval and dtl.is_practical_marks is not None:
                exam_components.append(f"Practical-{dtl.is_practical_marks}")
            if dtl.is_oral_apval and dtl.is_oral_marks is not None:
                exam_components.append(f"Oral-{dtl.is_oral_marks}")

            if is_absent:
                message = (
                    f"Dear Parents,\n"
                    f"{getattr(registration, 'full_name', 'Student')} was absent from school on {sendSms.exam_date.strftime('%d-%m-%Y')} and "
                    f"missed the {getattr(sendSms.exam_type_id, 'exam_type_name', '')}.\n"
                    f"Please ensure your child's presence in the next exam.\n"
                    f"SHKSC, EV"
                )
            else:
                components_text = ", ".join(exam_components)
                message = (
                    f"Dear {getattr(registration, 'full_name', 'Student')},\n"
                    f"Class: {getattr(sendSms.class_id, 'class_name', '')}, "
                    f"Exam Type: {getattr(sendSms.exam_type_id, 'exam_type_name', '')}, "
                    f"Date: {sendSms.exam_date.strftime('%d-%m-%Y')}, "
                    f"Subject: {getattr(sendSms.subject_id, 'subjects_name', '')}\n"
                    f"{components_text}, Obtained Mark: {dtl.grand_total_marks}, Highest: {highest_marks}\n"
                    f"SHKSC, EV"
                )

            listcomdata.append({
                'res_fin_id': sendSms.res_fin_id,
                'names_of_exam': sendSms.names_of_exam or '',
                'org_name': getattr(sendSms.org_id, 'org_name', ''),
                'branch_name': getattr(sendSms.branch_id, 'branch_name', ''),
                'exam_date': sendSms.exam_date.strftime('%Y-%m-%d') if sendSms.exam_date else '',
                'class_name': getattr(sendSms.class_id, 'class_name', ''),
                'section_name': getattr(sendSms.section_id, 'section_name', ''),
                'shift_name': getattr(sendSms.shifts_id, 'shift_name', ''),
                'group_name': getattr(sendSms.groups_id, 'groups_name', ''),
                'subjects_name': getattr(sendSms.subject_id, 'subjects_name', ''),
                'exam_type_name': getattr(sendSms.exam_type_id, 'exam_type_name', ''),
                'res_findtl_id': dtl.res_findtl_id,
                'roll_no': dtl.roll_no or '',
                'dtls_class_name': dtl.class_name or '',
                'dtls_section_name': dtl.section_name or '',
                'dtls_shift_name': dtl.shift_name or '',
                'dtls_groups_name': dtl.groups_name or '',
                'grand_total_marks': dtl.grand_total_marks or 0,
                'student_name': getattr(registration, 'full_name', ''),
                'mobile_number': getattr(registration, 'mobile_number', ''),
                'messages': message,
                'sms_status': dtl.sms_status,
            })

    return render(request, 'sms_services/send_sms_complated_services.html', {
        'listcomdata': listcomdata
    })

# =============================== sms send function start ===============================
def send_sms(number, message):
    api_key = 'a5m3N7Q8bp6Uz8cj1gP9'
    sender_id = '8809617625469'
    base_url = 'https://bulksmsbd.net/api/smsapi'

    payload = {
        'api_key': api_key,
        'type': 'text',
        'number': number,
        'senderid': sender_id,
        'message': message  # no need to manually urlencode
    }

    try:
        response = requests.get(base_url, params=payload, timeout=10)
        return {'number': number, 'status': 'success', 'response': response.text}
    except Exception as e:
        return {'number': number, 'status': 'error', 'response': str(e)}


# Optional: map response_code to human-readable messages
RESPONSE_CODE_MESSAGES = {
    202: "SMS Submitted Successfully",
    1001: "Invalid Number",
    1002: "Sender id not correct/sender id is disabled",
    1003: "Please Required all fields/Contact Your System Administrator",
    1005: "Internal Error",
    1006: "Balance Validity Not Available",
    1007: "Balance Insufficient",
    1011: "User Id not found",
    1012: "Masking SMS must be sent in Bengali",
    1013: "Sender Id has not found Gateway by api key",
    1014: "Sender Type Name not found using this sender by api key",
    1015: "Sender Id has not found Any Valid Gateway by api key",
    1016: "Sender Type Name Active Price Info not found by this sender id",
    1017: "Sender Type Name Price Info not found by this sender id",
    1018: "The Owner of this (username) Account is disabled",
    1019: "The (sender type name) Price of this (username) Account is disabled",
    1020: "The parent of this account is not found.",
    1021: "The parent active (sender type name) price of this account is not found.",
    1031: "Your Account Not Verified, Please Contact Administrator.",
    1032: "ip Not whitelisted",
}

@login_required()
def sendingSMSManagerAPI(request):
    if request.method == "POST":
        res_findtl_ids = request.POST.getlist('res_findtl_id[]')
        phone_numbers = request.POST.getlist('phone_number[]')
        messages = request.POST.getlist('message_body[]')

        if not phone_numbers or not messages or len(phone_numbers) != len(messages) or len(res_findtl_ids) != len(phone_numbers):
            return JsonResponse({'status': 'failed', 'errmsg': 'Invalid input lengths for SMS sending.'})

        results = []
        successful_ids = []
        failed_msgs = []
        success_count = 0
        failure_count = 0

        with transaction.atomic():
            for res_id, phone, message in zip(res_findtl_ids, phone_numbers, messages):
                sms_result = send_sms(phone, message)
                results.append(sms_result)

                try:
                    response_data = sms_result.get('response')
                    if isinstance(response_data, str):
                        response_data = json.loads(response_data)

                    response_code = response_data.get('response_code')
                    status_msg = RESPONSE_CODE_MESSAGES.get(response_code, "Unknown Error")

                    if response_code == 202:
                        in_result_finalizationdtls.objects.filter(res_findtl_id=res_id).update(sms_status=True)
                        successful_ids.append(res_id)
                        success_count += 1
                    else:
                        failure_count += 1
                        failed_msgs.append(f"Number: {phone}, Error: {status_msg} (Code: {response_code})")

                except (ValueError, TypeError, AttributeError):
                    failure_count += 1
                    failed_msgs.append(f"Number: {phone}, Error: Invalid or no response format")

        final_msg = f"{success_count} SMS sent and status updated. {failure_count} failed."
        if failed_msgs:
            final_msg += " Errors: " + " | ".join(failed_msgs)

        return JsonResponse({
            'status': 'success',
            'msg': final_msg,
            'results': results
        })

    return JsonResponse({'status': 'failed', 'errmsg': 'Invalid request method'})

# =============================== sms send function end ===============================
