from decimal import Decimal

from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.db.models import Count, Q, Sum
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.contrib.filters.admin import RangeDateFilter

from finance.models import FinancialEntry
from project.admin_base import ModelAdminUnfoldBase


def _totals(queryset):
    """Per-currency income / expense / net totals for a ledger queryset."""
    rows = []
    for row in (
        queryset.values("currency")
        .annotate(
            income=Sum("amount", filter=Q(amount__gt=0)),
            expenses=Sum("amount", filter=Q(amount__lt=0)),
            net=Sum("amount"),
            count=Count("id"),
        )
        .order_by("currency")
    ):
        row["income"] = row["income"] or Decimal("0")
        row["expenses"] = row["expenses"] or Decimal("0")
        row["net"] = row["net"] or Decimal("0")
        rows.append(row)
    return rows


@admin.register(FinancialEntry)
class FinancialEntryAdmin(ModelAdminUnfoldBase):
    sidebar_icon = "receipt_long"
    list_display = (
        "occurred_on",
        "kind",
        "artist",
        "display_amount",
        "currency",
        "reference",
        "reconciled",
    )
    list_editable = ("reconciled",)
    list_filter = (
        ("occurred_on", RangeDateFilter),
        ("artist", RelatedOnlyFieldListFilter),
        "kind",
        "payment_method",
        "currency",
        "reconciled",
    )
    search_fields = ("artist__name", "reference", "note")
    date_hierarchy = "occurred_on"
    list_after_template = "admin/finance/financialentry/ledger_totals.html"
    list_per_page = 50
    readonly_fields = (
        "occurred_on",
        "kind",
        "amount",
        "currency",
        "artist",
        "payment_method",
        "order",
        "subscription",
        "reference",
        "note",
        "created_at",
        "updated_at",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("artist")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        context = getattr(response, "context_data", None)
        if context is None or "cl" not in context:
            return response
        cl = context["cl"]
        context["ledger_totals"] = {
            "filtered": _totals(cl.queryset),
            "full": _totals(cl.root_queryset),
        }
        return response

    @admin.display(description=_("Monto"), ordering="amount")
    def display_amount(self, obj):
        color = "#166534" if obj.amount >= 0 else "#991b1b"
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>',
            color,
            f"{obj.amount:+,.2f}",
        )
