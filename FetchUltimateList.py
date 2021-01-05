#!/usr/bin/env python

fictionListUrls = [
  # Highest rated.
  "https://www.goodreads.com/list/show/24716.Highest_Rated_Books_on_Goodreads_with_at_least_100_ratings_",
  # Listopia voted.
  "https://www.goodreads.com/list/show/13086.Goodreads_Top_100_Literary_Novels_of_All_Time",
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
  # Bill Gates.
  "https://www.goodreads.com/review/list/62787798-bill-gates?shelf=read",
]

#### Set up ####

# Import required libraries
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd

# Specify the url
base_site = "https://www.goodreads.com/shelf/show/running"

# Make http request
response = requests.get(base_site)

# Check if request is successful. Status code of 200 indicates a successful attempt.
response.status_code

# Get the html from webpage
html = response.content

# Creating a BeautifulSoup object with the use of a parser
soup = BeautifulSoup(html, "lxml")

# Exporting html file
with open('popularrunningbooks.html', 'wb') as file:
    file.write(soup.prettify('utf-8'))
    
#### Extracting the url addresses of each book link ####

# First layer: The element that contains all the data
divs = soup.find_all("div", {"class": "elementList"})

# Second layer: Extracting html tags that contain the links
links = [div.find('a') for div in divs]

# Extracting the partial links  
relative_url = [link['href'] for link in links]  

# Computing the full url addresses 
full_url = [urljoin(base_site, relativeurl) for relativeurl in relative_url]

# Filter only the book links
book_url = [url for url in full_url if "https://www.goodreads.com/book/show" in url]

#### Scraping information of each book using for loop ####

book_description = []
book_author = []
book_title = []
book_rating = []
book_pages = []

#creating a loop counter
i = 0

#Loop through all 50 books
for url in book_url:
    
    #connect to url page
    note_resp = requests.get(url)
    
    #checking if the request is successful
    if note_resp.status_code == 200:
        print("URL{}: {}".format(i+1, url))
    
    else:
        print('Status code{}: Skipping URL #{}: {}'.format(note_resp.status_code, i+1, url))
        i = i+1
        continue
    
    #get HTML from url page
    note_html = note_resp.content
    
    #create beautifulsoup object for url page
    note_soup = BeautifulSoup(note_html, 'html.parser')
    
    #Extract Author particulars
    author_divs = note_soup.find_all("div", {"class":"authorName__container"})
    author_text = author_divs[0].find_all('a')[0].text
    book_author.append(author_text)
    
    #Extract title particulars
    title_divs = note_soup.find_all("div", {"class": "last col"})
    title_text = title_divs[0].find_all('h1')[0].text
    book_title.append(title_text)
    
    #Extract rating particulars
    rating_divs = note_soup.find_all("div", {"class": "uitext stacked", "id": "bookMeta"})
    rating_text = rating_divs[0].find_all("span", {"itemprop": "ratingValue"})[0].text
    book_rating.append(rating_text)
    
    #Extracting page particulars
    page_divs = note_soup.find_all("div", {"class": "row"})
    try:
        page_text = page_divs[0].find_all("span", {"itemprop": "numberOfPages"})[0].text.strip(' pages')
    except IndexError:
        page_text = 0
    book_pages.append(page_text)
    
    #Extracting description particulars
    description_divs = note_soup.find_all("div", {"class": "readable stacked", "id": "description"})
    try:
        description_text = description_divs[0].find_all("span")[1].text
    except IndexError:
        try:
            description_text = description_divs[0].find_all("span")[0].text
        except IndexError:
            description_text = "Nil"
    book_description.append(description_text)
        
    #Incremeting the loop counter
    i = i+1
    
#### Some simple data processing ####

revised_book_title = [book.strip() for book in book_title]
revised_book_rating = [float(rating.strip()) for rating in book_rating]
revised_book_pages = [int(page) for page in book_pages]
revised_book_description = [description.strip() for description in book_description]

#### Organising the data into a dataframe ####

book_df = pd.DataFrame()

book_df["Book Title"] = revised_book_title
book_df["Author"] = book_author
book_df["Rating"] = revised_book_rating
book_df["Pages"] = revised_book_pages
book_df["Description"] = revised_book_description
book_df["Links"] = book_url

#Preview dataframe
book_df.head()

# Sorting the dataframe based on ratings
sorted_book_df = book_df.sort_values(by='Rating', ascending = False)
sorted_book_df.reset_index(drop=True, inplace = True)

# Export dataframe
sorted_book_df.to_csv("top running books.csv")