import json
import os
from django.conf import settings
from organizations.models import branchslist


def save_branch_list_json_for_user(user, org_id=None):
    if user.is_staff and org_id:
        branch_qs = branchslist.objects.filter(is_active=True, org_id=org_id)
    elif user.branch_id:
        branch_qs = branchslist.objects.filter(is_active=True, branch_id=user.branch_id)
    else:
        branch_qs = []

    branch_list = []
    for branch in branch_qs:
        branch_list.append({
            "branch_id": branch.branch_id,
            "branch_name": branch.branch_name
        })

    # Save to JSON
    save_dir = os.path.join(settings.BASE_DIR, 'user_branch_list')
    os.makedirs(save_dir, exist_ok=True)

    file_path = os.path.join(save_dir, f'user_{user.user_id}_branches.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({"branch_access": branch_list}, f, ensure_ascii=False, indent=4)

    return file_path