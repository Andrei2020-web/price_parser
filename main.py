import asyncio
import aiohttp
import datetime
import time
import json
import xlwt
import lenta_parser

pause_between_requests_products = {'begin': 5, 'end': 6}
pause_between_requests_promos = {'begin': 2, 'end': 3}
pause_between_attempts_to_get_html = 30
number_of_attempts = 3


async def get_html(url, product_uri, headers):
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url + product_uri,
                                         headers=headers)
            if response.status == 200:
                return await response.text()
            else:
                print(f'Не удалось выполнить запрос, ошибка {response.status}')
                return None
    except Exception as e:
        print(f'Не удалось получить html! {e}')


def _save_results_in_exl_file(products_in_stores, book, sheet, promotions_in_stores=[]):
    # Записываем результат в таблицу exl

    # Устанавливаем ширину столбца
    _set_column_width(sheet)

    # Устанавливаем перенос по словам, выравнивание
    alignment = _set_word_wrap()

    # ------------ШРИФТЫ------------------
    # Устанавливаем шрифт заголовков
    font_heading = _create_font(name='Arial Cyr', bold=True)

    # Создаём шрифт адреса магазина
    font_addres_store = _create_font(name='Arial Cyr', underline=True, italic=True)

    # Создаём шрифт для тела
    font_body = _create_font(name='Arial Cyr')

    # ------------ЗАЛИВКА------------------
    # Создаём цвет фона красный
    pattern_red = _create_background_color(colour=2)

    # Создаём цвет фона зелёный
    pattern_green = _create_background_color(colour=3)

    # Создаём цвет фона серый
    pattern_gray = _create_background_color(colour=22)

    # ------------СТИЛИ------------------
    # Создаём стиль для заголовков
    header_style = _create_style(font_heading, alignment=alignment)

    # Создаём стиль для адреса магазина
    style_addres_store = _create_style(font_addres_store)

    # Создаём стиль для тела без заливки
    style_body = _create_style(font_body, alignment=alignment)

    # Создаём стиль для тела красный
    style_body_red = _create_style(font_body, alignment=alignment, pattern=pattern_red)

    # Создаём стиль для тела зелёный
    style_body_green = _create_style(font_body, alignment=alignment, pattern=pattern_green)

    # Создаём стиль для тела серый
    style_body_gray = _create_style(font_body, alignment=alignment, pattern=pattern_gray)

    # Печатаем заголовки
    _print_headlines(sheet, header_style)

    row = 0
    for key, values in products_in_stores.items():
        row += 1
        # Печатаем адрес магазина
        sheet.write(row, 0, values[0]['shop_addr'], style_addres_store)
        # Печатаем акции магазина
        row = _print_promo_in_store(key, promotions_in_stores, row, sheet, style_addres_store)
        row = _print_products_in_store(row, sheet, style_body, style_body_gray,
                                       style_body_green, style_body_red, values)
        # Печатаем пустую строку
        sheet.write(row, 0, '', style_addres_store)
    book.save(f"Цены_в_магазинах_на_{datetime.date.today()}.xls")


def _print_products_in_store(row, sheet, style_body, style_body_gray,
                             style_body_green, style_body_red, values):
    net_v_nalichii = ['Товар закончился', 'Нет в наличии']
    for value in values:
        row += 1
        style = style_body
        if value['discount']:
            discount = int(value['discount'].replace('-', '').replace('%', ''))
            if 25 <= discount < 50:
                style = style_body_green
            if discount >= 50:
                style = style_body_red
        if value['enough'] in net_v_nalichii:
            style = style_body_gray
        # Название продукта в виде гиперссылки
        formula = 'HYPERLINK("' + value['url'] + '";"' + value['title_sku'] + '")'
        sheet.write(row, 1, xlwt.Formula(formula), style)
        sheet.write(row, 2, value['price_regular'], style)
        sheet.write(row, 3, value['price_primary'], style)
        sheet.write(row, 4, value['discount'], style)
        sheet.write(row, 5, value['enough'], style)
    return row


