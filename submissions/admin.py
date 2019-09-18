from django.contrib import admin

from .models import Student, Submission

class SubmissionsAdminSite(admin.AdminSite):
    site_header = 'BFA submissions administration'
    site_title = 'BFA submissions admin'
    site_url = None
    index_title = 'Submissions admin'

class SubmissionInline(admin.TabularInline):
	model = Submission
	max_num = 3
	show_change_link = True

	ordering = ['-submitted_at']

	def has_add_permission(self, req, obj):
		return False
	def has_change_permission(self, req, obj):
		return False
	def has_delete_permission(self, req, obj):
		return False

class StudentAdmin(admin.ModelAdmin):
	inlines = [SubmissionInline]

	list_display = ('discord_id', 'ddr_name', 'twitter', 'alum')
	list_display_links = ('discord_id', 'ddr_name')
	list_filter = ('alum', ) # TODO: maybe a filter about needing info
	ordering = ('discord_id', )
	search_fields = ['discord_id', 'ddr_name', 'twitter']

class SubmissionAdmin(admin.ModelAdmin):
	autocomplete_fields = ['student']
	readonly_fields = ('submitted_at', 'submission_picture')

	list_display = ('student', 'score', 'submitted_at')
	list_display_links = ('score', )
	list_filter = (
		'student__alum',
		('student', admin.RelatedOnlyFieldListFilter)
	) # TODO: maybe also filter by verification
	list_select_related = ('student', )
	ordering = ('-submitted_at', )
	search_fields = ['student__discord_id', 'student__ddr_name']

admin_site = SubmissionsAdminSite()

admin_site.register(Student, StudentAdmin)
admin_site.register(Submission, SubmissionAdmin)
