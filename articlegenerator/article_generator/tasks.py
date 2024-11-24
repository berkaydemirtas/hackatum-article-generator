from celery import shared_task
import os
import urllib.request
import urllib
from bs4 import BeautifulSoup
import feedparser

@shared_task()
def generate_article_from_updated_cluster(cluster_id):
    from .services import topic_selection, content_selection, article_generation, gen_image_description, image_generation
    from .models import Cluster, News, Article, Image
    
    cluster = Cluster.objects.get(id=cluster_id)
    one_cluster_articles = []
    content_for_article = []
    for news in News.objects.filter(cluster=cluster):
        one_cluster_articles.append({
            "title": news.title,
            "link": news.link,
            "description": news.description,
            "content": news.content,
            "embedding": news.embedding
        })
    article_topic = str(topic_selection(one_cluster_articles))
    print(f"Topic: {article_topic}\n\n")
    for article in one_cluster_articles:
        content_for_article_each = {}
        content_for_article_each["link"] = article["link"]
        selected_contents = content_selection(content=article["content"], topic=article_topic)
        content_for_article_each["contents"] = selected_contents

        content_for_article.append(content_for_article_each)
        print(selected_contents)
        print("\n\n\n")

    article_content = article_generation(content=content_for_article, topic=article_topic)
    print(f"Article content:\n\n{article_content}")

    image_generation_instruction = gen_image_description(content=article_content, topic=article_topic)
    print(image_generation_instruction)
    image_url = image_generation(image_description=image_generation_instruction)
    print(image_url)
    article_topic =article_topic.strip('"\'')
    article = Article.objects.create(title=article_topic, content=article_content)
    article.used_news.set(cluster.news_set.all())
    if not os.path.exists("images"):
            os.makedirs("images")
    image_path = f"images/{article.id}_main_image.jpg"
    urllib.request.urlretrieve(image_url, image_path)
    with open(image_path, 'rb') as f:
        file_data = f.read()

    image = Image.objects.create(
        article=article,
        file_data=file_data,
        classification=0
    )
    article.images.add(image)

@shared_task
def generate_article_for_all_news():
    from .models import Cluster, News, Article, Image
    Article.objects.all().delete()
    for cluster in Cluster.objects.all():
        try:
            generate_article_from_updated_cluster(cluster.id)
        except Exception as e:
            print(e)


@shared_task
def crawl_news_from_rss(rss_urls, is_initial_crawl=False):
    from .services import cluster_initial_news, assign_cluster_for_news, is_about_electric_vehicles, get_article_content, clean_content_with_ai, get_embedding
    from .models import Cluster, News
    if is_initial_crawl:
        News.objects.all().delete()
        Cluster.objects.all().delete()
        
    news = []
    news_links = News.objects.values_list('link', flat=True)

    for rss_url in rss_urls:
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            description = BeautifulSoup(entry.description, "html.parser").get_text() if hasattr(entry, 'description') else ""

            if link in news_links:
                print(f"News already exists: {link}")
                continue
            
            print(f"Fetching: {title}")
            is_about_electric_vehicles_content = is_about_electric_vehicles(description)
            if is_about_electric_vehicles_content != "1":
                print("Not about electric vehicles")
                continue
            
            content = get_article_content(link)
            cleaned_content = clean_content_with_ai(content) if content else None
            
            cleaned_description = clean_content_with_ai(description)
            
            embedding = get_embedding(cleaned_content)
            
            news.append({
                "title": title,
                "link": link,
                "description": cleaned_description,
                "content": cleaned_content,
                "embedding": embedding
            })
            try:
                new_news = News.objects.create(title=title, link=link, description=cleaned_description, content=cleaned_content, embedding=embedding)
                if not is_initial_crawl:
                    assign_cluster_for_news(new_news)
                    generate_article_from_updated_cluster(new_news.cluster)
            except Exception as e:
                print(f"Failed to create news: {e}")
    
    if is_initial_crawl:
        cluster_initial_news()
        generate_article_for_all_news()
