import json
import os
from django.conf import settings
from user_setup.models import others_access_list
from django.http import JsonResponse

def save_othersaccess_json_for_user(user):
    access_data = others_access_list.objects.filter(user_id=user, is_active=True)

    data = {
        "class_access": [],
        "section_access": [],
        "shift_access": [],
        "group_access": []
    }

    for access in access_data:
        if access.class_id:
            data["class_access"].append({
                "class_id": access.class_id.class_id,
                "class_name": access.class_id.class_name,
                "allow_groups": access.class_id.allow_groups,
                "is_defaults": access.is_defaults
            })
        if access.section_id:
            data["section_access"].append({
                "section_id": access.section_id.section_id,
                "section_name": access.section_id.section_name,
                "is_defaults": access.is_defaults
            })
        if access.shifts_id:
            data["shift_access"].append({
                "shift_id": access.shifts_id.shift_id,
                "shift_name": access.shifts_id.shift_name,
                "is_defaults": access.is_defaults
            })
        if access.groups_id:
            data["group_access"].append({
                "groups_id": access.groups_id.groups_id,
                "groups_name": access.groups_id.groups_name,
                "is_defaults": access.is_defaults
            })

    # Ensure directory exists
    save_path = os.path.join(settings.BASE_DIR, 'user_others_access')
    os.makedirs(save_path, exist_ok=True)

    # Save with user ID
    file_path = os.path.join(save_path, f'user_{user.user_id}_access.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)