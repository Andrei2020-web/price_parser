import asyncio
import time
import lenta_parser
import perekrestok_parser
import globus_parser
import sahalin_ryba_parser
import alenka_parser
import spar_parser
import pyaterochka_parser
import work_with_exl
import work_with_json


async def main():
    start_time = time.time()

    workbook = work_with_exl.create_workbook()

    tasks = [asyncio.create_task(_) for _ in [
        lenta_parser.get_products(),
        perekrestok_parser.get_products(),
        globus_parser.get_promotions_in_stores(),
        globus_parser.get_products(),
        sahalin_ryba_parser.get_products(),
        alenka_parser.get_products(),
        spar_parser.get_products(),
        pyaterochka_parser.get_products(),
    ]
             ]

    results = await asyncio.gather(*tasks)

    # --------------Лента-----------------
    sheetLenta = work_with_exl.create_sheet(workbook, 'Лента')
    work_with_exl.freeze_the_cell(sheetLenta, 1)
    work_with_json.save_products_in_json(results[0], 'lenta')
    work_with_exl.save_results_in_exl_file(results[0], book=workbook, sheet=sheetLenta)

    # --------------Перекрёсток-----------------
    sheetPerekrestok = work_with_exl.create_sheet(workbook, 'Перекрёсток')
    work_with_exl.freeze_the_cell(sheetPerekrestok, 1)
    work_with_json.save_products_in_json(results[1], 'perekrestok')
    work_with_exl.save_results_in_exl_file(results[1], book=workbook, sheet=sheetPerekrestok)

    # --------------Глобус-----------------
    sheet_globus = work_with_exl.create_sheet(workbook, 'Глобус')
    work_with_exl.freeze_the_cell(sheet_globus, 1)
    work_with_json.save_promotions_in_json(results[2], 'globus')
    work_with_json.save_products_in_json(results[3], 'globus')
    work_with_exl.save_results_in_exl_file(results[3], book=workbook, sheet=sheet_globus,
                                            promotions_in_stores=results[2])

    # --------------Сахалин рыба-----------------
    sheet_sahalin_ryba = work_with_exl.create_sheet(workbook, 'Сахалин рыба')
    work_with_exl.freeze_the_cell(sheet_sahalin_ryba, 1)
    work_with_json.save_products_in_json(results[4], 'sahalin_ryba')
    work_with_exl.save_results_in_exl_file(results[4], book=workbook, sheet=sheet_sahalin_ryba)

    # --------------Алёнка-----------------
    sheet_alenka = work_with_exl.create_sheet(workbook, 'Алёнка')
    work_with_exl.freeze_the_cell(sheet_alenka, 1)
    work_with_json.save_products_in_json(results[5], 'alenka')
    work_with_exl.save_results_in_exl_file(results[5], book=workbook, sheet=sheet_alenka)

    # --------------Спар-----------------
    sheet_spar = work_with_exl.create_sheet(workbook, 'Спар')
    work_with_exl.freeze_the_cell(sheet_spar, 1)
    work_with_json.save_products_in_json(results[6], 'spar')
    work_with_exl.save_results_in_exl_file(results[6], book=workbook, sheet=sheet_spar)

    # --------------Пятёрочка-----------------
    sheet_pyaterochka = work_with_exl.create_sheet(workbook, 'Пятёрочка')
    work_with_exl.freeze_the_cell(sheet_pyaterochka, 1)
    work_with_json.save_products_in_json(results[7], 'pyaterochka')
    work_with_exl.save_results_in_exl_file(results[7], book=workbook, sheet=sheet_pyaterochka)

    finish_time = time.time()
    print(f'Программа завершена за {round((finish_time - start_time) / 60, 2)} минут.')


if __name__ == '__main__':
    asyncio.run(main())
