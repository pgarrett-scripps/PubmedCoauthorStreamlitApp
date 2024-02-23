import datetime
from dataclasses import dataclass
from typing import List

import pandas as pd
import streamlit as st

from pymed import PubMed

todays_date = datetime.date.today()
five_years_ago = todays_date - datetime.timedelta(days=5*365)


with st.sidebar:
    st.title("PubMed Coauthor affiliation Search")

    c1, c2 = st.columns(2)
    start_date = c1.date_input("Start date", value=five_years_ago)
    end_date = c2.date_input("End date", value=todays_date)
    author = st.text_input("Author", value="Yates, John 3rd").strip()
    max_results = st.number_input("Max results", value=5_000)

    query = f'(("{start_date.strftime("%Y/%m/%d")}"[Date - Create] : "{end_date.strftime("%Y/%m/%d")}"[Date - Create])) AND ({author}[Author])'

    st.write(f"Query: {query}")

    if not st.button("Search", use_container_width=True):
        st.stop()

pubmed = PubMed(tool="Author Affiliation Tool", email="pgarrett@scripps.edu")


# Execute the query against the API
results = pubmed.query(query, max_results=max_results)

@dataclass
class Author:
    name: str
    affiliation: str


@dataclass
class Article:
    title: str
    authors: List[Author]
    publication_date: str


articles = []
# Loop over the retrieved articles
for article in results:
    # Extract and format information from the article
    title = article.title

    # example authors object: [{'lastname': 'Yates', 'firstname': 'John R', 'initials': 'JR', 'affiliation': None}]
    authors = [Author(name=f"{author['firstname']} {author['lastname']}", affiliation=author['affiliation']) for author
               in article.authors]

    publication_date = article.publication_date

    # Create an Article object and append it to the list
    articles.append(Article(title=title, authors=authors, publication_date=publication_date))

# Assuming publication_date is a string that can be parsed into a datetime object,
# for example in the format "YYYY-MM-DD"
def get_latest_affiliations(articles: List[Article]) -> dict:
    author_latest_aff = {}

    for article in articles:
        pub_date = article.publication_date

        for author in article.authors:
            # Assuming author's name is unique enough for identification
            if author.name not in author_latest_aff or pub_date > author_latest_aff[author.name]['latest_pub_date']:
                author_latest_aff[author.name] = {'affiliation': author.affiliation, 'latest_pub_date': pub_date, 'title': article.title}

    return author_latest_aff


# Now, get the latest affiliation for each author
latest_affiliations = get_latest_affiliations(articles)

df = pd.DataFrame(latest_affiliations).T


st.subheader("Latest Affiliations")


st.dataframe(df)