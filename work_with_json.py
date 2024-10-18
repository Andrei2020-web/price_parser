import json
import datetime


def save_promotions_in_json(promotions_in_stores, name_store):
    with open(f'promotions_in_stores_{name_store}_{datetime.date.today()}.json',
              'w') as file:
        json.dump(promotions_in_stores, file, indent=4, ensure_ascii=False)


def save_products_in_json(products_in_stores, name_store):
    with open(f'products_in_stores_{name_store}_{datetime.date.today()}.json',
              'w') as file:
        json.dump(products_in_stores, file, indent=4, ensure_ascii=False)
