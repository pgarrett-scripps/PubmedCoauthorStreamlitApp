import datetime
from dataclasses import dataclass
from typing import List

import pandas as pd
import streamlit as st

from pymed import PubMed

# set page title
st.set_page_config(page_title="PubMed Affiliation Tool", page_icon=":microscope:")

todays_date = datetime.date.today()
five_years_ago = todays_date - datetime.timedelta(days=5*365)


with st.sidebar:
    st.title("PubMed Affiliation Tool :microscope:")
    st.markdown("This tool uses the pymed python package to search PubMed for articles by author and date. "
             "It then analyzes these articles to extract the most recent affiliations of the co-authors.")

    st.caption("Built by Patrick Garrett based on code from Andy Jones.")

    c1, c2 = st.columns(2)
    start_date = c1.date_input("Start date", value=five_years_ago, help="The start date for the search (inclusive).")
    end_date = c2.date_input("End date", value=todays_date, help="The end date for the search (inclusive).")
    author = st.text_input("Author", value="Yates, John 3rd", help="The author to search for.")
    max_results = st.number_input("Max results", value=5_000, help="The maximum number of results to return.")
    skip_none_affiliations = st.checkbox("Remove Missing Affiliations", value=True, help="Remove affiliations that are missing.")

    if start_date > end_date:
        st.error("Start date must be before end date.")
        st.stop()

    query = f'(("{start_date.strftime("%Y/%m/%d")}"[Date - Create] : "{end_date.strftime("%Y/%m/%d")}"[Date - Create])) AND ({author}[Author])'

    if not st.button("Search", use_container_width=True):
        st.stop()

    st.caption("PubMed API Query:")
    st.caption(query)

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

                if skip_none_affiliations and author.affiliation is None:
                    continue
                author_latest_aff[author.name] = {'affiliation': author.affiliation, 'latest_pub_date': pub_date, 'title': article.title}

    return author_latest_aff


# Now, get the latest affiliation for each author
latest_affiliations = get_latest_affiliations(articles)

df = pd.DataFrame(latest_affiliations).T


st.subheader("Affiliations:")

st.dataframe(df)

document_name = f"{author.replace(' ', '')}_affiliations_{start_date.strftime('%Y_%m_%d')}_{end_date.strftime('%Y_%m_%d')}.csv"

st.download_button(
    label="Download CSV",
    data=df.to_csv().encode(),
    file_name=document_name,
    mime="text/csv",
    use_container_width=True
)