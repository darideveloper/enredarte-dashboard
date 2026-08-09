from django.contrib.admin import SimpleListFilter


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
        if self.value() == "with":
            return queryset.filter(**{f"{self.related}__isnull": False}).distinct()
        if self.value() == "without":
            return queryset.filter(**{f"{self.related}__isnull": True}).distinct()
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
    """Filter integer `year` fields by decade buckets derived from distinct years."""

    title = "Año"
    parameter_name = "decade"

    def lookups(self, request, model_admin):
        years = (
            model_admin.get_queryset(request)
            .values_list("year", flat=True)
            .distinct()
            .order_by("year")
        )
        decades = sorted({(y // 10) * 10 for y in years})
        return [(str(start), f"{start}–{start + 9}") for start in decades]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        start = int(self.value())
        return queryset.filter(year__gte=start, year__lt=start + 10)
