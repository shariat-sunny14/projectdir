from django.shortcuts import render, redirect, get_object_or_404
from .models import YouTubeVideo
from .forms import YouTubeVideoForm
from django.contrib.auth.decorators import login_required


# LIST
@login_required()
def video_list(request):
    videos = YouTubeVideo.objects.all().order_by('-id')
    return render(request, 'youtube/video_list.html', {'videos': videos})


# ADD
@login_required()
def video_add(request):
    form = YouTubeVideoForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect('video_list')

    return render(request, 'youtube/video_form.html', {'form': form})


# EDIT
@login_required()
def video_edit(request, pk):
    video = get_object_or_404(YouTubeVideo, pk=pk)
    form = YouTubeVideoForm(request.POST or None, instance=video)

    if form.is_valid():
        form.save()
        return redirect('video_list')

    return render(request, 'youtube/video_form.html', {'form': form})


# DELETE
@login_required()
def video_delete(request, pk):
    video = get_object_or_404(YouTubeVideo, pk=pk)
    video.delete()
    return redirect('video_list')