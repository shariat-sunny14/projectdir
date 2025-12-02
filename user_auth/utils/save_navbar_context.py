import json
import os
from django.conf import settings
from module_setup.models import module_list, module_type, feature_list
from user_setup.models import access_list


def save_navbar_json_for_user(user):
    grouped_data = {}
    active_modules = module_list.objects.filter(is_active=True)
    active_types = module_type.objects.filter(is_active=True)
    access_data = access_list.objects.filter(user_id=user)

    for access_item in access_data:
        feature = access_item.feature_id
        if not (feature and feature.is_active and feature.feature_type == "Form"):
            continue

        module = feature.module_id
        type_ = feature.type_id

        if module_id := module.module_id:
            if module_id not in grouped_data:
                grouped_data[module_id] = {
                    'module_name': module.module_name,
                    'types': {}
                }

            if type_name := type_.type_name:
                if type_name not in grouped_data[module_id]['types']:
                    grouped_data[module_id]['types'][type_name] = {
                        'type_icon': type_.type_icon,
                        'features': []
                    }

                grouped_data[module_id]['types'][type_name]['features'].append({
                    'feature_page_link': feature.feature_page_link,
                    'feature_icon': feature.feature_icon,
                    'feature_name': feature.feature_name
                })

    # Remove types with no features
    for module_id in list(grouped_data):
        grouped_data[module_id]['types'] = {
            k: v for k, v in grouped_data[module_id]['types'].items() if v['features']
        }

    # Save to JSON
    save_path = os.path.join(settings.BASE_DIR, 'user_nav_data')
    os.makedirs(save_path, exist_ok=True)
    file_path = os.path.join(save_path, f'user_navbar_{user.user_id}.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(grouped_data, f, ensure_ascii=False, indent=4)