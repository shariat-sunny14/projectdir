from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import TeamMember, Award, Certificate, AboutUs, LifeAtOur
from .forms import (
    TeamForm, AwardForm, CertificateForm,
    AboutUsForm, LifeAtOurForm
)


# ===================== MAIN PAGE =====================
@login_required()
def about_page(request):
    context = {
        'about': AboutUs.objects.last(),  # only latest
        'life': LifeAtOur.objects.last(),
        'team': TeamMember.objects.all().order_by('-id'),
        'awards': Award.objects.all().order_by('-id'),
        'certificates': Certificate.objects.all().order_by('-id'),
    }
    return render(request, 'about_us/about.html', context)


# ===================== ABOUT US =====================
@login_required()
def about_add(request):
    form = AboutUsForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('about')

    return render(request, 'about_us/form.html', {'form': form, 'title': 'Add About Us'})

@login_required()
def about_edit(request, pk):
    obj = get_object_or_404(AboutUs, pk=pk)
    form = AboutUsForm(request.POST or None, instance=obj)

    if form.is_valid():
        form.save()
        return redirect('about')

    return render(request, 'about_us/form.html', {'form': form, 'title': 'Edit About Us'})

@login_required()
def about_delete(request, pk):
    get_object_or_404(AboutUs, pk=pk).delete()
    return redirect('about')


# ===================== LIFE AT OUR =====================
@login_required()
def life_add(request):
    form = LifeAtOurForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('about')

    return render(request, 'about_us/form.html', {'form': form, 'title': 'Add LifeAtOur'})

@login_required()
def life_edit(request, pk):
    obj = get_object_or_404(LifeAtOur, pk=pk)
    form = LifeAtOurForm(request.POST or None, instance=obj)

    if form.is_valid():
        form.save()
        return redirect('about')

    return render(request, 'about_us/form.html', {'form': form, 'title': 'Edit LifeAtOur'})

@login_required()
def life_delete(request, pk):
    get_object_or_404(LifeAtOur, pk=pk).delete()
    return redirect('about')


# ===================== TEAM =====================
@login_required()
def team_add(request):
    form = TeamForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('about')
    return render(request, 'about_us/form.html', {'form': form, 'title': 'Add Team'})

@login_required()
def team_edit(request, pk):
    obj = get_object_or_404(TeamMember, pk=pk)
    form = TeamForm(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save()
        return redirect('about')
    return render(request, 'about_us/form.html', {'form': form, 'title': 'Edit Team'})

@login_required()
def team_delete(request, pk):
    get_object_or_404(TeamMember, pk=pk).delete()
    return redirect('about')


# ===================== AWARD =====================
@login_required()
def award_add(request):
    form = AwardForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('about')
    return render(request, 'about_us/form.html', {'form': form, 'title': 'Add Award'})

@login_required()
def award_edit(request, pk):
    obj = get_object_or_404(Award, pk=pk)
    form = AwardForm(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save()
        return redirect('about')
    return render(request, 'about_us/form.html', {'form': form, 'title': 'Edit Award'})

@login_required()
def award_delete(request, pk):
    get_object_or_404(Award, pk=pk).delete()
    return redirect('about')


# ===================== CERTIFICATE =====================
@login_required()
def certificate_add(request):
    form = CertificateForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('about')
    return render(request, 'about_us/form.html', {'form': form, 'title': 'Add Certificate'})

@login_required()
def certificate_edit(request, pk):
    obj = get_object_or_404(Certificate, pk=pk)
    form = CertificateForm(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save()
        return redirect('about')
    return render(request, 'about_us/form.html', {'form': form, 'title': 'Edit Certificate'})

@login_required()
def certificate_delete(request, pk):
    get_object_or_404(Certificate, pk=pk).delete()
    return redirect('about')