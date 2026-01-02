import os
import django
from datetime import datetime, date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auditbrain.settings")
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth import get_user_model
from reports.views import EventSummaryView

User = get_user_model()
user = User.objects.filter(is_superuser=True).first() or User.objects.first()

factory = APIRequestFactory()

def test_date_filter(params, label):
    request = factory.get('/api/reports/events/summary/', params)
    force_authenticate(request, user=user)
    view = EventSummaryView.as_view()
    response = view(request)
    print(f"--- {label} ---")
    print(f"Params: {params}")
    if response.status_code == 200:
        print(f"Status: {response.status_code}")
        print(f"Total events in response: {response.data.get('total_events')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.data)
    print()

# Test with YYYY-MM-DD format
test_date_filter({'start_date': '2026-01-02', 'end_date': '2026-01-31'}, "Testing YYYY-MM-DD format")
# Test without filters (default 30 days)
test_date_filter({}, "Testing default (no filters)")
