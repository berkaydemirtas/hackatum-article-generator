
import requests
from celery import shared_task
import os
import urllib.request
import urllib
from bs4 import BeautifulSoup
import feedparser

from bs4 import BeautifulSoup
import feedparser
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from article_generator.models import News, Cluster

rss_urls = ["https://feeds.highgearmedia.com/?sites=MotorAuthority",
            "https://feeds.highgearmedia.com/?sites=MotorAuthority&tags=news",
            "https://rss.app/feeds/29fjfRVBrm8PE1cM.xml",
            "https://rss.app/feeds/9uYdzcRtEvf3fbDV.xml",
            "https://rss.app/feeds/f5iGSzFTIOCLMkZ6.xml",
            ]

azure_embedding_url = ''
azure_api_url = ''
azure_dalle_api_url = ""
azure_api_key =  ''

def get_article_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  
        soup = BeautifulSoup(response.content, "html.parser")
        
        paragraphs = soup.find_all('p')
        content = "\n".join([para.get_text() for para in paragraphs])
        return content
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def clean_content_with_ai(content):
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": azure_api_key
        }
        payload = {
            "messages": [
                {"role": "system", "content": "You are a text-cleaning assistant."},
                {"role": "user", "content": f"I got this text from a news website using web crawling. However, there might be some random and useless things because the crawling didn't work well. Clean the text. Don't add anything new, just clean the things random and useless, return empty string if no content is provided:\n\n{content}"}
            ],
            "temperature": 0.7,
            "max_tokens": 4800
        }
        response = requests.post(azure_api_url, headers=headers, json=payload)
        response.raise_for_status()  # Ensure the request was successful
        data = response.json()
        cleaned_content = data["choices"][0]["message"]["content"]
        return cleaned_content
    except Exception as e:
        print(f"Failed to clean content with AI: {e}")
        return content

def get_embedding(text):
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": azure_api_key
        }
        payload = {
            "input": text
        }
        response = requests.post(azure_embedding_url, headers=headers, json=payload)
        response.raise_for_status()  # Ensure the request was successful
        data = response.json()
        embedding = data['data'][0]['embedding']
        return embedding
    except Exception as e:
        print(f"Failed to get embedding: {e}")
        return None

def is_about_electric_vehicles(content):
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": azure_api_key
        }
        payload = {
            "messages": [
                {"role": "system", "content": "You are an assistant for deciding if a text is about electric vehicles."},
                {"role": "user", "content": f"I will give you title of a news. Return me 1 if it is about electric vehicles, return me 0 if not. Don't return anything else just 1 or 0: \n\n{content}"}
            ],
            "temperature": 0,
            "max_tokens": 2000
        }
        response = requests.post(azure_api_url, headers=headers, json=payload)
        response.raise_for_status()  # Ensure the request was successful
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Failed to clean content with AI: {e}")
        return content

def crawl_news_from_rss(is_initial_crawl=False):
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
            if not embedding:
                continue
            
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


