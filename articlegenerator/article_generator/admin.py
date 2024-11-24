from django.contrib import admin


from article_generator.models import News, Cluster, Article, Image

class NewsInline(admin.TabularInline):
    model = News  # This links the `News` model to the `Cluster` model
    extra = 0     # Do not show any extra empty rows by default
    fields = ('title', 'link', 'created_at')  # Fields to display in the inline
    readonly_fields = ('title', 'link', 'created_at')  # Make fields read-only to avoid accidental edits

class ClusterAdmin(admin.ModelAdmin):
    inlines = [NewsInline]  # Attach the `NewsInline` to the `ClusterAdmin`
    list_display = ('id',)  # Display the cluster ID in the cluster list view

# Register the models with the admin
admin.site.register(Cluster, ClusterAdmin)
admin.site.register(News)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'content', 'get_used_news')  # Add the custom method

    def get_used_news(self, obj):
        # Return a comma-separated list of related objects
        return ", ".join([news.title for news in obj.used_news.all()])

    get_used_news.short_description = 'Used News'  # Display name for the column

admin.site.register(Article, ArticleAdmin)
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_classification_display',)

    def get_classification_display(self, obj):
        return obj.get_classification_display()
    get_classification_display.short_description = 'Classification'