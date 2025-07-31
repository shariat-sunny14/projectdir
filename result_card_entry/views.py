from django.db.models import Q
from audioop import reverse
from datetime import datetime
from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.contrib import messages
from django.db import transaction, IntegrityError
from organizations.models import branchslist, organizationlst
from class_setup.models import in_class
from groups_setup.models import in_groups
from section_setup.models import in_section
from shift_setup.models import in_shifts
from registrations.models import in_registrations
from subject_setup.models import in_subjects
from result_finalization.models import in_result_finalizationdtls
from attendant_manager.models import in_student_attendant, in_student_attendantdtls
from . models import in_results_card_entry, in_results_card_entry_dtls
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required()
def resultCardEntryListManagerAPI(request):
    
    return render(request, 'result_card_entry/result_card_entry_list.html')


@login_required()
def resultCardEntryRePrintListManagerAPI(request):
    
    return render(request, 'result_card_entry_re_print/result_card_entry_re_print_list.html')


@login_required()
def getRegistrationListDetailsAPI(request):
    org_filter = request.GET.get('filter_org')
    branch_filter = request.GET.get('filter_branch')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shift = request.GET.get('filter_shift')
    filter_groups = request.GET.get('filter_groups')

    filter_kwargs = Q()

    if org_filter:
        filter_kwargs &= Q(org_id=org_filter)
    
    if branch_filter:
        filter_kwargs &= Q(branch_id=branch_filter)
    
    if filter_class:
        filter_kwargs &= Q(class_id=filter_class)

    if filter_section:
        filter_kwargs &= Q(section_id=filter_section)

    if filter_shift:
        filter_kwargs &= Q(shift_id=filter_shift)

    if filter_groups:
        filter_kwargs &= Q(groups_id=filter_groups)

    reg_data = in_registrations.objects.filter(filter_kwargs)

    data = []
    current_year = now().year

    for reglist in reg_data:
        # Check if related results_card_entry exists for this reg_id and current year
        exists_result = in_results_card_entry.objects.filter(
            reg_id=reglist.reg_id,
            create_date=current_year
        ).exists()

        data.append({
            'reg_id': reglist.reg_id,
            'students_no': reglist.students_no,
            'org_name': getattr(reglist.org_id, 'org_name', None),
            'branch_name': getattr(reglist.branch_id, 'branch_name', None),
            'class_name': getattr(reglist.class_id, 'class_name', None),
            'section_name': getattr(reglist.section_id, 'section_name', None),
            'shift_name': getattr(reglist.shift_id, 'shift_name', None),
            'groups_name': getattr(reglist.groups_id, 'groups_name', None),
            'full_name': reglist.full_name,
            'roll_no': reglist.roll_no,
            'status': exists_result  # True if result exists, else False
        })

    return JsonResponse({'data': data})


