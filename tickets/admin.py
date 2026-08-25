from django.contrib import admin
from .models import Category, SLAPolicy, Ticket, TicketAttachment, TicketComment, TicketHistory, TicketFeedback


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ('priority', 'response_time_minutes', 'resolution_time_minutes')


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'subject', 'category', 'priority', 'status', 'assigned_to', 'created_by', 'created_at', 'is_overdue')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('ticket_number', 'subject', 'description')
    inlines = [TicketCommentInline, TicketAttachmentInline]


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'actor', 'action', 'created_at')


@admin.register(TicketFeedback)
class TicketFeedbackAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'rating', 'submitted_at')
