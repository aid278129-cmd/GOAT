import json

with open('data/bis_dataset/real_bis_standards.json', 'r', encoding='utf-8') as f:
    standards = json.load(f)

print(f"Total standards: {len(standards)}")
for idx, s in enumerate(standards, 1):
    std_num = s.get('standard_number')
    title = s.get('title')
    qco = s.get('qco_orders', [])
    qco_name = qco[0].get('qco_title', 'No QCO') if qco else 'No QCO'
    print(f"{idx}. {std_num} - {title} | QCO: {qco_name}")
