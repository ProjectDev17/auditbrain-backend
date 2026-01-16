
import os
import django
import sys
from datetime import date, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auditbrain.settings")
django.setup()

from audits.models import Audit
from mcp.audit_tools import list_audits, get_audit_statistics

def test_filtering():
    print("="*60)
    print("TESTING MCP TOOL FILTERING")
    print("="*60)
    
    # Setup data
    today = date.today()
    Audit.objects.all().delete()
    
    a1 = Audit.objects.create(title="Audit 2026 A", status="pending", start_date="2026-01-01")
    a2 = Audit.objects.create(title="Audit 2026 B", status="completed", start_date="2026-06-01")
    a3 = Audit.objects.create(title="Audit 2025", status="completed", start_date="2025-12-01")
    
    print(f"Created 3 audits. IDs: {a1.id}, {a2.id}, {a3.id}")
    
    # 1. Test get_audit_statistics
    print("\n1. Testing get_audit_statistics (2026)...")
    stats = get_audit_statistics({
        "start_date": "2026-01-01", 
        "end_date": "2026-12-31"
    }, context={})
    
    print(f"Stats Result: {stats}")
    
    if stats['total'] == 2 and stats['by_status'].get('completed') == 1:
        print("✓ PASS: Stats filtered correctly")
    else:
        print(f"✗ FAIL: Expected total 2, got {stats['total']}")
        
    # 2. Test list_audits Date Filter
    print("\n2. Testing list_audits (start_date=2026-01-01)...")
    res = list_audits({"start_date": "2026-01-01"}, context={})
    titles = [a['title'] for a in res['audits']]
    print(f"Result titles: {titles}")
    
    if len(titles) == 2 and "Audit 2025" not in titles:
        print("✓ PASS: List filtered by date correctly")
    else:
        print("✗ FAIL: Date filter incorrect")
        
    # 3. Test list_audits Search
    print("\n3. Testing list_audits (search='2025')...")
    res = list_audits({"search": "2025"}, context={})
    titles = [a['title'] for a in res['audits']]
    print(f"Result titles: {titles}")
    
    if len(titles) == 1 and titles[0] == "Audit 2025":
        print("✓ PASS: Search worked")
    else:
        print("✗ FAIL: Search incorrect")

    print("\nDONE")

if __name__ == "__main__":
    test_filtering()