@login_required()
def getResultCardEntryRePrintDetailsListAPI(request):
    org_filter = request.GET.get('filter_org')
    branch_filter = request.GET.get('filter_branch')
    filter_class = request.GET.get('filter_class')
    filter_section = request.GET.get('filter_section')
    filter_shift = request.GET.get('filter_shift')
    filter_groups = request.GET.get('filter_groups')
    filter_year = request.GET.get('filter_year')
    search_input = request.GET.get('searchInput')

    filter_kwargs = Q()

    if org_filter:
        filter_kwargs &= Q(org_id=org_filter)
    if branch_filter:
        filter_kwargs &= Q(branch_id=branch_filter)
    if filter_class:
        filter_kwargs &= Q(class_id=filter_class)
    if filter_section:
        filter_kwargs &= Q(section_id=filter_section)
    if filter_shift:
        filter_kwargs &= Q(shift_id=filter_shift)
    if filter_groups:
        filter_kwargs &= Q(groups_id=filter_groups)
        
    # Search logic (matches roll_no, full_name, or students_no)
    if search_input:
        filter_kwargs &= (
            Q(roll_no__icontains=search_input) |
            Q(full_name__icontains=search_input)
        )

    # Step 1: Get all matching registrations
    registrations = in_registrations.objects.filter(filter_kwargs)

    data = []

    for reg in registrations:
        # Step 2: Try to find matching result card
        try:
            result_card = in_results_card_entry.objects.get(reg_id=reg.reg_id, create_date=filter_year)
            res_card_id = result_card.res_card_id
            is_approved = result_card.is_approved
            approved_date = result_card.approved_date
            is_approved_by = result_card.is_approved_by.username if result_card.is_approved_by else ''
        except in_results_card_entry.DoesNotExist:
            res_card_id = ''
            is_approved = False
            approved_date = ''
            is_approved_by = ''

        # Step 3: Construct response row
        data.append({
            'res_card_id': res_card_id,
            'reg_id': reg.reg_id,
            'students_no': reg.students_no,
            'org_name': getattr(reg.org_id, 'org_name', None),
            'branch_name': getattr(reg.branch_id, 'branch_name', None),
            'class_name': getattr(reg.class_id, 'class_name', None),
            'section_name': getattr(reg.section_id, 'section_name', None),
            'shift_name': getattr(reg.shift_id, 'shift_name', None),
            'groups_name': getattr(reg.groups_id, 'groups_name', None),
            'full_name': reg.full_name,
            'roll_no': reg.roll_no,
            'is_approved': is_approved,
            'approved_date': approved_date,
            'is_approved_by': is_approved_by,
        })

    return JsonResponse({'data': data})


@login_required()
def getResultsEntryUIManagerAPI(request):
    org_id = request.GET.get('org_id')
    branch_id = request.GET.get('branch_id')
    reg_id = request.GET.get('reg_id')
    is_year = request.GET.get('is_year')

    org_list = get_object_or_404(organizationlst, org_id=org_id)
    branch_list = get_object_or_404(branchslist, branch_id=branch_id)
    registration = get_object_or_404(in_registrations, reg_id=reg_id)

    subjects = in_subjects.objects.filter(
        class_id=registration.class_id,
        groups_id=registration.groups_id,
        org_id=registration.org_id,
        is_active=True
    ).order_by('subjects_no')
    
    def title_case(value):
        if value:
            return ' '.join(word.capitalize() for word in value.split())
        return ''

    # Title Case apply
    registration_data = {
        'reg_id': registration.reg_id,
        'class_id': registration.class_id.class_id if registration.class_id else '',
        'section_id': registration.section_id.section_id if registration.section_id else '',
        'shift_id': registration.shift_id.shift_id if registration.shift_id else '',
        'groups_id': registration.groups_id.groups_id if registration.groups_id else '',
        'full_name': title_case(registration.full_name),
        'father_name': title_case(registration.father_name),
        'mother_name': title_case(registration.mother_name),
        'class_name': registration.class_id.class_name if registration.class_id else '',
        'section_name': registration.section_id.section_name if registration.section_id else '',
        'shift_name': registration.shift_id.shift_name if registration.shift_id else '',
        'roll_no': registration.roll_no or '',
    }

    context = {
        'org_list': org_list,
        'branch_list': branch_list,
        'registration': registration_data,  # Use title-cased dict
        'subjects': subjects,
        'is_year': is_year, # for half-yearly, yearly results generation
    }

    return render(request, 'result_card_entry/result_card_half_yearly.html', context)


