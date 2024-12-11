import datetime
import xlwt


def save_results_in_exl_file(products_in_stores, book, sheet, promotions_in_stores=[]):
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
        if values:
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
    net_v_nalichii = ['Нет в наличии', 'В наличии 0 шт', 'В наличии 0.0 кг', 'Нет в магазине',
                      'Товар раскупили']
    for value in values:
        row += 1
        style = style_body
        if value['discount']:
            discount = value['discount']
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
    sheet.write(0, 4, 'Скидка, %', header_style)
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


def create_workbook():
    return xlwt.Workbook(encoding="utf-8")


def create_sheet(workbook, stores_name=''):
    return workbook.add_sheet(
        f'{stores_name}', cell_overwrite_ok=True)


def freeze_the_cell(sheet, cell_position):
    sheet.set_horz_split_pos(cell_position)
    sheet.panes_frozen = True
    sheet.remove_splits = True
