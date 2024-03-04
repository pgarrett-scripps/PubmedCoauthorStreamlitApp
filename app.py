import datetime
from typing import List, Tuple
import pandas as pd
import streamlit as st
from pymed import PubMed

from util import clean_affiliations, extract_emails, split_camel_case, remove_parentheses_with_initials, Author, \
    get_latest_affiliations

# set page title
st.set_page_config(page_title="PubMed Affiliations", page_icon=":microscope:", initial_sidebar_state="expanded")

current_date = datetime.date.today()
five_years_ago = current_date - datetime.timedelta(days=5 * 365)

with st.sidebar:
    st.title("PubMed Affiliations :microscope:")
    st.markdown("This tool uses the pymed python package to search PubMed for articles by author and date. "
                "It then analyzes these articles to extract the most recent affiliation for each coauthor.")

    st.caption("Built by Patrick Garrett based on code from Andy Jones.")
    st.caption(
        "Contact [pgarrett@scripps.edu](mailto:pgarrett@scripps.edu) | Github: [PubmedAffiliations](https://github.com/pgarrett-scripps/PubmedCoauthorStreamlitApp)")

    c1, c2 = st.columns(2)
    start_date = c1.date_input("Start date", value=five_years_ago, help="The start date for the search (inclusive).",
                               min_value=current_date - datetime.timedelta(days=100 * 365),
                               max_value=current_date)
    end_date = c2.date_input("End date", value=current_date, help="The end date for the search (inclusive).",
                             min_value=current_date - datetime.timedelta(days=100 * 365), max_value=current_date)

    if start_date > end_date:
        st.error("Start date must be before end date.")
        st.stop()

    c1, c2 = st.columns(2)
    query_author = c1.text_input("Name (Last, First)", value="Yates, John 3rd", help="The author to search for.")
    author_option = c2.radio("Author Filter", ["First", "Last", "Any"], index=2, horizontal=True,
                             help="Filter articles based on the author's position.")

    if query_author == "" or query_author is None or query_author == " " or len(query_author) < 3:
        st.error("Please enter a valid author name. Author name must be > 3 characters.")
        st.stop()

    with st.expander("Additional Options"):

        max_results = st.number_input("Max Articles", value=500, help="The maximum number of articles to analyze.",
                                      max_value=10000)

        skip_none_affiliations = st.checkbox("Skip Missing Affiliations", value=True,
                                             help="This option controls how the tool handles articles with missing author "
                                                  "affiliation information. "
                                                  "If enabled, the tool will not update an author's latest affiliation to "
                                                  "'None' if the affiliation data "
                                                  "is missing in a newer article. Instead, it retains the most recent "
                                                  "available affiliation. "
                                                  "This ensures that authors without updated affiliation information in "
                                                  "some articles are still "
                                                  "associated with their last known affiliation.")

        st.caption('Leave The following options checked unless you are experiencing issues with the data.')
        should_extract_emails = st.checkbox("Extract and Remove Emails", value=True,
                                            help="Extract and Remove email addresses from affiliations.")
        should_clean_affiliations = st.checkbox("Clean Affiliations", value=True,
                                                help="Clean up the affiliations. Fixes misplaced periods, extra spaces, "
                                                     "and separates multiple affiliations by ;")
        should_split_camel_case = st.checkbox("Split Camel Case", value=True,
                                              help="Add a space between the lowercase and uppercase letter, and numbers "
                                                   "and uppercase letter. For example SanDiegoCalifornia would become "
                                                   "San Diego California")
        should_remove_initials = st.checkbox("Remove Initials", value=True,
                                             help="Remove initials contained in parentheses from the affiliations. "
                                                  "Example: (XX Y,X)")

    if not st.button("Search", use_container_width=True):
        st.stop()

    if author_option == "First":
        author_tag = '1au'
    elif author_option == "Last":
        author_tag = 'lastau'
    elif author_option == "Any":
        author_tag = 'au'
    else:
        st.error("Invalid author option.")
        st.stop()

    st.caption("PubMed API Query:")
    query = f'(("{start_date.strftime("%Y/%m/%d")}"[Date - Create] : "{end_date.strftime("%Y/%m/%d")}' \
            f'"[Date - Create])) AND ({query_author}[{author_tag}])'
    st.caption(query)


