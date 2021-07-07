from django.contrib import admin
from django.forms import BaseInlineFormSet
from django.utils.html import format_html

from .models import Student, Challenge, Submission

class SubmissionsAdminSite(admin.AdminSite):
    site_header = 'BFA submissions administration'
    site_title = 'BFA submissions admin'
    site_url = None
    index_title = 'Submissions admin'

class LimitModelFormset(BaseInlineFormSet):
    """ Base Inline formset to limit inline Model query results."""
    def __init__(self, *args, **kwargs):
        super(LimitModelFormset, self).__init__(*args, **kwargs)
        _kwargs = {self.fk.name: kwargs['instance']}
        self.queryset = kwargs['queryset'].filter(**_kwargs).order_by('-id')[:5]

class SubmissionInline(admin.TabularInline):
	model = Submission
	show_change_link = True
	formset = LimitModelFormset

	ordering = ['-submitted_at']

	def has_add_permission(self, req, obj):
		return False
	def has_change_permission(self, req, obj):
		return False
	def has_delete_permission(self, req, obj):
		return False

class StudentAdmin(admin.ModelAdmin):
	inlines = [SubmissionInline]

	list_display = ('discord_id', 'ddr_name', 'twitter', 'level')
	list_display_links = ('discord_id', 'ddr_name')
	list_filter = ('level', )
	ordering = ('discord_id', )
	search_fields = ['discord_id', 'ddr_name', 'twitter']

class ChallengeAdmin(admin.ModelAdmin):
	ordering = ('-week', )
	search_fields = ['week', 'name']

class SubmissionAdmin(admin.ModelAdmin):

	def submission_picture(self, obj):
		return format_html(
			'''<a target="_blank" href="{}">
			<img src={} style="max-width:100%; max-height:700px">
			</a>''',
			obj.pic_url, obj.pic_url
		)

	autocomplete_fields = ['student', 'challenge']
	readonly_fields = ('submitted_at', 'submission_picture')

	list_display = ('student', 'challenge', 'score', 'submitted_at')
	list_display_links = ('score', )
	list_filter = (
		'student__level',
		('challenge', admin.RelatedOnlyFieldListFilter),
		('student', admin.RelatedOnlyFieldListFilter)
	) # TODO: maybe also filter by verification
	list_select_related = ('student', 'challenge')
	ordering = ('-submitted_at', )
	search_fields = ['student__discord_id', 'student__ddr_name', 'challenge']

admin_site = SubmissionsAdminSite()

admin_site.register(Student, StudentAdmin)
admin_site.register(Challenge, ChallengeAdmin)
admin_site.register(Submission, SubmissionAdmin)
