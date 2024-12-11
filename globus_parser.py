import asyncio
from bs4 import BeautifulSoup
import utils
import random
import lxml

url = 'https://www.globus.ru'

# id и имена магазинов. Например: [[77, '^%^D0^%^A2^%^D1^%^83^%^D0^%^BB^%^D0^%^B0']]
stores_id = [
    [],
]

# Акции
promotions_uri = '/promo/'

# Список любимых товаров. Например: ['/cat/153/p/mango-egipet-4088772',]
products_uri = []

async def get_promotions_in_stores():
    find_promotions_in_stores = {}

    for store_id in stores_id:
        promos = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Cookie': f'globus_hyper_id={store_id[0]}; globus_hyper_name={store_id[1]}; globus_hyper_show_select=1'
        }
        # Кол-во повторов, чтобы получить html документ с акциями
        for i in range(utils.number_of_attempts):
            # Пауза между запросами
            sleep_time = round(random.uniform(utils.pause_between_requests_promos['begin'],
                                              utils.pause_between_requests_promos['end']), 2)
            print(f'засыпаю на {sleep_time} c.')
            await asyncio.sleep(sleep_time)
            html = await utils.get_html(url, promotions_uri, headers)
            if html:
                break
            else:
                # Пауза между попытками
                await asyncio.sleep(utils.pause_between_attempts_to_get_html)
        if html:
            soup = BeautifulSoup(html[0], 'lxml')
            try:
                actions_in_globus = soup.find('div', id='actions-in-globus').find(
                    'div', class_='js-carousel-adaptive').find_all('div', class_='block')
                for promo in actions_in_globus:
                    title_promo = await _get_title_promo(promo)
                    date_promo = await _get_date_promo(promo)
                    promo_discount_label = await _get_promo_discount_label(promo)
                    promo_url = await _get_promo_url(promo)
                    print(
                        f'[+] Акция {title_promo}. {promo_discount_label} c {date_promo}')
                    promos.append(
                        {
                            'title_promo': title_promo,
                            'promo_discount_label': promo_discount_label,
                            'date_promo': date_promo,
                            'url': promo_url,
                        }
                    )
            except:
                print(f"Не удалось прочитать акцию в магазине {store_id[0]}")
        find_promotions_in_stores[store_id[0]] = promos

    return find_promotions_in_stores


async def _get_promo_url(promo):
    try:
        promo_url = promo.find('a', class_='name').attr['href']
    except:
        promo_url = ''
    return promo_url


async def _get_promo_discount_label(promo):
    try:
        promo_discount_label = promo.find('span',
                                          class_='short-desc').getText(
            strip=True).replace('\u00A0', '')
    except:
        promo_discount_label = 'Процент скидки не найден.'
    return promo_discount_label


async def _get_date_promo(promo):
    try:
        date_promo = promo.find('span',
                                class_='time').getText(strip=True).replace(
            '\u00A0', '')
    except:
        date_promo = 'Срок акции не найден.'
    return date_promo


async def _get_title_promo(promo):
    try:
        title_promo = 'Акция: ' + promo.find('a', class_='name').getText(
            strip=True).replace('\u00A0', '') + '.'
    except:
        title_promo = 'Заголовок акции не найден.'
    return title_promo


async def get_products():
    find_products_in_stores = {}

    for store_id in stores_id:
        find_products_in_store = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Cookie': f'globus_hyper_id={store_id[0]}; globus_hyper_name={store_id[1]}; globus_hyper_show_select=1'
        }
        for product_uri in products_uri:
            # Кол-во повторов, чтобы получить html документ с товаром
            for i in range(utils.number_of_attempts):
                # Пауза между запросами
                sleep_time = round(random.uniform(utils.pause_between_requests_products['begin'],
                                                  utils.pause_between_requests_products['end']), 2)
                await asyncio.sleep(sleep_time)
                print(f'засыпаю на {sleep_time} c.')
                html = await utils.get_html(url, product_uri, headers)
                if html:
                    break
                else:
                    # Пауза между попытками
                    await asyncio.sleep(utils.pause_between_attempts_to_get_html)

            if html:
                enough = ''
                soup = BeautifulSoup(html[0], 'lxml')
                title_sku = await _get_title_sku(product_uri, soup, store_id)
                shop_addr = await _get_shop_addr(product_uri, soup, store_id)
                price_regular = await _get_price_regular(product_uri, soup,
                                                         store_id)
                price_primary = await _get_price_primary(product_uri, soup,
                                                         store_id)
                discount = await _get_discount(product_uri, soup, store_id)
                title_sku = await _get_duration_discount(product_uri, soup, store_id, title_sku)
                actual_price_date_substring = await _get_actual_price_date(soup, store_id)
                if actual_price_date_substring:
                    shop_addr += f'\n({actual_price_date_substring})'

                find_products_in_store.append(
                    {
                        'title_sku': title_sku,
                        'shop_addr': shop_addr,
                        'price_regular': price_regular,
                        'price_primary': price_primary,
                        'discount': discount,
                        'enough': enough,
                        'url': url + product_uri
                    }
                )
        find_products_in_stores[store_id[0]] = find_products_in_store
    return find_products_in_stores


