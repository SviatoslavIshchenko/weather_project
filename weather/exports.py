
import csv
from io import BytesIO

from django.http import HttpResponse
from django.db.models import Count, Avg, Min, Max
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


def get_city_statistics(searches):
    return (
        searches.values("city")
        .annotate(
            count=Count("id"),
            avg_temp=Avg("temperature"),
            min_temp=Min("temperature"),
            max_temp=Max("temperature"),
        )
        .order_by("city")
    )


def export_csv(searches):
    response = HttpResponse(
        content_type="text/csv; charset=utf-8"
    )
    response["Content-Disposition"] = (
        'attachment; filename="weather_history.csv"'
    )

    # BOM для коректного відкриття кирилиці в Excel
    response.write("\ufeff")

    writer = csv.writer(response, delimiter=";")

    writer.writerow([
        "Місто",
        "Температура",
        "Вологість",
        "Відчувається як",
        "Вітер",
        "Тиск",
        "Опис погоди",
        "Дата пошуку",
    ])

    for item in searches:
        writer.writerow([
            item.city,
            item.temperature,
            item.humidity,
            item.feels_like,
            item.wind_speed,
            item.pressure,
            item.description,
            timezone.localtime(item.search_date).strftime(
                "%d.%m.%Y %H:%M"
            ),
        ])

    return response


def export_excel(searches):
    workbook = Workbook()

    sheet = workbook.active
    sheet.title = "Історія пошуків"

    sheet.append([
        "Місто",
        "Температура",
        "Вологість",
        "Відчувається як",
        "Вітер",
        "Тиск",
        "Опис погоди",
        "Дата пошуку",
    ])

    for item in searches:
        sheet.append([
            item.city,
            item.temperature,
            item.humidity,
            item.feels_like,
            item.wind_speed,
            item.pressure,
            item.description,
            timezone.localtime(item.search_date).strftime(
                "%d.%m.%Y %H:%M"
            ),
        ])

    stats_sheet = workbook.create_sheet("Статистика міст")

    stats_sheet.append([
        "Місто",
        "Кількість пошуків",
        "Середня температура",
        "Мінімальна температура",
        "Максимальна температура",
    ])

    for stat in get_city_statistics(searches):
        stats_sheet.append([
            stat["city"],
            stat["count"],
            round(stat["avg_temp"], 2)
            if stat["avg_temp"] is not None else None,
            stat["min_temp"],
            stat["max_temp"],
        ])

    # Оформлення таблиць
    for ws in workbook.worksheets:
        for cell in ws[1]:
            cell.font = Font(color="FFFFFF", bold=True)
            cell.fill = PatternFill(
                start_color="2563EB",
                end_color="2563EB",
                fill_type="solid",
            )

        ws.freeze_panes = "A2"

        for column in ws.columns:
            letter = column[0].column_letter
            max_length = max(
                len(str(cell.value or ""))
                for cell in column
            )
            ws.column_dimensions[letter].width = min(
                max_length + 3, 35
            )

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )

    response["Content-Disposition"] = (
        'attachment; filename="weather_statistics.xlsx"'
    )

    return response
