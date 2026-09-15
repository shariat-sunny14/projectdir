from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST

from .forms import TestimonialForm
from .models import Testimonial


# ---------------------------------------------------------------------------
# PUBLIC SIDE — homepage form + JSON API for the site's testimonials section
# ---------------------------------------------------------------------------

def testimonial_create(request):
    """
    Public form — client ra ei view diye testimonial submit korbe.
    Notun entry default e is_approved=False thakbe, dashboard theke
    approve/edit/delete kora jabe.
    """
    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Thank you! Your testimonial has been submitted and will appear after review."
            )
            return redirect("testimonials:create")
    else:
        form = TestimonialForm()

    return render(request, "testimonials/testimonial_form.html", {"form": form})


@require_http_methods(["GET"])
def testimonial_list_api(request):
    """
    JSON API — shudhu approved testimonials return kore.
    Homepage er JS (div#testimonials) ei API fetch kore card banabe.
    """
    qs = Testimonial.objects.filter(is_approved=True)

    data = []
    for t in qs:
        data.append({
            "id": t.id,
            "couple_name": t.couple_name,
            "message": t.message,
            "image_url": t.image.url if t.image else None,
            "created_at": t.created_at.strftime("%d %b, %Y"),
        })

    return JsonResponse({"results": data})


# ---------------------------------------------------------------------------
# DASHBOARD (STAFF ONLY) — list / add / edit / delete UI
# ---------------------------------------------------------------------------

@staff_member_required
def dashboard_list(request):
    """
    Shob testimonials (approved + pending) ekta table/list a dekhabe,
    each row theke Edit / Delete, ar upore Add New button.
    """
    testimonials = Testimonial.objects.all()
    return render(request, "testimonials/dashboard_list.html", {
        "testimonials": testimonials,
        "approved_count": testimonials.filter(is_approved=True).count(),
        "pending_count": testimonials.filter(is_approved=False).count(),
    })


@staff_member_required
def dashboard_add(request):
    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Testimonial added successfully.")
            return redirect("testimonials:dashboard_list")
    else:
        form = TestimonialForm()

    return render(request, "testimonials/dashboard_form.html", {
        "form": form,
        "mode": "add",
    })


@staff_member_required
def dashboard_edit(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)

    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES, instance=testimonial)
        if form.is_valid():
            form.save()
            messages.success(request, "Testimonial updated successfully.")
            return redirect("testimonials:dashboard_list")
    else:
        form = TestimonialForm(instance=testimonial)

    return render(request, "testimonials/dashboard_form.html", {
        "form": form,
        "mode": "edit",
        "testimonial": testimonial,
    })


@staff_member_required
def dashboard_delete(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)

    if request.method == "POST":
        testimonial.delete()
        messages.success(request, "Testimonial deleted.")
        return redirect("testimonials:dashboard_list")

    return render(request, "testimonials/dashboard_confirm_delete.html", {
        "testimonial": testimonial,
    })


@staff_member_required
@require_POST
def dashboard_toggle_approve(request, pk):
    """
    List view theke ekta quick toggle button diye approve/unapprove
    kora jay, alada page a na giye.
    """
    testimonial = get_object_or_404(Testimonial, pk=pk)
    testimonial.is_approved = not testimonial.is_approved
    testimonial.save(update_fields=["is_approved"])
    return redirect("testimonials:dashboard_list")