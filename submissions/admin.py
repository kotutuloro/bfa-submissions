from django.contrib import admin

from .models import Student, Submission

class StudentAdmin(admin.ModelAdmin):
	list_display = ('discord_id', 'ddr_name', 'twitter', 'alum')
	list_display_links = ('discord_id', 'ddr_name')
	list_filter = ('alum', ) # TODO: maybe a filter about needing info
	ordering = ('discord_id', )
	search_fields = ['discord_id', 'ddr_name', 'twitter']

	# TODO: form -> view recent submissions?

class SubmissionAdmin(admin.ModelAdmin):
	list_display = ('student', 'score', 'submitted_at')
	list_display_links = ('score', )
	list_filter = (
		'student__alum',
		('student', admin.RelatedOnlyFieldListFilter)
	) # TODO: maybe also filter by verification
	list_select_related = ('student', )
	ordering = ('-submitted_at', )
	search_fields = ['student__discord_id', 'student__ddr_name']

	autocomplete_fields = ['student']
	readonly_fields = ('submitted_at', 'submission_picture')

admin.site.register(Student, StudentAdmin)
admin.site.register(Submission, SubmissionAdmin)
