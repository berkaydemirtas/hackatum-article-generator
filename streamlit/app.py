import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import re

def render_text_with_links(text):
    links = re.findall(r'\[([^\]]+)\]', text)
    unique_links = list(set(links))  
    link_dict = {idx + 1: url for idx, url in enumerate(unique_links)}
    
    for idx, url in link_dict.items():
        text = text.replace(f"[{url}]", f'<a href="{url}" target="_blank">[{idx}]</a>')
    
    link_list_html = "<ul style='list-style-type: none; padding-left: 0;'>"
    for idx, url in link_dict.items():
        link_list_html += f'<li><a href="{url}" target="_blank">[{idx}] {url}</a></li>'
    link_list_html += "</ul>"
    
    st.markdown(
        f"<p style='font-size: 1em; line-height: 1.8; text-align: justify; margin-bottom: 20px;'>{text}</p>", 
        unsafe_allow_html=True
    )
    st.markdown(link_list_html, unsafe_allow_html=True)

def format_timestamp(created_at_str):
    created_at_dt = datetime.strptime(created_at_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    return created_at_dt.strftime('%Y-%m-%d %H:%M:%S')

# Set wide layout
st.set_page_config(layout="wide", page_title="Artify", page_icon="📰")

# Query Parameters for Navigation
query_params = st.query_params
article_id = query_params.get("article_id", None)

# Set consistent layout for all sections
c1, c2, c3 = st.columns((1.5, 6, 1.5))

# If viewing a specific article
if article_id is not None:
    with c2:
        response = requests.get(f"http://django:8000/articles/{article_id}/")
        article = response.json()

        # Display the article title, image, and content
        st.markdown(
            f"""
            <style>
                .tooltip {{
                    position: relative;
                    display: inline-block;
                }}
                .tooltip .tooltiptext {{
                    visibility: hidden;
                    width: 200px;
                    background-color: black;
                    color: #fff;
                    text-align: center;
                    border-radius: 6px;
                    padding: 5px;
                    position: absolute;
                    z-index: 1;
                    bottom: 125%; /* Position above the circle */
                    left: 50%;
                    margin-left: -100px;
                    opacity: 0;
                    transition: opacity 0.3s;
                }}
                .tooltip:hover .tooltiptext {{
                    visibility: visible;
                    opacity: 1;
                }}
            </style>
            <h2 style="text-align: left; display: flex; align-items: center; justify-content: space-between;">
                {article['title']}
                <div class="tooltip" style="width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
                            background-color: {'#ff4d4d' if len(article['used_news']) == 1 else '#ffa500' if len(article['used_news']) == 2 else '#4caf50'};
                            color: white; font-size: 16px; font-weight: bold; line-height: 1; margin-left: 10px; flex-shrink: 0;">
                    {len(article['used_news'])}
                    <span class="tooltiptext">Number of sources used to generate this article </span>
                </div>
            </h2>
            """,
            unsafe_allow_html=True
        )
        
        try:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center;">
                    <img src="{article['main_image']}" style="width: 50%; height: auto;"/>
                </div>
                <p style="text-align: center;">{article["title"]}</p>
                """, 
                unsafe_allow_html=True
            )
        except:
            pass

        st.write(f"<p style='font-size: 1em; line-height: 1.8;'>{render_text_with_links(article['content'])}</p>", unsafe_allow_html=True)
        st.write(f"**Posted on:** {format_timestamp(article['created_at'])}")

else:
    with c2:
        st.markdown("<h1 style='text-align: center; color: #1e90ff;'>Artify - Electric Vehicle News</h1>", unsafe_allow_html=True)
        st.markdown("📰 Latest News Feed")

        search_query = st.text_input("Search for news:", key="search")
        response = requests.get("http://django:8000/articles/")
        news_data = response.json() 

        # Filter news based on the search query
        if search_query:
            filtered_news = [article for article in news_data if search_query.lower() in article['title'].lower() or search_query.lower() in article['content'].lower()]
        else:
            filtered_news = news_data 

        # Display news feed with clickable titles and images
        if filtered_news:
            for idx, article in enumerate(filtered_news):
                st.markdown(
                        f"""
                        <style>
                            .tooltip {{
                                position: relative;
                                display: inline-block;
                            }}
                            .tooltip .tooltiptext {{
                                visibility: hidden;
                                width: 200px;
                                background-color: black;
                                color: #fff;
                                text-align: center;
                                border-radius: 6px;
                                padding: 5px;
                                position: absolute;
                                z-index: 1;
                                bottom: 125%; /* Position above the circle */
                                left: 50%;
                                margin-left: -100px;
                                opacity: 0;
                                transition: opacity 0.3s;
                            }}
                            .tooltip:hover .tooltiptext {{
                                visibility: visible;
                                opacity: 1;
                            }}
                        </style>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; border: 1px solid #ddd; border-radius: 10px; padding: 20px; margin-bottom: 15px; width: 90%; margin-left: auto; margin-right: auto;">
                            <div style="flex: 4; padding-right: 20px;">
                                <a href="?article_id={article['id']}" style="font-size: 20px; color: #1e90ff; text-decoration: none;">
                                    🔹 {article['title']}
                                </a>
                                <p style="color: grey; font-size: 0.9em;">Posted on {format_timestamp(article['created_at'])}</p>
                                <p>{' '.join(article['content'].split()[:35])}...</p>
                            </div>
                            <div style="flex: 1; text-align: center;">
                                <div class="tooltip" style="width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
                                                            background-color: {'#ff4d4d' if len(article['used_news']) == 1 else '#ffa500' if len(article['used_news']) == 2 else '#4caf50'};
                                                            color: white; font-size: 16px; font-weight: bold;">
                                    {len(article['used_news'])}
                                    <span class="tooltiptext">This is the number of used news articles</span>
                                </div>
                            </div>
                            <div style="flex: 1; text-align: right;">
                                <img src="{article['main_image']}" alt="{article['title']}" style="width: 120px; height: auto; border-radius: 5px;">
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )


        else:
            st.write("No news articles match your search. Try a different keyword!")
