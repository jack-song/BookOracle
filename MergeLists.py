#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import Counter
import pandas as pd
from functools import reduce
import re

fictionListUrls = [
    # Highest rated.
    "https://www.goodreads.com/list/show/24716.Highest_Rated_Books_on_Goodreads_with_at_least_100_ratings_",
    "https://www.goodreads.com/list/show/24716.Highest_Rated_Books_on_Goodreads_with_at_least_100_ratings_?page=2",
    "https://www.goodreads.com/list/show/24716.Highest_Rated_Books_on_Goodreads_with_at_least_100_ratings_?page=3",
    # Listopia voted.
    "https://www.goodreads.com/list/show/13086.Goodreads_Top_100_Literary_Novels_of_All_Time",
    "https://www.goodreads.com/list/show/13086.Goodreads_Top_100_Literary_Novels_of_All_Time?page=2",
    # Time magazine novels.
    "https://www.goodreads.com/list/show/2681.Time_Magazine_s_All_Time_100_Novels",
    # World Library List.
    "https://www.goodreads.com/list/show/9440.100_Best_Books_of_All_Time_The_World_Library_List",
]


nonFictionListUrls = [
  # The Guardian.
  "https://www.goodreads.com/list/show/11168.The_Guardian_s_Top_100_Non_Fiction_Books",
  # Time Magazine.
  "https://www.goodreads.com/list/show/12719.Time_Magazine_s_All_TIME_100_Best_Non_Fiction_Books",
  # Random list.
  "https://www.goodreads.com/list/show/134.Best_Non_Fiction_no_biographies_",
  # Other random list.
  "https://www.goodreads.com/list/show/144661.Best_Nonfiction_Books_Of_All_Time",
]
# Bill Gates read list.
for page in range(12):
  nonFictionListUrls.append("https://www.goodreads.com/review/list/62787798-bill-gates?page={}&print=true&shelf=read&view=table".format(page))


testUrls = [
  "https://www.goodreads.com/shelf/show/running",
  "https://www.goodreads.com/review/list/62787798-bill-gates?shelf=read"
]

URL_LIST = fictionListUrls
OUTPUT_NAME = "novels"

def get_book_urls(base_url):
    print("Fetching list: {}".format(base_url))
    # Make http request
    response = requests.get(base_url)
    if response.status_code != 200:
      print("bad url: {}".format(base_url))
      exit

    html = response.content
    soup = BeautifulSoup(html, "lxml")
    # Curated lists
    links = soup.find_all("a", {"class": "bookTitle"})
    
    # "Shelves"
    if len(links) < 1:
        title_containers = soup.find_all("td", {"class": "field title"})
        links = [td.find('a') for td in title_containers]

    relative_url = [link['href'] for link in links]
    full_url = [urljoin(base_url, relativeurl) for relativeurl in relative_url]
    book_urls = [url for url in full_url if "https://www.goodreads.com/book/show" in url]

    print("Got books: {}".format(len(book_urls)))

    return book_urls

list_urls = [get_book_urls(base_url) for base_url in URL_LIST]
all_urls = reduce(list.__add__, list_urls)
url_counts = Counter(all_urls)

unique_urls = list(set(all_urls))

book_rating = []
book_standout_score = []
book_count = []

for url in unique_urls:
    note_resp = requests.get(url)
    
    #checking if the request is successful
    if note_resp.status_code == 200:
        print("Successfully pulled: {}".format(url))
        try:
            #get HTML from url page
            note_html = note_resp.content
            note_soup = BeautifulSoup(note_html, 'html.parser')

            #Extract rating particulars
            rating_divs = note_soup.find_all("div", {"id": "bookMeta"})
            rating_text = float(rating_divs[0].find_all("span", {"itemprop": "ratingValue"})[0].text)
            book_rating.append(rating_text)

            #Standout score - tooltip is rendered dynamically, so must be extracted from inside CDATA with regex.
            full_str = str(rating_divs[0])
            voting_subtotal_strs = re.findall('% \(.*?\)', full_str)
            print("strs {}".format(voting_subtotal_strs))
            voting_subtotals = [float(s[s.find("(")+1:s.find(")")]) for s in voting_subtotal_strs]
            print("subtotals {}".format(voting_subtotals))
            five_stars = voting_subtotals[0]
            four_stars = voting_subtotals[1]
            three_stars = voting_subtotals[2]
            score = (five_stars/(four_stars+three_stars))
            book_standout_score.append(score)

        except Exception as e:
            print('Could not parse book page: {}: {}'.format(url, e))
            book_rating.append(0)
            book_standout_score.append(0)

    else:
        print('Status code {}, skipping URL: {}'.format(note_resp.status_code, url))
        book_rating.append(0)
        book_standout_score.append(0)

    book_count.append(url_counts[url])

print("Building Dataframe for {} books".format(len(unique_urls)))

book_df = pd.DataFrame()

book_df["Goodreads Link"] = unique_urls
book_df["Count"] = book_count
book_df["SOScore"] = book_standout_score
book_df["Rating"] = book_rating

print("Sorting Dataframess")

# Sorting the dataframe based on ratings
sorted_soscore_book_df = book_df.sort_values(by=['Count', 'SOScore'], ascending = False)
sorted_soscore_book_df.reset_index(drop=True, inplace = True)

sorted_rating_book_df = book_df.sort_values(by=['Count', 'Rating'], ascending = False)
sorted_rating_book_df.reset_index(drop=True, inplace = True)

print("Exporting Dataframes")

# Export dataframe
sorted_soscore_book_df.to_csv("{}_by_soscore.csv".format(OUTPUT_NAME))
sorted_rating_book_df.to_csv("{}_by_rating.csv".format(OUTPUT_NAME))

print("Done!")