async def _get_actual_price_date(soup, store_id):
    try:
        actual_price_date = soup.find('div',
                                      class_='catalog-detail__additional-text').get_text(
            strip=True).replace('\u00A0', '')
        actual_price_date_index_begin = actual_price_date.index(
            'Цены действительны')
        actual_price_date_substring = actual_price_date[
                                      actual_price_date_index_begin:actual_price_date_index_begin + 67]
    except:
        actual_price_date_substring = ''
        print(
            f"Не удалось прочитать на какую дату цены действительны в магазине {store_id[0]}")
    return actual_price_date_substring


async def _get_duration_discount(product_uri, soup, store_id, title_sku):
    try:
        duration_discount = soup.find('div',
                                      class_='catalog-detail__header-content').find(
            'div', class_='catalog-detail__header-desc-small').get_text(
            strip=True).replace('\u00A0', '')
        title_sku += f'\n{duration_discount}'
    except:
        duration_discount = ''
        print(
            f"Не удалось прочитать срок скидки {product_uri} в магазине {store_id[0]}")
    return title_sku


async def _get_discount(product_uri, soup, store_id):
    try:
        dic = {'\u00A0': '', '-': '', '%': ''}
        discount = int(utils.replace_all(soup.find('span', class_='sale--orang-mt').get_text(
            strip=True), dic))
        print(
            f'  -- Скидка {discount}')
    except:
        discount = ''
        print(
            f"Не удалось прочитать скидку для товара {product_uri} в магазине {store_id[0]}")
    return discount


async def _get_price_primary(product_uri, soup, store_id):
    try:
        price_primary = soup.find('span',
                                  class_='catalog-detail__item-price-actual-main').get_text(
            strip=True).replace('\u00A0', '')
        print(
            f'  -- Цена по карте: {price_primary}')
    except:
        price_primary = ''
        print(
            f"Не удалось прочитать цену со скидкой для товара {product_uri} в магазине {store_id[0]}")
    return price_primary


async def _get_price_regular(product_uri, soup, store_id):
    try:
        price_regular = soup.find('span',
                                  class_='catalog-detail__item-price-old-main').get_text(
            strip=True).replace('\u00A0', '')
        print(f'  -- Обычная цена {price_regular}:')
    except:
        price_regular = ''
        print(
            f"Не удалось прочитать обычную цену для товара {product_uri} в магазине {store_id[0]}")
    return price_regular


async def _get_shop_addr(product_uri, soup, store_id):
    try:
        shop_addr = soup.find('div',
                              class_='header__mobile-giper_title js-header__mobile-change-city-popup').get_text(
            strip=True)
        print(f'  -- В магазине глобус {shop_addr}:')
    except:
        shop_addr = 'Не удалось прочитать адрес магазина'
        print(
            f"Не удалось прочитать адрес для товара {product_uri} в магазине {store_id[0]}")
    return shop_addr


async def _get_title_sku(product_uri, soup, store_id):
    try:
        title_sku = soup.find('h1',
                              class_='catalog-detail__title-h1').getText(
            strip=True).replace('\u00A0', '')
        print(f'[+] Товар {title_sku}')
    except:
        title_sku = 'Не удалось прочитать наименование товара'
        print(
            f"Не удалось прочитать наименование товара {product_uri} в магазине лобус {store_id[0]}")
    return title_sku
