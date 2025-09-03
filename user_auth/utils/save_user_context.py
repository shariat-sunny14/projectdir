import json
import os
from django.conf import settings
from organizations.models import organizationlst, branchslist  # Adjust the import path if needed

def save_user_context_to_json(user):
    if not user.is_authenticated:
        return

    data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "designation": getattr(user, 'designation', ""),
        "profile_img": user.profile_img.url if getattr(user, 'profile_img', None) else "",
        "org_name": "",
        "org_address": "",
        "branch_name": "",
        "branch_address": ""
    }

    if user.org_id:
        try:
            org = organizationlst.objects.get(org_id=user.org_id)
            data["org_name"] = org.org_name
            data["org_address"] = org.address
        except organizationlst.DoesNotExist:
            pass

    if user.branch_id:
        try:
            branch = branchslist.objects.get(branch_id=user.branch_id)
            data["branch_name"] = branch.branch_name
            data["branch_address"] = branch.address
        except branchslist.DoesNotExist:
            pass

    # Ensure directory exists
    save_path = os.path.join(settings.BASE_DIR, 'user_context_data')
    os.makedirs(save_path, exist_ok=True)

    # Save with user ID
    file_path = os.path.join(save_path, f'user_context_{user.user_id}.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