@st.cache_data
def query_pubmed(query: str, max_results: int) -> Tuple[List[Author], int]:
    pubmed = PubMed(tool="Author Affiliation Tool", email="pgarrett@scripps.edu")

    results = pubmed.query(query, max_results=max_results)
    num_articles = 0
    authors = []
    # Loop over the retrieved articles
    for article in results:
        # Extract and format information from the article
        title = article.title
        publication_date = article.publication_date

        if isinstance(publication_date, datetime.date):
            pass

        if isinstance(publication_date, str):
            publication_date = datetime.datetime.strptime(publication_date, '%Y')  # some articles only have the year

            # convert to date
            publication_date = publication_date.date()

            if publication_date < start_date or publication_date > end_date:
                continue

        # example authors object: [{'lastname': 'Yates', 'firstname': 'John R', 'initials': 'JR', 'affiliation': None}]
        authors.extend([Author(last_name=author.get('lastname', None),
                               first_name=author.get('firstname', None),
                               initials=author.get('initials', None),
                               affiliation=author.get('affiliation', None),
                               affiliation_date=publication_date,
                               publication_title=title) for author in article.authors])

        num_articles += 1

    return authors, num_articles


def mock_query_pubmed(query: str, max_results: int) -> Tuple[List[Author], int]:
    df = pd.read_csv("mock_data.csv")

    # fill nan with None
    df = df.where(pd.notna(df), None)

    num_articles = len(df['publication_title'].unique())
    authors = []
    for _, row in df.iterrows():
        authors.append(Author(last_name=row['last_name'],
                              first_name=row['first_name'],
                              initials=row['initials'],
                              affiliation=row['affiliation'],
                              affiliation_date=row['affiliation_date'],
                              publication_title=row['publication_title']))

    return authors, num_articles


if query_author == 'MOCK DATA':
    authors, num_articles = mock_query_pubmed(query, max_results)
else:
    authors, num_articles = query_pubmed(query, max_results)

if num_articles == 0:
    st.error("No articles found for the given query.")
    st.stop()

if len(authors) == 0:
    st.error("No authors found in the articles.")
    st.stop()

if num_articles >= max_results:
    st.warning(f"Retrieved {num_articles} / {max_results} articles. Consider increasing the max articles to get more results.")
    st.warning("This may also be an indication that the author name is too broad.")


starting_authors = len(authors)

with st.expander("Raw Data"):
    st.markdown("<h1 style='text-align: center;'>All Affiliations</h1>", unsafe_allow_html=True)
    df = pd.DataFrame([author.to_dict() for author in authors])

    st.dataframe(df)

    document_name = f"{query_author.replace(' ', '')}_all_affiliations_{start_date.strftime('%Y_%m_%d')}_" \
                    f"{end_date.strftime('%Y_%m_%d')}.csv"

    st.download_button(
        label="Download CSV",
        data=df.to_csv().encode(),
        file_name=document_name,
        mime="text/csv",
        use_container_width=True
    )

# remove authors with invalid names
authors = [author for author in authors if author.first_name is not None or author.last_name is not None]
st.caption(f"Found {num_articles} articles with {len(authors)} coauthors.")
st.caption(f"Removed {starting_authors - len(authors)} coauthors with no name.")

author_affiliation_counts = {}
for author in authors:
    author_affiliation_counts[author.name] = author_affiliation_counts.get(author.name, 0) + 1

unique_authors_with_latest_publication = get_latest_affiliations(authors, skip_none_affiliations)
latest_affiliation_df = pd.DataFrame([author.to_dict() for author in unique_authors_with_latest_publication])
latest_affiliation_df['affiliation_count'] = latest_affiliation_df['name'].map(author_affiliation_counts)

try:
    if should_clean_affiliations:
        latest_affiliation_df['affiliation'] = latest_affiliation_df['affiliation'].map(clean_affiliations)
except ValueError as e:
    st.error(f"Error cleaning affiliations: {e}. Consider Unselecting this option.")
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
        latest_affiliation_df['affiliation'] = latest_affiliation_df['affiliation'].map(
            remove_parentheses_with_initials)
except ValueError:
    st.error("Error removing initials. Consider Unselecting this option.")
    st.stop()

st.markdown("<h1 style='text-align: center;'>Latest Affiliations</h1>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Total Coauthors", len(authors))
c2.metric("Unique Coauthors", len(set([a.name for a in authors])))
c3.metric("Missing Affiliations", latest_affiliation_df['affiliation'].isna().sum())
st.dataframe(latest_affiliation_df)

document_name = f"{query_author.replace(' ', '')}_latest_affiliations_{start_date.strftime('%Y_%m_%d')}_" \
                f"{end_date.strftime('%Y_%m_%d')}.csv"

st.download_button(
    label="Download CSV",
    data=latest_affiliation_df.to_csv().encode(),
    file_name=document_name,
    mime="text/csv",
    use_container_width=True
)
