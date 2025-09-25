from django.db.models import Count, Min, Q
from django.utils import timezone
from .models import Boy, Dinner
from datetime import date as date_cls
from datetime import timedelta


DECISION_WINDOW_DAYS = 7  # how long they have to decide

def current_year():
    return date_cls.today().year

def last_dinner():
    return Dinner.objects.select_related("host").prefetch_related("attendees").order_by("-date").first()

def hosts_this_year():
    yr = current_year()
    qs = (Dinner.objects
          .filter(date__year=yr)
          .values("host")
          .annotate(ct=Count("id")))
    return {row["host"]: row["ct"] for row in qs}

def upcoming_dinner():
    today = timezone.now().date()
    return (
        Dinner.objects
        .filter(date__isnull=False, date__gte=today)
        .select_related("host")
        .order_by("date", "id")
        .first()
    )


def eligible_next_host_pool():
    """
    Eligible pool = attendees of the most recent dinner who have NOT hosted this year.
    If everyone there already hosted this year, allow everyone who attended that last dinner.
    """
    ld = last_dinner()
    if not ld:
        return Boy.objects.none(), False  # no dinners yet

    already = hosts_this_year()
    attendees = ld.attendees.all().order_by("name")
    pool = [b for b in attendees if already.get(b.id, 0) == 0]
    if pool:
        return Boy.objects.filter(id__in=[b.id for b in pool]).order_by("name"), True
    # fallback: all attendees allowed (they’ll start new cycle or it’s a second host if you permit)
    return attendees, False

def hosted_list_this_year():
    """Return queryset of Boys who have hosted this year, annotated with times_hosted."""
    yr = current_year()
    return (Boy.objects
            .filter(hosted_dinners__date__year=yr)
            .annotate(times_hosted=Count("hosted_dinners"))
            .order_by("name"))

def dinner_history(limit=20):
    """Recent dinners with host + restaurant for a simple history list."""
    return (Dinner.objects
            .select_related("host")
            .order_by("-date")[:limit])

def get_current_cycle_deadline():
    last_dinner = Dinner.objects.order_by('-date').first()
    base_date = last_dinner.date if last_dinner else timezone.now().date()
    return base_date + timezone.timedelta(days=DECISION_WINDOW_DAYS)

def pick_next_host():
    boys = (Boy.objects
            .annotate(
                hosted_count=Count('hosted_dinners'),
                last_hosted_null=Count('last_hosted', filter=Q(last_hosted__isnull=True))
            )
            .order_by('-last_hosted_null', 'last_hosted', 'hosted_count', '-reliability', 'name'))
    return boys.first()


def get_days_left():
    return (get_current_cycle_deadline() - timezone.now().date()).days


def next_assignment():
    """
    The next host is the most recent Dinner with no date set (placeholder).
    """
    return Dinner.objects.filter(date__isnull=True).select_related("host").order_by("-created_at").first()

def days_left_to_decide(assignment):
    if not assignment:
        return None
    deadline = assignment.created_at.date() + timedelta(days=DECISION_WINDOW_DAYS)
    return (deadline - timezone.now().date()).days