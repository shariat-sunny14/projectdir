import json
import os
from django.conf import settings
from organizations.models import organizationlst


def save_org_list_json_for_user(user):
    if user.is_superuser:
        org_qs = organizationlst.objects.filter(is_active=True)
    elif user.org_id is not None:
        org_qs = organizationlst.objects.filter(is_active=True, org_id=user.org_id)
    else:
        org_qs = []

    org_list = []

    for org in org_qs:
        org_list.append({
            "org_id": org.org_id,
            "org_name": org.org_name
        })

    # Save as JSON with key 'org_access'
    save_path = os.path.join(settings.BASE_DIR, 'user_org_list')
    os.makedirs(save_path, exist_ok=True)

    file_path = os.path.join(save_path, f'user_{user.user_id}_orgs.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({"org_access": org_list}, f, ensure_ascii=False, indent=4)
        