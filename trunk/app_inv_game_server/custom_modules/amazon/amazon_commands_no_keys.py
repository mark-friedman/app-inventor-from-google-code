# Copyright 2010 Google Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#      http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Looks up books on Amazon by keyword or ISBN

Uses a library originally downloaded from
http://blog.umlungu.co.uk/blog/2009/jul/12/pyaws-adding-request-authentication/
to access AWS E-Commerce Service API's and retrieve book results
for searches by keyword and ISBN number.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>',
               '"Dave Wolber" <wolber@usfca.edu>']


# This file has had its license and secret keys removed and will not function.
license_key = ''
secret_key = ''

from pyaws import ecs

return_limit = 5

def keyword_search_command(model, player, arguments):
  """ Return books by keyword.

  Args:
    model: Not used, can be anything.
    player: Not used, can be anything.
    arguments: A one item list containing the keywords to search for.

  Returns:
    A list of three item lists. Each sublist represents
    a result and includes the book title, its lowest found
    price and its ASIN number.
  """
  return amazon_by_keyword(arguments[0])

def isbn_search_command(model, player, arguments):
  """ Return a book result by ISBN number.

  Args:
    model: Not used, can be anything.
    player: Not used, can be anything.
    arguments: A one item list containing the keywords to search for.

  Returns:
    A list with a single sublist representing the book found.
    The sublist contains the book title, its lowest found
    price and its ASIN number.

  Raises:
    ValueError if the ISBN number is invalid.
  """
  return amazon_by_isbn(arguments[0])

def amazon_by_keyword(keyword):
  """ Use the ecs library to search for books by keyword.

  Args:
    keyword: A string of keyword(s) to search for.

  Returns:
    A list of three item lists. Each sublist represents
    a result and includes the book title, its lowest found
    price and its ASIN number.
  """
  ecs.setLicenseKey(license_key)
  ecs.setSecretKey(secret_key)
  ecs.setLocale('us')

  books = ecs.ItemSearch(keyword, SearchIndex='Books', ResponseGroup='Medium')
  return format_output(books)

def amazon_by_isbn(isbn):
  """ Use the ecs library to search for books by ISBN number.

  Args:
    isbn: The 10 digit ISBN number to look up.

  Returns:
    A list with a single sublist representing the book found.
    The sublist contains the book title, its lowest found
    price and its ASIN number.

  Raises:
    ValueError if the ISBN number is invalid.
  """
  ecs.setLicenseKey(license_key)
  ecs.setSecretKey(secret_key)
  ecs.setLocale('us')
  try:
    books = ecs.ItemLookup(isbn, IdType='ISBN', SearchIndex='Books',
                           ResponseGroup='Medium')
    return format_output(books)
  except ecs.InvalidParameterValue:
    raise ValueError('Invalid ISBN')

def format_output(books):
  """ Return a formatted output list from an iterator returned by ecs.

  Args:
    books: An iterator of book results from the ecs library.

  Returns:
    A list of three item lists. Each sublist represents
    a result and includes the book title, its lowest found
    price and its ASIN number.
  """
  size = min(len(books), return_limit)
  return [[books[i].Title, get_amount(books[i]), books[i].ASIN]
          for i in xrange(size)]

def get_amount(book):
  """ Return the lowest price found or 'Not found.' if none exists. """
  try:
    if book.OfferSummary and book.OfferSummary.LowestNewPrice:
      return book.OfferSummary.LowestNewPrice.FormattedPrice
  except:
    return 'Not found.'