def topic_selection(content : list):
    sys_prompt = """ You are a professional news article topic generator. Your job is to create an engaging and clear title for a brand-new news article based on the provided input. The input will consist of a list of JSON data containing news articles from various sources.

    Instructions:
    1. Carefully review and analyze all the given input articles. Pay close attention to key details, themes, and insights. Do not skip or skim this step.
    2. Generate a creative and attention-grabbing title that reflects the essence of the content. Ensure the title is clear, specific, and avoids being vague.
    3. Only return the title as the output.
    
    Input Format:
    [{'id':'', "link":'', 'title':'', 'description':'', 'content':''}, ]

    """
    user_content = f"Input Content:\n{content}\n\nNew Title:"
    print(f"User Content:\n{user_content}")
    
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": azure_api_key
        }
        payload = {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.9,
            "max_tokens": 10000
        }
        response = requests.post(azure_api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        response_content = data["choices"][0]["message"]["content"]
        return response_content
    except Exception as e:
        print(f"Failed to get a response: {e}")
        return ""


def content_selection(content : list, topic : str):
    sys_prompt = """ You are a professional and meticulous news article content selector. Your task is to extract sentences relevant to a given topic from the provided article content.

    Instructions:
    1. Carefully review and analyze the input article content. Pay close attention to key details, themes, and insights. Do not skip or rush this step.
    2. Identify and select sentences that directly relate to the given topic. Ensure the selections are precise and relevant.
    3. Return the selected sentences in the form of a list.

    """
    user_content = f"Topic:\n{topic}\n\nInput Content:\n{content}\n\nSelected Sentences list:"
    
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": azure_api_key
        }
        payload = {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.0,
            "max_tokens": 10000
        }
        response = requests.post(azure_api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        response_content = data["choices"][0]["message"]["content"]
        return response_content
    except Exception as e:
        print(f"Failed to get a response: {e}")
        return ""
    
def article_generation(content : list, topic : str):
    sys_prompt = """ You are a professional and meticulous news article content generator. Your task is to create an engaging and clear news article based on a provided topic and supporting information related to that topic.

    Instructions:
    1. Carefully review and analyze the given input information. Pay close attention to key details, themes, and insights. Avoid skipping or rushing through this step.
    2. Write a well-structured news article based on the topic and input information. Ensure the article is both informative and interesting. Feel free to elaborate on the sentences and present the content in an engaging way.
    3. You can add some additional information to the article in addition to the given sources if you think it is relevant but don't generate wrong information
    4. Write longer texts by adding your own words as well and don't citate that kind of addition
    5. Ensure that any factual content derived from the input sources is properly credited. Include citations, formatted like this example:

    If the input is this: [
    \{ 'link': link1, 'content': '1. Berlin is the capital and a state of the Federal Republic of Germany . \n2.It has around 3.8 million inhabitants.' \}, 
    \{ 'link': link2, 'content': '1. Berlin is one of the economic centres in Europe. 2. The important branches of the city's economy include tourism , the creative and cultural industries, and information technology.' \}
    ]
    
    Example article content: Berlin, the capital and one of the 16 states of the Federal Republic of Germany, is a dynamic metropolis with a population of approximately 3.8 million. [link1] Renowned for its rich history and modern innovation, the city serves as one of Europe's major economic hubs. [link2] Key pillars of Berlin's economy include tourism. [link2]

    """
    user_content = f"Topic:\n{topic}\n\nInput:\n{content}\n\nArticle Content:"
    
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": azure_api_key
        }
        payload = {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.0,
            "max_tokens": 10000
        }
        response = requests.post(azure_api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        response_content = data["choices"][0]["message"]["content"]
        return response_content
    except Exception as e:
        print(f"Failed to get a response: {e}")
        return ""

def gen_image_description(content : str, topic : str):
    sys_prompt = """ You are a skilled and detail-oriented art instructor with a passion for imagery. Your task is to provide a detailed description for creating an image based on the given content.

    Instructions:
    1. Carefully review and analyze the input information. Pay close attention to key details, themes, and insights.
    2. Based on the information provided, envision an image that captures the essence of the content.
    3. Write a detailed description of how to create the image you imagined. Include specifics on elements like colors, composition, perspective, and any other relevant details to guide the creation of the image.
    4. Create realistic images that can be used in the context of a news article. This is important. Be realistic!
    """
    user_content = f"Topic:\n{topic}\n\nInput:\n{content}\n\nInstruction:"
    
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": azure_api_key
        }
        payload = {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.0,
            "max_tokens": 10000
        }
        response = requests.post(azure_api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        response_content = data["choices"][0]["message"]["content"]
        return response_content
    except Exception as e:
        print(f"Failed to get a response: {e}")
        return ""

def image_generation(image_description):
    headers= { "api-key": azure_api_key, "Content-Type": "application/json" }
    body = {
        "prompt": image_description,
        "size": "1024x1024",
        "n": 1,
        "quality": "hd", 
        "style": "vivid"
    }
    submission = requests.post(azure_dalle_api_url, headers=headers, json=body)
    image_url = submission.json()['data'][0]['url']
    return image_url


def decide_k_and_cluster(embeddings):
    best_k = None
    best_score = -1
    best_model = None

    for k in range(2, len(embeddings)-1):
        kmeans = KMeans(n_clusters=k, random_state=42)
        labels = kmeans.fit_predict(embeddings)
        
        score = silhouette_score(embeddings, labels)
        
        if score > best_score:
            best_k = k
            best_score = score
            best_model = kmeans
    return best_model, best_k, best_score


def cluster_initial_news():
    newss = News.objects.all()
    embeddings = []
    ids = []
    for news in newss:
        embeddings.append(news.embedding)
        ids.append(news.id)
    
    best_model, best_k, best_score = decide_k_and_cluster(embeddings)
    print(f"best K:{best_k} \nScore: {best_score}")
    
    labels = best_model.labels_
    centroids = best_model.cluster_centers_
    centroid_ids = []
    for centroid in centroids:
        new_cluster = Cluster.objects.create(centroid=centroid)
        centroid_ids.append(new_cluster.id)
    
    for i in range(len(ids)):
        news = News.objects.get(id=ids[i])
        news.cluster = Cluster.objects.get(id=centroid_ids[labels[i]])
        news.save()

        

    print(f"Cluster Labels: {labels}")
    print(f"Centroids: \n{centroids}")


def assign_cluster_for_news(news):
    closest_cluster, similarity = news.get_closest_cluster()
    if similarity < 0.8:
        new_cluster = Cluster.objects.create(centroid=news.embedding)
        news.cluster = new_cluster
    else:
        news.cluster = closest_cluster
    news.save()

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


def generate_article_for_all_news():
    from .models import Cluster, News, Article, Image
    Article.objects.all().delete()
    for cluster in Cluster.objects.all():
        try:
            generate_article_from_updated_cluster(cluster.id)
        except Exception as e:
            print(e)