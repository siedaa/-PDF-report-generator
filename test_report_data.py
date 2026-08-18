import json

from report_data import get_report_data

print(json.dumps(get_report_data(), indent=2))
