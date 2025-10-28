import os
import json
import random
from django.conf import settings
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from item_setup.models import item_supplierdtl, items
from stock_list.models import in_stock, stock_lists
from organizations.models import organizationlst
from store_setup.models import store
from django.contrib.auth import get_user_model
User = get_user_model()


def save_stock_zero_data_context_to_json(user):
    org_instance = organizationlst.objects.filter(is_active=True, org_id=user.org_id).first()
    stock_data = in_stock.objects.select_related('item_id', 'store_id').all()

    low_stock_items = []

    for stock in stock_data:
        item_details = stock.item_id
        store_data = stock.store_id

        if item_details and item_details.org_id == org_instance:
            total_stockQty = stock.stock_qty

            if item_details.re_order_qty and total_stockQty < float(item_details.re_order_qty):
                serialized_item = {
                    'item_name': item_details.item_name,
                    'store_name': store_data.store_name if store_data else '',
                    'total_stockQty': total_stockQty,
                }
                low_stock_items.append(serialized_item)

    random.shuffle(low_stock_items)

    # Save to JSON file
    try:
        folder_path = os.path.join(settings.BASE_DIR, 'stock_zero_data')
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, 'stock_zero_data_{user.user_id}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'alert_data': low_stock_items}, f, ensure_ascii=False, indent=4)

        print("Stock zero data saved to JSON.")
    except Exception as e:
        print("Error saving stock zero data JSON:", e)