@login_required()
def getHalfYearlyResultAPI(request):
    if request.method == 'GET':
        filter_kwargs = {}

        def safe_int(param_name):
            value = request.GET.get(param_name)
            return int(value) if value and value.isdigit() else None

        # Collect parameters
        org_id = safe_int('org_id')
        branch_id = safe_int('branch_id')
        reg_id = safe_int('reg_id')
        class_id = safe_int('class_id')
        section_id = safe_int('section_id')
        shift_id = safe_int('shift_id')
        groups_id = safe_int('groups_id')
        year = safe_int('year')

        # Fixed filter
        filter_kwargs.update({
            'org_id': org_id,
            'branch_id': branch_id,
            'reg_id': reg_id,
            'class_id': class_id,
            'section_id': section_id,
            'shifts_id': shift_id,
            'groups_id': groups_id,
            'finalize_year': year,
            'is_half_yearly': True
        })

        response_data = {
            'success': True,
            'message': '',
            'subjects': []
        }

        try:
            result_qs = in_result_finalizationdtls.objects.filter(**filter_kwargs)

            for result in result_qs:
                response_data['subjects'].append({
                    'subject_id': result.subject_id.subjects_id if result.subject_id else None,
                    'is_mcq_marks': result.is_mcq_marks,
                    'is_written_marks': result.is_written_marks,
                    'is_practical_marks': result.is_practical_marks,
                })

        except Exception as e:
            response_data['success'] = False
            response_data['message'] = str(e)
            return JsonResponse(response_data)

        # Now fetch working_days from in_student_attendant
        try:
            att_filter = {
                'org_id': org_id,
                'branch_id': branch_id,
                'class_id': class_id,
                'section_id': section_id,
                'shifts_id': shift_id,
                'groups_id': groups_id,
                'attendant_year': year,
                'is_half_yearly': True
            }
            working_att = in_student_attendant.objects.filter(**att_filter).first()
            response_data['working_days'] = working_att.working_days if working_att else 0
        except Exception as e:
            response_data['working_days'] = 0

        # Fetch attendant_qty from in_student_attendantdtls
        try:
            attdtl_filter = {
                'org_id': org_id,
                'branch_id': branch_id,
                'class_id': class_id,
                'section_id': section_id,
                'shifts_id': shift_id,
                'groups_id': groups_id,
                'reg_id': reg_id,
                'attendant_year': year,
                'is_half_yearly': True
            }
            qty_obj = in_student_attendantdtls.objects.filter(**attdtl_filter).first()
            response_data['attendant_qty'] = qty_obj.attendant_qty if qty_obj else 0
        except Exception as e:
            response_data['attendant_qty'] = 0

        return JsonResponse(response_data)

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required()
def saveResultsCardEntryManagerAPI(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    org_id = data.get('is_org_id')
    branch_id = data.get('is_branch_id')
    reg_id = data.get('is_reg_id')
    class_id = data.get('is_class_id')
    section_id = data.get('is_section_id')
    shift_id = data.get('is_shifts_id')
    groups_id = data.get('is_groups_id')
    merit_position = data.get('merit_position')
    if merit_position == '':
        merit_position = None
    total_working_days = data.get('total_working_days')
    total_present_days = data.get('total_present_days')
    is_remarks = data.get('is_remarks')
    date_of_publication_raw = data.get('date_of_publication')
    is_average_gpa = data.get('is_average_gpa')
    average_letter_grade = data.get('average_letter_grade')
    result_status = data.get('result_status')
    total_defaults_marks = data.get('total_defaults_marks')
    is_grand_total_marks = data.get('is_grand_total_marks', 0)
    total_pass_marks = data.get('total_pass_marks', 0)
    is_year = data.get('is_year', 0)


    try:
        with transaction.atomic():
            org_instance = organizationlst.objects.get(org_id=org_id)
            branch_instance = branchslist.objects.get(branch_id=branch_id)
            class_instance = in_class.objects.get(class_id=class_id)
            section_instance = in_section.objects.get(section_id=section_id)
            shift_instance = in_shifts.objects.get(shift_id=shift_id)
            if groups_id:
                groups_instance = in_groups.objects.get(groups_id=groups_id)
            else:
                groups_instance = None
            
            if is_grand_total_marks:
                is_grand_total_marks = is_grand_total_marks
            else:
                is_grand_total_marks = 0

            if reg_id:
                reg_instance = in_registrations.objects.get(reg_id=reg_id)
            else:
                reg_instance = None

            date_of_publication = None
            if date_of_publication_raw:
                try:
                    # Convert from 'DD-MM-YYYY' to 'YYYY-MM-DD'
                    date_of_publication = datetime.strptime(date_of_publication_raw, '%d-%m-%Y').date()
                except ValueError:
                    resp['msg'] = f"Invalid date format for date_of_publication: {date_of_publication_raw}"
                    return JsonResponse(resp)

            res_card_entry = in_results_card_entry.objects.create(
                date_of_publication=date_of_publication,
                create_date=is_year,
                org_id=org_instance,
                branch_id=branch_instance,
                reg_id=reg_instance,
                class_id=class_instance,
                section_id=section_instance,
                shift_id=shift_instance,
                groups_id=groups_instance,
                is_half_year=True,
                is_annual=False,
                is_average_gpa=is_average_gpa,
                average_letter_grade=average_letter_grade,
                result_status=result_status,
                total_defaults_marks=total_defaults_marks,
                is_grand_pass_marks=total_pass_marks,
                is_grand_total_marks=is_grand_total_marks,
                merit_position=merit_position,
                total_working_days=total_working_days,
                total_present_days=total_present_days,
                is_remarks=is_remarks,
                is_approved=True,
                is_approved_by=request.user,
                approved_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ss_creator=request.user,
                ss_modifier=request.user
            )

            res_card_id = res_card_entry.res_card_id

            # Fetch all POST data at once
            details_data = list(zip(
                request.POST.getlist('is_subjects_id[]'),
                request.POST.getlist('sub_defaults_marks[]'),
                request.POST.getlist('sub_pass_marks[]'),
                request.POST.getlist('is_mcq[]'),
                request.POST.getlist('is_written[]'),
                request.POST.getlist('is_practical[]'),
                request.POST.getlist('total_inv_marks[]'),
                request.POST.getlist('sub_letter_grade[]'),
                request.POST.getlist('is_sub_gp[]'),
            ))

            for subjects_id, sub_defaults_marks, sub_pass_marks, is_mcq, is_written, is_practical, total_inv_marks, sub_letter_grade, is_sub_gp in details_data:
                subs_instance = in_subjects.objects.get(subjects_id=subjects_id)

                results_card_detail = in_results_card_entry_dtls.objects.create(
                    res_card_id=res_card_entry,
                    subjects_id=subs_instance,
                    sub_defaults_marks=sub_defaults_marks,
                    sub_pass_marks=sub_pass_marks,
                    is_mcq=is_mcq,
                    is_written=is_written,
                    is_practical=is_practical,
                    total_inv_marks=total_inv_marks,
                    sub_letter_grade=sub_letter_grade,
                    is_sub_gp=is_sub_gp,
                    ss_creator=request.user,
                    ss_modifier=request.user,
                )

            resp['status'] = 'success'
            resp['res_card_id'] = res_card_id
    except Exception as e:
        resp['msg'] = str(e)

    return JsonResponse(resp)

@login_required()
def resultsCardEntryReportManagerAPI(request):
    id = request.GET.get('id')

    card_entry = get_object_or_404(in_results_card_entry, res_card_id=id)

    # Correct: Fetch all subject results linked to this result card
    subjects = in_results_card_entry_dtls.objects.filter(res_card_id=card_entry).select_related('subjects_id')

    def title_case(value):
        if value:
            return ' '.join(word.capitalize() for word in value.split())
        return ''

    transaction = {
        'create_date': card_entry.create_date or '',
        'reg_id': card_entry.reg_id.reg_id if card_entry.reg_id else '',
        'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
        'full_name': title_case(card_entry.reg_id.full_name) if card_entry.reg_id else '',
        'roll_no': card_entry.reg_id.roll_no if card_entry.reg_id else '',
        'father_name': title_case(card_entry.reg_id.father_name) if card_entry.reg_id else '',
        'mother_name': title_case(card_entry.reg_id.mother_name) if card_entry.reg_id else '',
        'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
        'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
        'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
        'merit_position': card_entry.merit_position or '',
        'total_working_days': card_entry.total_working_days or '',
        'total_present_days': card_entry.total_present_days or '',
        'is_remarks': card_entry.is_remarks or '',
        'date_of_publication': card_entry.date_of_publication or '',
        'is_average_gpa': card_entry.is_average_gpa or '',
        'average_letter_grade': card_entry.average_letter_grade or '',
        'result_status': card_entry.result_status or '',
        'total_defaults_marks': card_entry.total_defaults_marks or '',
        'is_grand_pass_marks': card_entry.is_grand_pass_marks or '',
        'is_grand_total_marks': card_entry.is_grand_total_marks or '',
    }

    context = {
        "transaction": transaction,
        "subjects": subjects,
    }

    return render(request, 'result_card_entry/result_card_half_yearly_viewer.html', context)


@login_required()
def printResultsCardEntryReportManagerAPI(request):
    id = request.GET.get('id')

    card_entry = get_object_or_404(in_results_card_entry, res_card_id=id)

    # Correct: Fetch all subject results linked to this result card
    subjects = in_results_card_entry_dtls.objects.filter(res_card_id=card_entry).select_related('subjects_id')

    def title_case(value):
        if value:
            return ' '.join(word.capitalize() for word in value.split())
        return ''

    transaction = {
        'res_card_id': card_entry.res_card_id,
        'create_date': card_entry.create_date or '',
        'reg_id': card_entry.reg_id.reg_id if card_entry.reg_id else '',
        'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
        'full_name': title_case(card_entry.reg_id.full_name) if card_entry.reg_id else '',
        'roll_no': card_entry.reg_id.roll_no if card_entry.reg_id else '',
        'father_name': title_case(card_entry.reg_id.father_name) if card_entry.reg_id else '',
        'mother_name': title_case(card_entry.reg_id.mother_name) if card_entry.reg_id else '',
        'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
        'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
        'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
        'merit_position': card_entry.merit_position or '',
        'total_working_days': card_entry.total_working_days or '',
        'total_present_days': card_entry.total_present_days or '',
        'is_remarks': card_entry.is_remarks or '',
        'date_of_publication': card_entry.date_of_publication or '',
        'is_average_gpa': card_entry.is_average_gpa or '',
        'average_letter_grade': card_entry.average_letter_grade or '',
        'result_status': card_entry.result_status or '',
        'total_defaults_marks': card_entry.total_defaults_marks or '',
        'is_grand_pass_marks': card_entry.is_grand_pass_marks or '',
        'is_grand_total_marks': card_entry.is_grand_total_marks or '',
    }

    context = {
        "transaction": transaction,
        "subjects": subjects,
    }

    return render(request, 'result_card_entry/print_result_card_half_yearly_report.html', context)


def print_transcript(request):
    id = request.GET.get('id')
    card_entry = get_object_or_404(in_results_card_entry, res_card_id=id)

    subjects = in_results_card_entry_dtls.objects.filter(res_card_id=card_entry).select_related('subjects_id')

    def parse_int_param(value):
        return int(value) if value and value not in ['null', 'None'] else None

    is_class = parse_int_param(request.GET.get('is_class', ''))
    is_section = parse_int_param(request.GET.get('is_section', ''))
    is_shift = parse_int_param(request.GET.get('is_shift', ''))
    is_groups = parse_int_param(request.GET.get('is_groups', ''))

    filter_q = Q(org_id=card_entry.org_id, branch_id=card_entry.branch_id)
    if is_class:
        filter_q &= Q(class_id=is_class)
    if is_section:
        filter_q &= Q(section_id=is_section)
    if is_shift:
        filter_q &= Q(shift_id=is_shift)
    if is_groups:
        filter_q &= Q(groups_id=is_groups)

    class_entries = in_results_card_entry.objects.filter(filter_q).select_related('reg_id')

    def sort_key(entry):
        gpa = float(entry.is_average_gpa or 0.0)
        total = int(entry.is_grand_total_marks or 0)
        roll = int(entry.reg_id.roll_no) if entry.reg_id and entry.reg_id.roll_no and entry.reg_id.roll_no.isdigit() else 99999
        return (-gpa, -total, roll)

    sorted_entries = sorted(class_entries, key=sort_key)

    ranking_map = {}
    previous_key = None
    current_position = 1
    merit_counter = 1

    for entry in sorted_entries:
        key = sort_key(entry)
        if previous_key is not None and key == previous_key:
            pass
        else:
            merit_counter = current_position
        ranking_map[entry.res_card_id] = merit_counter
        previous_key = key
        current_position += 1

    calculated_merit_position = ranking_map.get(card_entry.res_card_id, '')
    
    def title_case(value):
        if value:
            return ' '.join(word.capitalize() for word in value.split())
        return ''

    transaction = {
        'create_date': card_entry.create_date or '',
        'reg_id': card_entry.reg_id.reg_id if card_entry.reg_id else '',
        'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
        'full_name': title_case(card_entry.reg_id.full_name) if card_entry.reg_id else '',
        'roll_no': card_entry.reg_id.roll_no if card_entry.reg_id else '',
        'father_name': title_case(card_entry.reg_id.father_name) if card_entry.reg_id else '',
        'mother_name': title_case(card_entry.reg_id.mother_name) if card_entry.reg_id else '',
        'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
        'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
        'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
        'merit_position': calculated_merit_position,
        'total_working_days': card_entry.total_working_days or '',
        'total_present_days': card_entry.total_present_days or '',
        'is_remarks': card_entry.is_remarks or '',
        'date_of_publication': card_entry.date_of_publication or '',
        'is_average_gpa': card_entry.is_average_gpa or '',
        'average_letter_grade': card_entry.average_letter_grade or '',
        'result_status': card_entry.result_status or '',
        'total_defaults_marks': card_entry.total_defaults_marks or '',
        'is_grand_pass_marks': card_entry.is_grand_pass_marks or '',
        'is_grand_total_marks': card_entry.is_grand_total_marks or '',
    }

    context = {
        "transaction": transaction,
        "subjects": subjects,
        "printed_on": datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
    }

    html_string = render_to_string("result_card_entry/print_result_card_half_yearly_report.html", context)

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response['Content-Disposition'] = 'inline; filename="Students_Transcript_Report.pdf"'
    return response



# ১. is_class, is_section, is_shift, is_groups থেকে যেসব মান আসবে তা দিয়ে in_results_card_entry.objects.filter() হবে:
# অর্থাৎ, ইউজার যদি ক্লাস, সেকশন, শিফট, গ্রুপ সিলেক্ট করে তাহলে ঐ মানগুলোর উপর ভিত্তি করে filter() হবে।
# কিন্তু যদি কোন ফিল্ড null, 'null', 'None', অথবা খালি ('') হয়, তাহলে সেই ফিল্ড বাদ দিয়ে সব ক্লাস/সেকশন/শিফট/গ্রুপ এর রেজাল্ট দেখা যাবে।
# অর্থাৎ, ঐ ফিল্ডটি ফিল্টার করার দরকার নেই।

# ২. is_grand_total_marks এর বদলে merit sort হবে is_average_gpa অনুযায়ী:
# আগে যেভাবে is_grand_total_marks দিয়ে সবার র‍্যাংকিং করা হতো, এখন সেটা হবে is_average_gpa দিয়ে।
# অর্থাৎ, যার GPA বেশি, তার পজিশন আগে হবে।

# ৩. যদি কারো is_average_gpa সমান হয়, তাহলে is_grand_total_marks দেখা হবে:
# GPA সমান হলেও যার টোটাল মার্কস বেশি, তার merit position হবে আগে।

# ৪. যদি is_average_gpa এবং is_grand_total_marks দুইটাই সমান হয়, তাহলে:
# তখন reg_id.roll_no দেখা হবে।
# যার রোল নাম্বার সবচেয়ে ছোট (মানে, রোল ১ → রোল ২ → রোল ৩...), সে আগের merit position পাবে।

def print_multiple_transcripts(request):
    ids = request.GET.get('ids', '')
    id_list = [res_id for res_id in ids.split(',') if res_id.isdigit()]

    # Helper function to safely parse integer filters
    def parse_int_param(value):
        return int(value) if value and value != 'null' and value != 'None' else None

    is_class = parse_int_param(request.GET.get('is_class', ''))
    is_section = parse_int_param(request.GET.get('is_section', ''))
    is_shift = parse_int_param(request.GET.get('is_shift', ''))
    is_groups = parse_int_param(request.GET.get('is_groups', ''))

    combined_html = ""

    for res_id in id_list:
        try:
            card_entry = in_results_card_entry.objects.select_related(
                'class_id', 'section_id', 'shift_id', 'groups_id',
                'org_id', 'branch_id', 'reg_id'
            ).get(res_card_id=int(res_id))
        except in_results_card_entry.DoesNotExist:
            continue

        subjects = in_results_card_entry_dtls.objects.filter(res_card_id=card_entry).select_related('subjects_id')

        # Build dynamic Q filter for class comparison
        filter_q = Q(org_id=card_entry.org_id, branch_id=card_entry.branch_id)

        if is_class:
            filter_q &= Q(class_id=is_class)
        if is_section:
            filter_q &= Q(section_id=is_section)
        if is_shift:
            filter_q &= Q(shift_id=is_shift)
        if is_groups:
            filter_q &= Q(groups_id=is_groups)

        class_entries = in_results_card_entry.objects.filter(filter_q).select_related('reg_id')

        # Sort by: average_gpa DESC, grand_total_marks DESC, roll_no ASC
        def sort_key(entry):
            gpa = float(entry.is_average_gpa or 0.0)
            total = int(entry.is_grand_total_marks or 0)
            roll = int(entry.reg_id.roll_no) if entry.reg_id and entry.reg_id.roll_no and entry.reg_id.roll_no.isdigit() else 99999
            return (-gpa, -total, roll)

        sorted_entries = sorted(class_entries, key=sort_key)

        # Assign merit positions
        ranking_map = {}
        previous_key = None
        current_position = 1
        merit_counter = 1

        for entry in sorted_entries:
            key = sort_key(entry)
            if previous_key is not None and key == previous_key:
                # Same merit position for same scores
                pass
            else:
                merit_counter = current_position
            ranking_map[entry.res_card_id] = merit_counter
            previous_key = key
            current_position += 1

        calculated_merit_position = ranking_map.get(card_entry.res_card_id, '')
        
        def title_case(value):
            if value:
                return ' '.join(word.capitalize() for word in value.split())
            return ''

        transaction = {
            'create_date': card_entry.create_date or '',
            'reg_id': card_entry.reg_id.reg_id if card_entry.reg_id else '',
            'org_name': card_entry.org_id.org_name if card_entry.org_id else '',
            'full_name': title_case(card_entry.reg_id.full_name) if card_entry.reg_id else '',
            'roll_no': card_entry.reg_id.roll_no if card_entry.reg_id else '',
            'father_name': title_case(card_entry.reg_id.father_name) if card_entry.reg_id else '',
            'mother_name': title_case(card_entry.reg_id.mother_name) if card_entry.reg_id else '',
            'class_name': card_entry.class_id.class_name if card_entry.class_id else '',
            'section_name': card_entry.section_id.section_name if card_entry.section_id else '',
            'shift_name': card_entry.shift_id.shift_name if card_entry.shift_id else '',
            'merit_position': calculated_merit_position,
            'total_working_days': card_entry.total_working_days or '',
            'total_present_days': card_entry.total_present_days or '',
            'is_remarks': card_entry.is_remarks or '',
            'date_of_publication': card_entry.date_of_publication or '',
            'is_average_gpa': card_entry.is_average_gpa or '',
            'average_letter_grade': card_entry.average_letter_grade or '',
            'result_status': card_entry.result_status or '',
            'total_defaults_marks': card_entry.total_defaults_marks or '',
            'is_grand_pass_marks': card_entry.is_grand_pass_marks or '',
            'is_grand_total_marks': card_entry.is_grand_total_marks or '',
        }

        context = {
            "transaction": transaction,
            "subjects": subjects,
            "printed_on": datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
        }

        html_string = render_to_string("result_card_entry/print_result_card_half_yearly_report.html", context)
        combined_html += f'<div style="page-break-after: always;">{html_string}</div>'

    # Remove last trailing page break
    if combined_html.endswith('page-break-after: always;">'):
        combined_html = combined_html.rsplit('<div style="page-break-after: always;">', 1)[0]

    pdf = HTML(string=combined_html, base_url=request.build_absolute_uri('/')).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Academic_Transcript_Report.pdf"'
    return response


def testingAPI(request):
    

    return render(request, 'result_card_entry/print_result_card_half_yearly_report.html')