from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from datetime import datetime, date
from itertools import groupby
from typing import List, Union, Tuple


def remove_parentheses_with_initials(text: str) -> Union[str, None]:
    """
    Remove parentheses containing initials and their contents from a string.

    :param text: The text to remove parentheses from.
    :type text: str

    :return: The text with the parentheses removed.
    :rtype: Union[str, None]

    .. python::

        # remove parentheses and their contents
        >>> remove_parentheses_with_initials('The Scripps Research Institute. (S.T., R.L., A.L., J.C., D.J., R.S.R., Y.C.).')
        'The Scripps Research Institute.'

        >>> remove_parentheses_with_initials('The Scripps Research Institute (S.T., R.L., A.L., J.C., D.J., R.S.R., Y.C.).')
        'The Scripps Research Institute.'

        >>> remove_parentheses_with_initials('The Scripps Research Institute. (TSRI)')
        'The Scripps Research Institute. (TSRI)'
    """

    if text is None:
        return None

    pattern = r"\(([A-Z]\.\,?\s?)+\)"

    # Remove the matching parentheses and their contents
    cleaned_text = re.sub(pattern, '', text)

    # More flexible handling of whitespace between dots
    cleaned_text = re.sub(r'\.\s+\.', '.', cleaned_text)

    # remove extra spaces
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

    # replace ' .' with '.'
    cleaned_text = re.sub(r'\s+\.', '.', cleaned_text)

    return cleaned_text.strip()


def extract_emails(text: str) -> Tuple[Union[str, None], Union[str, None]]:
    """
    Extract email addresses from a string and remove them from the string.

    :param text: The text to extract email addresses from.
    :type text: str

    :return: A tuple containing the cleaned text and a list of email addresses.
    :rtype: Tuple[Union[str, None], Union[List[str], None]]

    .. python::

        # extract email addresses from a string
        >>> extract_emails('The Scripps Research Institute. Electronic address: pgarrett@scripps.edu.')
        ('The Scripps Research Institute.', ['pgarrett@scripps.edu'])

        >>> extract_emails('The Scripps Research Institute. Electronic address: pgarrett@scripps.edu')
        ('The Scripps Research Institute.', ['pgarrett@scripps.edu'])
    """

    if text is None:
        return None, None

    # Regular expression to match email addresses
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    # Find all email addresses using the regex
    emails = re.findall(email_regex, text)

    # Remove the email addresses from the text
    cleaned_text = re.sub(email_regex, '', text)

    # also remove  'Electronic address:'
    cleaned_text = re.sub(r'Electronic address:', '', cleaned_text)

    # More flexible handling of whitespace between dots
    cleaned_text = re.sub(r'\.\s+\.', '.', cleaned_text)

    # remove extra spaces
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

    # remove leading and trailing whitespace
    cleaned_text = cleaned_text.strip()

    email_str = ';'.join(emails) if emails else None

    return cleaned_text, email_str


def clean_affiliations(affiliation: str) -> Union[None, str]:
    """
    Clean up an affiliation string.

    :param affiliation: The affiliation string to clean.
    :type affiliation: str

    :return: The cleaned affiliation string.
    :rtype: Union[None, str]

    .. python::

        # remove parentheses and their contents
        >>> clean_affiliations('The Scripps Research Institute (XX Y,X), La Jolla, CA 92037, USA')
        'The Scripps Research Institute, La Jolla, CA 92037, USA'

        # replace newlines with '; '
        >>> clean_affiliations('The Scripps Research Institute, La Jolla, CA 92037, USA\\nAnother Affiliation')
        'The Scripps Research Institute, La Jolla, CA 92037, USA; Another Affiliation'

        # remove extra spaces
        >>> clean_affiliations('The Scripps    Research Institute, La Jolla, CA 92037, USA')
        'The Scripps Research Institute, La Jolla, CA 92037, USA'
    """

    if affiliation is None:
        return None

    if not isinstance(affiliation, str):
        raise ValueError(f"Affiliation must be a string, not {type(affiliation)}. Affiliation: {affiliation}")

    # replace newlines with '; '
    affiliation = affiliation.replace('\n', '; ')

    # replace ' ,' with ','
    affiliation = re.sub(r'\s+,', ',', affiliation)

    # remove extra spaces
    affiliation = re.sub(r'\s+', ' ', affiliation)

    # remove leading and trailing whitespace
    affiliation = affiliation.strip()

    return affiliation


