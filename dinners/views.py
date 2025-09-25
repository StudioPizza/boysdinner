# dinners/views.py
from datetime import date
from django.db.models import Count
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from .models import Boy, Dinner


# helpers kept local to avoid drift
def _get_upcoming():
    today = date.today()
    return (Dinner.objects
            .filter(date__isnull=False, date__gte=today)
            .select_related("host")
            .order_by("date", "id")
            .first())

def last_dinner():
    return Dinner.objects.select_related("host").prefetch_related("attendees").order_by("-date").first()

def _get_last_done():
    today = date.today()
    return (Dinner.objects
            .filter(date__isnull=False, date__lte=today)
            .select_related("host")
            .order_by("-date", "-id")
            .first())



def _get_placeholder():
    # the “Assign next” POST creates/updates this
    return (Dinner.objects
            .filter(date__isnull=True)
            .select_related("host")
            .order_by("-id")
            .first())

def _get_history(limit=30):
    return (Dinner.objects
            .filter(date__isnull=False)
            .select_related("host")
            .order_by("-date", "-id")[:limit])

def _get_eligible_pool():
    """
    Rule: Eligible = all active members who have NOT hosted this calendar year (past dinners only).
    If everyone has hosted, fallback = all active members, ordered by fewest all-time hosts (fairness).
    """
    today = date.today()
    hosted_ids = set(
        Dinner.objects
        .filter(date__isnull=False, date__year=today.year, date__lte=today)
        .values_list("host_id", flat=True)
    )
    everyone = Boy.objects.filter(is_active=True).order_by("name")
    eligible = everyone.exclude(id__in=hosted_ids)

    is_strict = True
    if not eligible.exists():
        eligible = (everyone
                    .annotate(all_time_hosted=Count("hosted_dinners"))
                    .order_by("all_time_hosted", "name"))
        is_strict = False
    return eligible, is_strict


def home(request):
    upcoming = _get_upcoming()
    last_done = _get_last_done()
    placeholder = _get_placeholder()

    # If no upcoming & no placeholder, show the pool so you can decide next
    pool, is_strict = (None, None)
    if not upcoming and not placeholder:
        pool, is_strict = _get_eligible_pool()

    return render(request, "home.html", {
        "upcoming": upcoming,
        "next_placeholder": placeholder,   # ← pass to template
        "last_dinner": last_done,
        "eligible_pool": pool,
        "pool_is_strict": is_strict,
    })


def dashboard(request):
    pool, is_strict = _get_eligible_pool()
    history = _get_history(30)
    last_done = _get_last_done()
    return render(request, "dashboard.html", {
        "eligible_pool": pool,
        "pool_is_strict": is_strict,
        "history": history,
        "last_dinner": last_done,
    })


@require_POST
def assign_next_host(request):
    """
    Create or update a single placeholder Dinner (date=NULL) with the chosen host.
    Home page will then show that person if there's no scheduled future date yet.
    """
    boy_id = request.POST.get("boy_id")
    if not boy_id:
        return redirect("dashboard")

    try:
        boy = Boy.objects.get(pk=boy_id, is_active=True)
    except Boy.DoesNotExist:
        return redirect("dashboard")

    # If there's already a placeholder, update it; else create one.
    placeholder = Dinner.objects.filter(date__isnull=True).order_by("-id").first()
    if placeholder:
        if placeholder.host_id != boy.id:
            placeholder.host = boy
            placeholder.save(update_fields=["host"])
    else:
        Dinner.objects.create(host=boy)  # date remains NULL

    return redirect("home")
