import os
import json
import datetime
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from module_setup.models import feature_list
from django.contrib.auth.decorators import login_required


def export_voice_commands():
    features = feature_list.objects.filter(feature_type="Form", is_active=True)
    data = []

    for f in features:
        if f.command_name:
            data.append({
                "command_name": f.command_name.strip().lower(),
                "feature_page_link": f.feature_page_link
            })

    # ✅ Write to static directory
    static_dir = os.path.join(settings.BASE_DIR, 'static', 'jarvis_assistant')
    os.makedirs(static_dir, exist_ok=True)  # Ensure folder exists

    json_path = os.path.join(static_dir, 'voice_commands.json')
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ voice_commands.json exported to static folder.")


@login_required()
def process_command(request):
    command = request.GET.get('command', '').lower()
    print("🟢 Received Command from JS:", command)  # Add this
    response = "Sorry, I didn’t understand."

    if "hello" in command or "hi" in command:
        response = "Hi! I am Jarvis, your assistant."
        return JsonResponse({'response': response})

    elif "time" in command:
        response = datetime.datetime.now().strftime("It’s %I:%M %p")
        return JsonResponse({'response': response})

    json_path = os.path.join(settings.BASE_DIR, 'jarvis_assistant', 'voice_commands.json')

    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            commands = json.load(file)

        for item in commands:
            json_command = item['command_name'].strip().lower()
            print(f"🔍 Matching: '{json_command}' in '{command}'")  # Debug log

            if json_command in command:
                response = f"Redirecting to {item['command_name'].title()} page."
                return JsonResponse({
                    'response': response,
                    'redirect_url': item['feature_page_link']
                })

    except Exception as e:
        response = f"Error loading commands: {str(e)}"
        print("❌ ERROR:", e)

    return JsonResponse({'response': response})