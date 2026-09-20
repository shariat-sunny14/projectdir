# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import WhoWeAre
from .forms import WhoWeAreForm, StatCardFormSet


def who_we_are_view(request):
    """Public facing view — ei view diye about section render hobe."""
    about = WhoWeAre.load()
    stats = about.stats.all()
    context = {
        "about": about,
        "stats": stats,
    }
    return render(request, "who_we_are/who_we_are.html", context)


@login_required
def who_we_are_edit_view(request):
    """
    Django admin chhara nijer moto ekta simple edit page.
    login_required diye already protect kora hoyeche.
    """
    about = WhoWeAre.load()

    if request.method == "POST":
        form = WhoWeAreForm(request.POST, instance=about)
        formset = StatCardFormSet(request.POST, instance=about)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("who_we_are:who_we_are_edit")
    else:
        form = WhoWeAreForm(instance=about)
        formset = StatCardFormSet(instance=about)

    return render(
        request,
        "who_we_are/who_we_are_edit.html",
        {"form": form, "formset": formset},
    )