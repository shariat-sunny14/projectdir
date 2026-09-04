from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import FAQ
from user_auth.models import org_info


def whyUsManagerAPI(request):
    org_data = org_info.objects.first()
    faqs = FAQ.objects.filter(is_active=True).order_by('is_serial')

    context = {
        'org_data': org_data,
        'faqs': faqs,
    }
    return render(request, 'websites/why_us.html', context)


# 🔹 Create
@login_required
def faq_create(request):
    if request.method == "POST":
        FAQ.objects.create(
            question=request.POST.get('question'),
            answer=request.POST.get('answer'),
            is_serial=request.POST.get('is_serial') or 0,
            is_active=True if request.POST.get('is_active') == 'on' else False
        )
        messages.success(request, "FAQ Added Successfully")
        return redirect('faq_list')

    return render(request, 'faq/faq_create.html')


# 🔹 List
@login_required
def faq_list(request):
    faqs = FAQ.objects.all().order_by('is_serial')
    return render(request, 'faq/faq_list.html', {'faqs': faqs})


# 🔹 Update
@login_required
def faq_update(request, id):
    faq = get_object_or_404(FAQ, id=id)

    if request.method == "POST":
        faq.question = request.POST.get('question')
        faq.answer = request.POST.get('answer')
        faq.is_serial = request.POST.get('is_serial') or 0
        faq.is_active = True if request.POST.get('is_active') == 'on' else False
        faq.save()

        messages.success(request, "FAQ Updated Successfully")
        return redirect('faq_list')

    return render(request, 'faq/faq_update.html', {'faq': faq})


# 🔹 Delete
@login_required
def faq_delete(request, id):
    faq = get_object_or_404(FAQ, id=id)
    faq.delete()

    messages.success(request, "FAQ Deleted Successfully")
    return redirect('faq_list')