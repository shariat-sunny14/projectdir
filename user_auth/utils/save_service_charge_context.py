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
        is_alert_start_day = org.is_alert_start or 1
        is_alert_end_day = org.is_alert_end or 1
        ser_char_alert = org.ser_char_alert
        today = date.today()

        # Setup alert dates (based on current and previous months)
        current_year, current_month = today.year, today.month

        # Previous month calculation
        if current_month == 1:
            prev_month, prev_year = 12, current_year - 1
        else:
            prev_month, prev_year = current_month - 1, current_year

        # Alert start = previous month, Alert end = current month
        alert_start_date = date(prev_year, prev_month, min(
            is_alert_start_day, calendar.monthrange(prev_year, prev_month)[1]))
        alert_end_date = date(current_year, current_month, min(
            is_alert_end_day, calendar.monthrange(current_year, current_month)[1]))

        # --- Remaining days until alert_end_date ---
        remaining_alert_days = max(0, (alert_end_date - today).days)

        # Initialize due_amount
        total_months = 0
        paid_months = set()
        unpaid_months = []
        due_amount = 0

        if is_start_up:
            # Calculate end of previous month
            first_of_current_month = date(today.year, today.month, 1)
            end_of_prev_month = first_of_current_month - timedelta(days=1)
            last_pointer = date(end_of_prev_month.year, end_of_prev_month.month, 1)

            # Get all months from is_start_up to end of previous month
            current_pointer = date(is_start_up.year, is_start_up.month, 1)
            all_months = []

            while current_pointer <= last_pointer:
                y = current_pointer.year
                m = current_pointer.month
                all_months.append((y, MONTHS_LIST[m - 1]))  # e.g. (2025, 'june')
                if m == 12:
                    current_pointer = date(y + 1, 1, 1)
                else:
                    current_pointer = date(y, m + 1, 1)

            total_months = len(all_months)

            # Get all approved paid months
            paid_records = serviceChargePayment.objects.filter(
                org_id=org, is_approved=True)
            for p in paid_records:
                if p.service_year and p.service_month:
                    paid_months.add(
                        (int(p.service_year), p.service_month.lower().strip()))

            unpaid_months = [m for m in all_months if m not in paid_months]
            due_amount = len(unpaid_months) * service_charge
            paid_amount = len(paid_months) * service_charge
            balance_amt = paid_amount - due_amount

        # Prepare data to return & save
        data = {
            'ser_char_alert': ser_char_alert,
            'is_start_up': str(is_start_up) if is_start_up else None,
            'is_start_up_date': is_start_up.strftime("%d %B %Y") if is_start_up else None,
            'service_charge': service_charge,
            'is_alert_start': alert_start_date.strftime("%d %B %Y"),
            'alert_start_isoformat': alert_start_date.isoformat(),
            'is_alert_end': alert_end_date.strftime("%d %B %Y"),
            'alert_end_isoformat': alert_end_date.isoformat(),
            'remaining_alert_days': remaining_alert_days,
            'total_months': total_months,
            'paid_months': list(paid_months),
            'unpaid_months': unpaid_months,
            'paid_amount': paid_amount,
            'due_amount': due_amount,
            'balance_amt': balance_amt,
        }

        # Save to JSON file
        save_path = os.path.join(settings.BASE_DIR, 'service_charge_data')
        os.makedirs(save_path, exist_ok=True)

        file_path = os.path.join(
            save_path, f'service_charge_{user.user_id}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
