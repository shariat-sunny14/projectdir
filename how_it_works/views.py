from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProcessSectionForm, ProcessStepForm
from .models import ProcessSection, ProcessStep


# ---------------------------------------------------------
# PUBLIC-FACING: আসল website এ section টা রেন্ডার করার জন্য
# (home page view এর মধ্যে include করা যাবে, নিচে instructions দেওয়া আছে)
# ---------------------------------------------------------
def get_process_context():
    section = ProcessSection.load()
    steps = ProcessStep.objects.filter(is_active=True).order_by("order", "step_number")
    return {"process_section": section, "process_steps": steps}


# ---------------------------------------------------------
# ADMIN/BACKEND UI: এইখান থেকে data setup ও edit করা যাবে
# ---------------------------------------------------------
@login_required
def how_it_workstAPI(request):
    """সব step এবং section heading এক জায়গায় দেখাবে"""
    section = ProcessSection.load()
    steps = ProcessStep.objects.all().order_by("order", "step_number")
    context = {
        "section": section,
        "steps": steps,
    }
    return render(request, "how_it_works/dashboard.html", context)


@login_required
def section_edit(request):
    """kicker + heading edit করার ফর্ম"""
    section = ProcessSection.load()
    if request.method == "POST":
        form = ProcessSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, "Section heading আপডেট হয়েছে।")
            return redirect("how_it_works:how_it_workst")
    else:
        form = ProcessSectionForm(instance=section)
    return render(request, "how_it_works/section_form.html", {"form": form})


@login_required
def step_create(request):
    if request.method == "POST":
        form = ProcessStepForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "নতুন step যোগ করা হয়েছে।")
            return redirect("how_it_works:how_it_workst")
    else:
        form = ProcessStepForm()
    return render(
        request,
        "how_it_works/step_form.html",
        {"form": form, "title": "Add New Step"},
    )


@login_required
def step_update(request, pk):
    step = get_object_or_404(ProcessStep, pk=pk)
    if request.method == "POST":
        form = ProcessStepForm(request.POST, instance=step)
        if form.is_valid():
            form.save()
            messages.success(request, "Step আপডেট করা হয়েছে।")
            return redirect("how_it_works:how_it_workst")
    else:
        form = ProcessStepForm(instance=step)
    return render(
        request,
        "how_it_works/step_form.html",
        {"form": form, "title": f"Edit Step {step.formatted_step_number}"},
    )


@login_required
def step_delete(request, pk):
    step = get_object_or_404(ProcessStep, pk=pk)
    if request.method == "POST":
        step.delete()
        messages.success(request, "Step ডিলিট করা হয়েছে।")
        return redirect("how_it_works:how_it_workst")
    return render(request, "how_it_works/step_confirm_delete.html", {"step": step})
