import json
import os
import calendar
from django.conf import settings
from datetime import date, datetime, timedelta
from django.http import JsonResponse
from organizations.models import organizationlst
from user_setup.models import serviceChargePayment

MONTHS_LIST = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december'
]


def save_org_service_charge_to_json(user):
    if not user.is_authenticated:
        return

    if user.org_id is not None:
        org = organizationlst.objects.get(is_active=True, org_id=user.org_id)

        # Basic data
        is_start_up = org.is_start_up
        service_charge = org.service_charge or 0
        is_alert_start = org.is_alert_start or 1
        is_alert_end = org.is_alert_end or 1
        today = date.today()

        # Alert period dates
        current_year, current_month = today.year, today.month
        alert_start_date = date(current_year, current_month, min(
            is_alert_start, calendar.monthrange(current_year, current_month)[1]))
        if current_month == 12:
            next_month, next_year = 1, current_year + 1
        else:
            next_month, next_year = current_month + 1, current_year
        alert_end_date = date(next_year, next_month, min(
            is_alert_end, calendar.monthrange(next_year, next_month)[1]))

        # --- Remaining days between now and alert_end_date ---
        remaining_alert_days = 0
        if today <= alert_end_date:
            remaining_alert_days = (alert_end_date - today).days

        # Initialize due_amount
        total_months = 0
        paid_months = set()
        unpaid_months = []

        if is_start_up:
            # Get all months from is_start_up to today (inclusive)
            current_pointer = date(is_start_up.year, is_start_up.month, 1)
            last_pointer = date(today.year, today.month, 1)

            all_months = []
            while current_pointer <= last_pointer:
                y = current_pointer.year
                m = current_pointer.month
                all_months.append((y, MONTHS_LIST[m - 1]))
                if m == 12:
                    current_pointer = date(y + 1, 1, 1)
                else:
                    current_pointer = date(y, m + 1, 1)

            total_months = len(all_months)

            # Get all paid months for this org
            paid_records = serviceChargePayment.objects.filter(
                org_id=org, is_approved=True)
            for p in paid_records:
                if p.service_year and p.service_month:
                    paid_months.add(
                        (int(p.service_year), p.service_month.lower().strip()))

            # Subtract paid from total
            unpaid_months = [m for m in all_months if m not in paid_months]
            due_amount = len(unpaid_months) * service_charge

        # Prepare data to return & save
        data = {
            'is_start_up': str(is_start_up) if is_start_up else None,
            'is_start_up_date': is_start_up.strftime("%d %B %Y" if is_start_up else None),
            'service_charge': service_charge,
            'is_alert_start': alert_start_date.strftime("%d %B %Y"),
            'alert_start_isoformat': alert_start_date.isoformat(),
            'is_alert_end': alert_end_date.strftime("%d %B %Y"),
            'alert_end_isoformat': alert_end_date.isoformat(),
            'remaining_alert_days': remaining_alert_days,
            'total_months': total_months,
            'paid_months': list(paid_months),
            'unpaid_months': unpaid_months,
            'due_amount': due_amount
        }

        # Save to JSON file
        save_path = os.path.join(settings.BASE_DIR, 'service_charge_data')
        os.makedirs(save_path, exist_ok=True)

        file_path = os.path.join(
            save_path, f'service_charge_{user.user_id}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
