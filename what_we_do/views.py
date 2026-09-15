# what_we_do/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Service, ServiceSection
from .forms import ServiceForm, ServiceSectionForm


def service_home(request):
    """মূল UI — services list + Section heading edit ফর্ম + Add Service ফর্ম"""

    section = ServiceSection.load()
    section_form = ServiceSectionForm(instance=section)
    service_form = ServiceForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # --- Section heading এডিট ---
        if form_type == 'section':
            section_form = ServiceSectionForm(request.POST, instance=section)
            if section_form.is_valid():
                section_form.save()
                messages.success(request, "Section heading সফলভাবে আপডেট হয়েছে!")
                return redirect('what_we_do:service_home')
            else:
                messages.error(request, "Section ফর্মে কিছু ভুল আছে।")

        # --- নতুন Service অ্যাড ---
        elif form_type == 'service':
            service_form = ServiceForm(request.POST)
            if service_form.is_valid():
                service_form.save()
                messages.success(request, "নতুন সার্ভিস সফলভাবে যোগ করা হয়েছে!")
                return redirect('what_we_do:service_home')
            else:
                messages.error(request, "Service ফর্মে কিছু ভুল আছে।")

    context = {
        'section': section,
        'services': Service.objects.filter(is_active=True),
        'section_form': section_form,
        'service_form': service_form,
    }
    return render(request, 'what_we_do/home.html', context)


def service_edit(request, pk):
    """UI থেকে existing সার্ভিস এডিট করার জন্য"""
    service = get_object_or_404(Service, pk=pk)
    section = ServiceSection.load()

    if request.method == 'POST':
        service_form = ServiceForm(request.POST, instance=service)
        if service_form.is_valid():
            service_form.save()
            messages.success(request, "সার্ভিস আপডেট হয়েছে!")
            return redirect('what_we_do:service_home')
    else:
        service_form = ServiceForm(instance=service)

    context = {
        'section': section,
        'services': Service.objects.filter(is_active=True),
        'section_form': ServiceSectionForm(instance=section),
        'service_form': service_form,
        'editing': service,
    }
    return render(request, 'what_we_do/home.html', context)


def service_delete(request, pk):
    """UI থেকে সার্ভিস ডিলিট করার জন্য"""
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.delete()
        messages.success(request, "সার্ভিস ডিলিট করা হয়েছে।")
    return redirect('what_we_do:service_home')