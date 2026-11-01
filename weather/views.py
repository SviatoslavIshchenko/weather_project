from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import SearchHistory
from .services import get_weather
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Min, Max
from .exports import export_csv, export_excel

@login_required             # Це декоратор, який дозволяє відкривати сторінку тільки авторизованим користувачам. Якщо користувач не ввійшов у систему, Django автоматично перенаправить його на /login/.
def home(request):
    weather = None
    error = None

    if request.method == "POST":
        city = request.POST.get("city", "").strip()

        if not city:
            error = "Введіть назву міста."
        else:
            weather = get_weather(city)

            if weather is None:
                error = "Не вдалося отримати погоду. Перевірте назву міста або спробуйте пізніше."

            else:
                SearchHistory.objects.create(     # SearchHistory — наша модель бази даних, objects — менеджер Django ORM для роботи із записами, create() — створює та зберігає новий запис у SQLite.
                    user=request.user,             # поточний авторизований користувач
                    city=weather["city"],           # назва міста з відповіді API
                    temperature=weather["temperature"],
                    description=weather["description"],
                    humidity=weather["humidity"],
                    feels_like=weather["feels_like"],
                    wind_speed=weather["wind_speed"],
                    pressure=weather["pressure"],
                )

    return render(
        request,
        "weather/home.html",
        {
            "weather": weather,
            "error": error,
        }
    )


@login_required
def history(request):

    sort = request.GET.get("sort", "date_desc")

    # Отримуємо параметри фільтрації з GET-запиту
    city_query = request.GET.get("city", "").strip()
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    date_error = None

    # Перевіряємо правильність діапазону дат
    if date_from and date_to and date_from > date_to:
        date_error = "Початкова дата не може бути пізнішою за кінцеву."

    # Отримуємо записи тільки поточного користувача
    searches = SearchHistory.objects.filter(
        user=request.user
    )

    # Фільтрація за назвою міста
    if city_query:
        searches = searches.filter(
            city__icontains=city_query
        )

    # Фільтрація за датами
    if not date_error:

        if date_from:
            searches = searches.filter(
                search_date__date__gte=date_from
            )

        if date_to:
            searches = searches.filter(
                search_date__date__lte=date_to
            )

    else:
        searches = searches.none()

    # Доступні варіанти сортування
    sort_options = {
        "date_desc": "-search_date",
        "date_asc": "search_date",
        "temp_asc": "temperature",
        "temp_desc": "-temperature",
        "city_asc": "city",
    }

    # Визначаємо поле сортування
    sort_field = sort_options.get(sort, "-search_date")

    # Сортуємо записи через Django ORM
    searches = searches.order_by(sort_field, "id")

    # Статистика пошуків за містами
    city_stats = (
        searches
        .order_by()
        .values("city") # групує записи за містом
        .annotate(      # обчислює статистичні показники для кожної групи.
            search_count=Count("id"),
            avg_temperature=Avg("temperature"),
            min_temperature=Min("temperature"),
            max_temperature=Max("temperature"),
        )
        .order_by("-search_count", "city") # сортує міста за спаданням кількості пошуків
    )

    # Підготовка даних для графіків
    chart_data = {
        "cities": [],
        "counts": [],
        "avg_temperatures": [],
        "min_temperatures": [],
        "max_temperatures": [],
    }

    for stat in city_stats:
        chart_data["cities"].append(stat["city"])
        chart_data["counts"].append(stat["search_count"])

        chart_data["avg_temperatures"].append(
            float(stat["avg_temperature"])
            if stat["avg_temperature"] is not None else None
        )

        chart_data["min_temperatures"].append(
            float(stat["min_temperature"])
            if stat["min_temperature"] is not None else None
        )

        chart_data["max_temperatures"].append(
            float(stat["max_temperature"])
            if stat["max_temperature"] is not None else None
        )

    export_format = request.GET.get("export")

    if export_format == "csv":
        return export_csv(searches)

    if export_format == "xlsx":
        return export_excel(searches)

    # ---------------------------
    # ПАГІНАЦІЯ
    # ---------------------------

    # Отримуємо кількість записів на сторінці з GET-запиту
    per_page = request.GET.get("per_page", "10")

    # Дозволяємо тільки 5, 10, 20 або 50 записів
    if per_page not in ("5", "10", "20", "50"):
        per_page = "10"

    # Створюємо пагінатор з обраною кількістю записів
    paginator = Paginator(searches, int(per_page))

    # Отримуємо номер сторінки з GET-запиту
    page_number = request.GET.get("page")

    # Отримуємо записи потрібної сторінки
    page_obj = paginator.get_page(page_number)

    # Зберігаємо GET-параметри для посилань пагінації
    query_params = request.GET.copy()
    query_params.pop("page", None)
    filter_query = query_params.urlencode()

    # Передаємо дані в HTML-шаблон
    return render(
        request,
        "weather/history.html",
        {
            "searches": page_obj,
            "page_obj": page_obj,
            "city_query": city_query,
            "date_from": date_from,
            "date_to": date_to,
            "date_error": date_error,
            "sort": sort,
            "per_page": per_page,
            "filter_query": filter_query,
            "city_stats": city_stats,
            "chart_data": chart_data,
        }
    )

@login_required
@require_POST
def delete_search(request, search_id):

    search = get_object_or_404(
        SearchHistory,
        id=search_id,
        user=request.user
    )

    # Зберігаємо назву міста перед видаленням
    city_name = search.city

    # Видаляємо запис із бази даних
    search.delete()

    # Створюємо повідомлення про успішне видалення
    messages.success(
        request,
        f"Запис пошуку погоди для міста {city_name} успішно видалено."
    )

    # Повертаємо користувача на сторінку історії
    return redirect("history")

@login_required
@require_POST
def clear_history(request):

    deleted_count, _ = SearchHistory.objects.filter( # Вибирає з бази даних тільки записи поточного користувача
        user=request.user
    ).delete()

    messages.success(
        request,
        f"Історію пошуку очищено. Видалено записів: {deleted_count}."
    )

    return redirect("history")