def split_camel_case(affiliation: str) -> Union[None, str]:
    """
    Add a space between the lowercase and uppercase letter, and numbers and uppercase letters.

    :param affiliation: The affiliation string to clean.
    :type affiliation: str

    :return: The cleaned affiliation string.
    :rtype: Union[None, str]

    .. python::

        # fix zipcodes without a preceeding space
        >>> split_camel_case('The Scripps Research Institute, La Jolla, CA92037, USA')
        'The Scripps Research Institute, La Jolla, CA 92037, USA'

        >>> split_camel_case('The Scripps Research Institute, La Jolla, CA75390-8505, USA')
        'The Scripps Research Institute, La Jolla, CA 75390-8505, USA'

        # Replacement to add space between the lowercase and uppercase letter
        >>> split_camel_case('The ScrippsResearch Institute, La Jolla, CA 92037, USA')
        'The Scripps Research Institute, La Jolla, CA 92037, USA'

        # Replacement to add space between the digit and the uppercase letter
        >>> split_camel_case('Royal Institute of Technology 114 28Stockholm Sweden.')
        'Royal Institute of Technology 114 28 Stockholm Sweden.'

        >>> split_camel_case('Institute for Systems Biology SeattleWashington98109 USA.')
        'Institute for Systems Biology Seattle Washington 98109 USA.'

        >>> split_camel_case('National Institute of Standards and Technology CharlestonSouth Carolina29412 USA.')
        'National Institute of Standards and Technology Charleston South Carolina 29412 USA.'

        >>> split_camel_case('Rochester Institute of Technology RochesterNew York14623 USA.')
        'Rochester Institute of Technology Rochester New York 14623 USA.'

        >>> split_camel_case('UMass Chan Medical School WorcesterMassachusetts01655 USA.')
        'UMass Chan Medical School Worcester Massachusetts 01655 USA.'

        >>> split_camel_case('Genome Campus HinxtonCambridgeCB10 1SD United Kingdom.')
        'Genome Campus Hinxton Cambridge CB10 1SD United Kingdom.'

        >>> split_camel_case('University of Minnesota MinneapolisMinnesota55455 USA.')
        'University of Minnesota Minneapolis Minnesota 55455 USA.'

        >>> split_camel_case('Protein Metrics LLC ChandlerTexas75758 USA.')
        'Protein Metrics LLC Chandler Texas 75758 USA.'

    """

    if affiliation is None:
        return None

    # fix zipcodes without a preceding space
    affiliation = re.sub(r'([a-zA-Z])(\d{5})', r'\1 \2', affiliation)

    # Fix for 'SanDiego' -> 'San Diego'
    affiliation = re.sub(r"([a-z])([a-z])([A-Z])([a-z])", r"\1\2 \3\4", affiliation)

    # Fix for 'SacramentoSD' -> 'Sacramento SD'
    affiliation = re.sub(r"([a-z])([a-z])([A-Z])([A-Z])", r"\1\2 \3\4", affiliation)

    # Replacement to add space between the digit and the uppercase letter
    affiliation = re.sub(r"([0-9])([A-Z])([a-z])", r"\1 \2\3", affiliation)

    return affiliation


@dataclass(frozen=True)
class Author:
    last_name: str | None
    first_name: str | None
    initials: str | None
    affiliation: str | None
    affiliation_date: date
    publication_title: str | None

    @property
    def name(self):
        if self.last_name is None and self.first_name is None:
            return None

        if self.last_name is None:
            return self.first_name

        if self.first_name is None:
            return self.last_name

        return f"{self.last_name}, {self.first_name}"

    def to_dict(self):
        # Convert the dataclass fields to a dictionary
        data = asdict(self)
        # Add any additional properties
        data['name'] = self.name
        return data


def get_latest_affiliations(authors: List[Author], skip_none_affiliations: bool) -> List[Author]:
    """
    Get the latest affiliation for each author.

    :param authors: A list of authors.
    :type authors: List[Author]
    :param skip_none_affiliations: Whether to skip authors with no affiliation.
    :type skip_none_affiliations: bool

    :return: A list of authors with the latest affiliation.
    :rtype: List[Author]

    .. python::

        # get the latest affiliation for each author
        >>> a1 = Author(last_name='Yates', first_name='John R', initials='JR', affiliation='TSRI', affiliation_date='2021-01-01', publication_title='Title 1')
        >>> a2 = Author(last_name='Yates', first_name='John R', initials='JR', affiliation='TSRI', affiliation_date='2021-01-02', publication_title='Title 2')
        >>> a3 = Author(last_name='Yates', first_name='John R', initials='JR', affiliation='TSRI', affiliation_date='2021-01-03', publication_title='Title 3')

        >>> get_latest_affiliations([a1, a2, a3], skip_none_affiliations=False)
        [Author(last_name='Yates', first_name='John R', initials='JR', affiliation='TSRI', affiliation_date='2021-01-03', publication_title='Title 3')]

        >>> a4 = Author(last_name='Yates', first_name='John R', initials='JR', affiliation=None, affiliation_date='2021-01-04', publication_title='Title 4')

        >>> get_latest_affiliations([a1, a2, a3, a4], skip_none_affiliations=True)
        [Author(last_name='Yates', first_name='John R', initials='JR', affiliation='TSRI', affiliation_date='2021-01-03', publication_title='Title 3')]

        >>> get_latest_affiliations([a1, a2, a3, a4], skip_none_affiliations=False)
        [Author(last_name='Yates', first_name='John R', initials='JR', affiliation=None, affiliation_date='2021-01-04', publication_title='Title 4')]

    """
    # Use groupby to group authors by lastname and firstname, then pick the first from each group
    authors_sorted = sorted(authors, key=lambda x: (x.name, x.affiliation_date), reverse=True)
    unique_authors_with_latest_publication = []
    for key, group in groupby(authors_sorted, key=lambda x: x.name):
        group_authors = list(group)
        if skip_none_affiliations:
            if all(author.affiliation is None for author in group_authors):  # all affiliations are None
                unique_authors_with_latest_publication.append(group_authors[0])
            else:
                for group_author in group_authors:
                    if group_author.affiliation is not None:
                        unique_authors_with_latest_publication.append(group_author)
                        break
        else:
            unique_authors_with_latest_publication.append(group_authors[0])

    return unique_authors_with_latest_publication
