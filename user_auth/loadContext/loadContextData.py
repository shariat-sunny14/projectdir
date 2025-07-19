import os
import json
from django.conf import settings

def load_navbar_context_from_json(request):
    if not request.user.is_authenticated:
        return {}

    json_path = os.path.join(settings.BASE_DIR, 'user_nav_data', f'user_navbar_{request.user.user_id}.json')

    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                grouped_data = json.load(file)
                return {'grouped_data': grouped_data}
        except json.JSONDecodeError:
            return {'grouped_data': {}}

    return {'grouped_data': {}}


def load_user_context_from_json(request):
    if not request.user.is_authenticated:
        return {}

    user_id = getattr(request.user, 'user_id', None)
    if not user_id:
        return {}

    file_path = os.path.join(settings.BASE_DIR, 'user_context_data', f'user_context_{user_id}.json')
    
    # Default values
    context_data = {
        'user_org_name': 'Org Name Not Found',
        'user_org_address': 'Address Not Found',
        'user_branch_name': 'Branch Name Not Found',
        'user_branch_address': 'Address Not Found',  # <-- default if missing or empty
        'user_first_name': 'User Not Found',
        'user_last_name': '',
        'user_designation': 'Des. Not Found',
        'user_profile_img': ''
    }

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)

                # Fallback if key missing or empty
                context_data['user_org_name'] = data.get("org_name") or 'Org Name Not Found'
                context_data['user_org_address'] = data.get("org_address") or 'Address Not Found'
                context_data['user_branch_name'] = data.get("branch_name") or 'Branch Name Not Found'
                context_data['user_branch_address'] = data.get("branch_address") or 'Address Not Found'
                context_data['user_first_name'] = data.get("first_name") or 'User Not Found'
                context_data['user_last_name'] = data.get("last_name") or ''
                context_data['user_designation'] = data.get("designation") or 'Des. Not Found'
                context_data['user_profile_img'] = data.get("profile_img") or ''
                
            except json.JSONDecodeError:
                pass

    return context_data