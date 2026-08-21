from django.contrib.admin import SimpleListFilter
from django.db.models import Exists, Max, Min, OuterRef


class HasRelatedFilter(SimpleListFilter):
    """Filter a changelist on whether records reference a related object.

    Concrete subclasses set `related` (reverse relation name), `title`, and a
    unique `parameter_name`; use the `has_related_filter` factory helper.
    """

    related = None

    def lookups(self, request, model_admin):
        return (
            ("with", f"Con {self.related}"),
            ("without", f"Sin {self.related}"),
        )

    def queryset(self, request, queryset):
        def has():
            lookup = {f"{self.related}__isnull": False}
            return queryset.model.objects.filter(pk=OuterRef("pk"), **lookup)

        if self.value() == "with":
            return queryset.filter(Exists(has()))
        if self.value() == "without":
            return queryset.filter(~Exists(has()))
        return queryset


def has_related_filter(related, title, parameter_name):
    """Build a concrete SimpleListFilter subclass checking for related records."""

    class _HasRelatedFilter(HasRelatedFilter):
        pass

    _HasRelatedFilter.related = related
    _HasRelatedFilter.title = title
    _HasRelatedFilter.parameter_name = parameter_name
    return _HasRelatedFilter


class YearFilter(SimpleListFilter):
    """Filter integer `year` fields by decade buckets derived from min/max years."""

    title = "Año"
    parameter_name = "decade"

    def lookups(self, request, model_admin):
        stats = model_admin.model.objects.aggregate(
            min_year=Min("year"), max_year=Max("year")
        )
        if stats["min_year"] is None:
            return []
        start = (stats["min_year"] // 10) * 10
        end = (stats["max_year"] // 10) * 10
        return [(str(d), f"{d}–{d + 9}") for d in range(start, end + 10, 10)]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        start = int(self.value())
        return queryset.filter(year__gte=start, year__lt=start + 10)
