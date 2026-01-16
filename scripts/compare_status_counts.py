
import os
import sys
# Add project root to sys.path
sys.path.append("c:/WORK/AUDIBRAIN/auditbrain-backend")

import django
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auditbrain.settings")
django.setup()

from reports.services import get_audit_summary
from mcp.audit_tools import get_audit_statistics

def compare_counts():
    start_date = "2025-01-01"
    end_date = "2025-12-31"
    
    # Reports Service (using dictionary filter)
    filters = {'start_date': start_date, 'end_date': end_date}
    report_data = get_audit_summary(filters)
    
    # MCP Tool (using start_date/end_date params)
    mcp_params = {'start_date': start_date, 'end_date': end_date}
    mcp_data = get_audit_statistics(mcp_params, {})
    
    print("\n--- COMPARISON 2025 ---")
    print(f"Reports Total: {report_data['total']}")
    print(f"MCP Total:     {mcp_data['total']}")
    
    print("\n--- BY STATUS (Reports) ---")
    for k, v in report_data['by_status'].items():
        print(f"{k}: {v}")
        
    print("\n--- BY STATUS (MCP) ---")
    for k, v in mcp_data['by_status'].items():
        print(f"{k}: {v}")

    print("\n--- RAW DB DEBUG ---")
    from audits.models import Audit
    qs = Audit.objects.filter(start_date__gte=start_date, start_date__lte=end_date, deleted=False)
    print(f"Raw Count: {qs.count()}")
    from django.db.models import Count
    print(qs.values('status').annotate(c=Count('id')))

if __name__ == "__main__":
    compare_counts()