def _print_promo_in_store(key, promotions_in_stores, row, sheet, style_addres_store):
    if promotions_in_stores:
        row += 1
        sheet.write(row, 0, '', style_addres_store)
        row += 1
        sheet.write(row, 0, 'Акции в магазине:', style_addres_store)
        for promo in promotions_in_stores[key]:
            row += 1
            formula = 'HYPERLINK("' + promo['url'] + '";"' + promo['title_promo'] + ' ' + \
                      promo['promo_discount_label'] + ' c ' + promo['date_promo'] + '")'
            sheet.write(row, 0, xlwt.Formula(formula), style_addres_store)
        sheet.write(row, 0, '', style_addres_store)
    return row


def _set_column_width(sheet):
    # первое число - это количество символов, а 256 - это единица измерения
    sheet.col(0).width = 45 * 256
    sheet.col(1).width = 80 * 256
    sheet.col(2).width = 20 * 256
    sheet.col(3).width = 20 * 256
    sheet.col(4).width = 11 * 256
    sheet.col(5).width = 24 * 256


def _print_headlines(sheet, header_style):
    sheet.write(0, 0, 'Адрес магазина', header_style)
    sheet.write(0, 1, 'Наименование товара', header_style)
    sheet.write(0, 2, 'Обычная цена', header_style)
    sheet.write(0, 3, 'Цена по карте', header_style)
    sheet.write(0, 4, 'Скидка', header_style)
    sheet.write(0, 5, 'Наличие в магазине', header_style)


def _create_style(font, alignment=None, pattern=None):
    style = xlwt.XFStyle()
    style.font = font
    if alignment:
        style.alignment = alignment
    if pattern:
        style.pattern = pattern
    return style


def _create_background_color(colour=1):
    pattern = xlwt.Pattern()
    # Установить режим цвета фона
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    # фоновый цвет
    pattern.pattern_fore_colour = colour
    return pattern


def _create_font(name='', bold=False, height=20 * 14, underline=False, italic=False):
    font = xlwt.Font()
    font.name = name
    font.bold = bold
    font.height = height
    font.underline = underline
    font.italic = italic  # курсив
    return font


def _set_word_wrap():
    alignment = xlwt.Alignment()
    alignment.wrap = 1
    alignment.horz = xlwt.Alignment.HORZ_CENTER  # May be: HORZ_GENERAL, HORZ_LEFT, HORZ_CENTER, HORZ_RIGHT, HORZ_FILLED, HORZ_JUSTIFIED, HORZ_CENTER_ACROSS_SEL, HORZ_DISTRIBUTED
    alignment.vert = xlwt.Alignment.VERT_CENTER  # May be: VERT_TOP, VERT_CENTER, VERT_BOTTOM, VERT_JUSTIFIED, VERT_DISTRIBUTED
    return alignment


def _save_promotions_in_json(promotions_in_stores, name_store):
    with open(f'promotions_in_stores_{name_store}_{datetime.date.today()}.json',
              'w') as file:
        json.dump(promotions_in_stores, file, indent=4, ensure_ascii=False)


def _save_products_in_json(products_in_stores, name_store):
    with open(f'products_in_stores_{name_store}_{datetime.date.today()}.json',
              'w') as file:
        json.dump(products_in_stores, file, indent=4, ensure_ascii=False)


def _create_workbook():
    return xlwt.Workbook(encoding="utf-8")


def _create_sheet(workbook, stores_name=''):
    return workbook.add_sheet(
        f'{stores_name}', cell_overwrite_ok=True)


async def main():
    start_time = time.time()

    workbook = _create_workbook()

    tasks = [asyncio.create_task(_) for _ in [
        lenta_parser.get_promotions_in_stores(),
        lenta_parser.get_products()
    ]
             ]

    results = await asyncio.gather(*tasks)

    # --------------Лента-----------------
    sheetLenta = _create_sheet(workbook, 'Лента')
    _save_promotions_in_json(results[0], 'lenta')
    _save_products_in_json(results[1], 'lenta')
    _save_results_in_exl_file(results[1], book=workbook, sheet=sheetLenta,
                              promotions_in_stores=results[0])

    finish_time = time.time()
    print(f'Программа завершена за {finish_time - start_time} c.')


if __name__ == '__main__':
    asyncio.run(main())
