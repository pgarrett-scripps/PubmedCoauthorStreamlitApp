import datetime
from typing import List
import pandas as pd
import streamlit as st
from pymed import PubMed

from util import clean_affiliations, extract_emails, split_camel_case, remove_parentheses_with_initials, Author, \
    get_latest_affiliations

# set page title
st.set_page_config(page_title="PubMed Affiliations", page_icon=":microscope:")

todays_date = datetime.date.today()
five_years_ago = todays_date - datetime.timedelta(days=5 * 365)

with st.sidebar:
    st.title("PubMed Affiliations :microscope:")
    st.markdown("This tool uses the pymed python package to search PubMed for articles by author and date. "
                "It then analyzes these articles to extract the most recent affiliations of the co-authors.")

    st.caption("Built by Patrick Garrett based on code from Andy Jones.")

    c1, c2 = st.columns(2)
    start_date = c1.date_input("Start date", value=five_years_ago, help="The start date for the search (inclusive).")
    end_date = c2.date_input("End date", value=todays_date, help="The end date for the search (inclusive).")
    query_author = st.text_input("Name (Last, First)", value="Yates, John 3rd", help="The author to search for.")

    max_results = st.number_input("Max Articles", value=5_000, help="The maximum number of articles to analyze.")

    skip_none_affiliations = st.checkbox("Skip Missing Affiliations", value=True,
                                         help="This option controls how the tool handles articles with missing author affiliation information. "
                                              "If enabled, the tool will not update an author's latest affiliation to 'None' if the affiliation data "
                                              "is missing in a newer article. Instead, it retains the most recent available affiliation. "
                                              "This ensures that authors without updated affiliation information in some articles are still "
                                              "associated with their last known affiliation.")
    with st.expander("Additional Options"):

        st.caption('Leave these options checked unless you are experiencing issues with the data.')
        should_extract_emails = st.checkbox("Extract and Remove Emails", value=True, help="Extract and Remove email addresses from affiliations.")
        should_clean_affiliations = st.checkbox("Clean Affiliations", value=True, help="Clean up the affiliations. Fixes misplaced periods, extra spaces, and separates multiple affiliations by ;")
        should_split_camel_case = st.checkbox("Split Camel Case", value=True, help="Add a space between the lowercase and uppercase letter, and numbers and uppercase letter. For example SanDiegoCalifornia would become San Diego California")
        should_remove_initials = st.checkbox("Remove Initials", value=True, help="Remove initials contained in parentheses from the affiliations. Example: (XX Y,X)")

    if start_date > end_date:
        st.error("Start date must be before end date.")
        st.stop()

    query = f'(("{start_date.strftime("%Y/%m/%d")}"[Date - Create] : "{end_date.strftime("%Y/%m/%d")}"[Date - Create])) AND ({query_author}[Author])'

    if not st.button("Search", use_container_width=True):
        st.stop()

    st.caption("PubMed API Query:")
    st.caption(query)


@st.cache_data
def query_pubmed(query: str, max_results: int) -> List:
    pubmed = PubMed(tool="Author Affiliation Tool", email="pgarrett@scripps.edu")

    results = pubmed.query(query, max_results=max_results)

    authors = []
    # Loop over the retrieved articles
    for article in results:
        # Extract and format information from the article
        title = article.title
        publication_date = article.publication_date

        # example authors object: [{'lastname': 'Yates', 'firstname': 'John R', 'initials': 'JR', 'affiliation': None}]
        authors.extend([Author(last_name=author.get('lastname', None),
                               first_name=author.get('firstname', None),
                               initials=author.get('initials', None),
                               affiliation=author.get('affiliation', None),
                               affiliation_date=publication_date,
                               publication_title=title) for author in article.authors])

    return authors


authors = query_pubmed(query, max_results)

with st.expander("Raw Data"):
    st.markdown("<h1 style='text-align: center;'>All Affiliations</h1>", unsafe_allow_html=True)
    df = pd.DataFrame([author.to_dict() for author in authors])

    st.dataframe(df)

    document_name = f"{query_author.replace(' ', '')}_all_affiliations_{start_date.strftime('%Y_%m_%d')}_{end_date.strftime('%Y_%m_%d')}.csv"

    st.download_button(
        label="Download CSV",
        data=df.to_csv().encode(),
        file_name=document_name,
        mime="text/csv",
        use_container_width=True
    )

# Step 1: Sort authors by name and publication date
author_affiliation_counts = {}
for author in authors:
    author_affiliation_counts[author.name] = author_affiliation_counts.get(author.name, 0) + 1

unique_authors_with_latest_publication = get_latest_affiliations(authors, skip_none_affiliations)

latest_affiliation_df = pd.DataFrame([author.to_dict() for author in unique_authors_with_latest_publication])
latest_affiliation_df['affiliation_count'] = latest_affiliation_df['name'].map(author_affiliation_counts)

try:
    if should_clean_affiliations:
        latest_affiliation_df['affiliation'] = latest_affiliation_df['affiliation'].map(clean_affiliations)
except ValueError:
    st.error("Error cleaning affiliations. Consider Unselecting this option.")
    st.stop()


try:
    if should_extract_emails:
        latest_affiliation_df['affiliation'], latest_affiliation_df['email'] = zip(
            *latest_affiliation_df['affiliation'].map(extract_emails))
except ValueError:
    st.error("Error extracting emails. Consider Unselecting this option.")
    st.stop()


try:
    if should_split_camel_case:
        latest_affiliation_df['affiliation'] = latest_affiliation_df['affiliation'].map(split_camel_case)
except ValueError:
    st.error("Error splitting camel case. Consider Unselecting this option.")
    st.stop()

try:
    if should_remove_initials:
        latest_affiliation_df['affiliation'] = latest_affiliation_df['affiliation'].map(remove_parentheses_with_initials)
except ValueError:
    st.error("Error removing initials. Consider Unselecting this option.")
    st.stop()


st.markdown("<h1 style='text-align: center;'>Latest Affiliations</h1>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Total Coauthors", len(authors))
c2.metric("Unique Coauthors", len(set([a.name for a in authors])))
c3.metric("Missing Affiliations", latest_affiliation_df['affiliation'].isna().sum())
st.dataframe(latest_affiliation_df)

document_name = f"{query_author.replace(' ', '')}_latest_affiliations_{start_date.strftime('%Y_%m_%d')}_{end_date.strftime('%Y_%m_%d')}.csv"

st.download_button(
    label="Download CSV",
    data=latest_affiliation_df.to_csv().encode(),
    file_name=document_name,
    mime="text/csv",
    use_container_width=True
)
