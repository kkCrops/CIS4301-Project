from MARIADB_CREDS import DB_CONFIG
from mariadb import connect
from models.LoanHistory import LoanHistory
from models.Waitlist import Waitlist
from models.Book import Book
from models.Loan import Loan
from models.User import User

UFID = "82071356"
FULLNAME = "Liang, Karen"

conn = connect(user=DB_CONFIG["username"], password=DB_CONFIG["password"], host=DB_CONFIG["host"],
               # , collation='utf8mb4_unicode_ci')
               database=DB_CONFIG["database"], port=DB_CONFIG["port"])

cur = conn.cursor()


def add_book(new_book: Book = None):
    """
    new_book - A Book object containing a new book to be inserted into the DB in the Books table.
        new_book and its attributes will never be None.
    """
    cur.execute("INSERT INTO Book (isbn, title, author, publication_year, publisher, num_owned) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                [new_book.isbn, new_book.title, new_book.author, new_book.publication_year, new_book.publisher, new_book.num_owned])


def add_user(new_user: User = None):
    """
    new_user - A User object containing a new user to be inserted into the DB in the Users table.
        new_user and its attributes will never be None.
    """
    cur.execute("INSERT INTO User (account_id, name, address, phone_number, email) "
                "VALUES (%s, %s, %s, %s, %s)",
                [new_user.account_id, new_user.name, new_user.address, new_user.phone_number, new_user.email])


def edit_user(original_account_id: str = None, new_user: User = None):
    """
    original_account_id - A string containing the account id for the user to be edited. e.g. if the original_account_id =
        "f3aa549b042a", then all attributes that are being updated should be applied to the user in the DB with account_id ==
        "f3aa549b042a". original_account_id will never be None
    new_user - A User object containing attributes to update for a user in the database. If an attribute is None,
        then it should not be altered. e.g. if new_user.name = "John" then the user with the same account_id as
        original_account_id should have their name updated to "John". If filter_attributes.name = None, then the name should
        not be altered. new_user will never be None, but any attribute not being updated will be None.
    """

    my_query = "UPDATE User SET "
    my_values = []

    if new_user.name is not None:
        my_query += "name = %s, "
        my_values.append(new_user.name)

    if new_user.address is not None:
        my_query += "address = %s, "
        my_values.append(new_user.address)

    if new_user.phone_number is not None:
        my_query += "phone_number = %s, "
        my_values.append(new_user.phone_number)

    if new_user.email is not None:
        my_query += "email = %s, "
        my_values.append(new_user.email)

    if len(my_values) == 0:
        return  # no attributes updating
    my_query = my_query[:-2]
    my_query += " WHERE account_id = %s"
    my_values.append(original_account_id)
    cur.execute(my_query, my_values)


def checkout_book(isbn: str = None, account_id: str = None):
    """
    isbn - A string containing the ISBN for the book being checked out. isbn will never be None.
    account_id - A string containing the account id of the user checking out a book. account_id will never be None.
    """
    cur.execute("INSERT INTO Loan (isbn, account_id, checkout_date, due_date)"
                "VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY))",
                [isbn, account_id])


def waitlist_user(isbn: str = None, account_id: str = None) -> int:
    """
    isbn - A string containing the ISBN for the book that a user desires to be waitlisted for. isbn will never be None.
    account_id - A string containing the account id for the user that wants to be waitlisted. account_id will never be None.

    returns an integer that is the user's place in line to check out the book.
    """
    cur.execute("SELECT MAX(place_in_line) "
                "FROM Waitlist "
                "WHERE isbn = %s",
                [isbn])

    position = cur.fetchone()

    if position[0] is None:
        new_position = 1
    else:
        new_position = position[0] + 1

    cur.execute("INSERT INTO Waitlist (isbn, account_id, place_in_line) "
                "VALUES (%s, %s, %s)",
                [isbn, account_id, new_position])
    return new_position


def update_waitlist(isbn: str = None):
    """
    isbn - A string containing the ISBN for a book on the waitlist. isbn will never be None.
    """
    cur.execute("DELETE FROM Waitlist "
                "WHERE isbn = %s AND place_in_line = 1",
                [isbn])  # delete first person in line
    cur.execute("UPDATE Waitlist "
                "SET place_in_line = place_in_line - 1 "
                "WHERE isbn = %s AND place_in_line > 1",
                [isbn])  # move everyone else in line up one spot


def return_book(isbn: str = None, account_id: str = None):
    """
    isbn - A string containing the ISBN for the book that the user desires to return. isbn will never be None
    account_id - A string containing the account id for the user that wants to return the book. account_id will never be None
    """
    cur.execute("INSERT INTO LoanHistory (isbn, account_id, checkout_date, due_date, return_date) "
                "SELECT isbn, account_id, checkout_date, due_date, CURDATE() "
                "FROM Loan WHERE isbn = %s AND account_id = %s", [isbn, account_id])
    cur.execute("DELETE FROM Loan WHERE isbn = %s AND account_id = %s", [
                isbn, account_id])


def grant_extension(isbn: str = None, account_id: str = None):
    """
    isbn - A string containing the ISBN for a book. isbn will never be None.
    account_id - A string containing the account id for a user. account_id will never be None.
    """
    cur.execute("UPDATE Loan "
                "SET due_date = DATE_ADD(due_date, INTERVAL 14 DAY) "
                "WHERE isbn = %s AND account_id = %s",
                [isbn, account_id])


def get_filtered_books(filter_attributes: Book = None,
                       use_patterns: bool = False,
                       min_publication_year: int = -1,
                       max_publication_year: int = -1) -> list[Book]:
    """
    filter_attributes - A Book object containing attributes to filter books in the database. If an attribute is None,
        then it should not be considered for the search. e.g. if filter_attributes.title = "1984" then all books returned
        should have their title == "1984". If filter_attributes.author = None, then we do not care what the author is when
        filtering. It is important to note that filter_attributes.publication_year will always be -1 since we have
        separate parameters to handle publication_year. It is also worth noting that since num_owned is an integer, it
        can't be None, so it will default to -1 instead when not used. Additionally, many attributes may be used as a
        filter simultaneously. filter_attributes will never be None, but any attribute not being used as a filter will be None.
        It is also possible all the attributes in filter_attributes to be None, if that is the case then all rows should be returned.
    use_patterns - If True, then the string attributes in filter_attributes may contain string patterns rather than typical
        string literals, so the filtering should handle this accordingly. e.g. if filter_attributes.title = "The Great%" and
        use_patterns = True, then all Books returned should have their title start with "The Great%". If use_patterns = False,
        then all books returned should have their title == "The Great%".
    min_publication_year - The minimum publication year to filter books by, inclusively. e.g. if min_publication_year = 2000,
        then all books should be published between 2000 and the current year, including 2000 and the current year. If
        min_publication_year is not used, it will be -1.
    max_publication_year - The maximum publication year to filter books by, inclusively. e.g. if max_publication_year = 1999,
        then all books should be published before the year 2000, not including 2000. If max_publication_year is not used,
        it will be -1.

    returns a list of Book objects with books that meet the qualifications of the filtered attributes. If no books meet the
        requirements, then an empty list is returned.
    """
    my_query = "SELECT isbn, title, author, publication_year, publisher, num_owned FROM Book"
    my_values = []

    if filter_attributes.isbn is not None:
        if len(my_values) == 0:
            my_query += " WHERE isbn"
        else:
            my_query += " AND isbn"
        if use_patterns:
            my_query += " LIKE %s"
        else:
            my_query += " = %s"
        my_values.append(filter_attributes.isbn)

    if filter_attributes.title is not None:
        if len(my_values) == 0:
            my_query += " WHERE title"
        else:
            my_query += " AND title"
        if use_patterns:
            my_query += " LIKE %s"
        else:
            my_query += " = %s"
        my_values.append(filter_attributes.title)

    if filter_attributes.author is not None:
        if len(my_values) == 0:
            my_query += " WHERE author"
        else:
            my_query += " AND author"
        if use_patterns:
            my_query += " LIKE %s"
        else:
            my_query += " = %s"
        my_values.append(filter_attributes.author)

    if filter_attributes.publisher is not None:
        if len(my_values) == 0:
            my_query += " WHERE publisher"
        else:
            my_query += " AND publisher"
        if use_patterns:
            my_query += " LIKE %s"
        else:
            my_query += " = %s"
        my_values.append(filter_attributes.publisher)

    if filter_attributes.num_owned != -1:
        if len(my_values) == 0:
            my_query += " WHERE num_owned = %s"
        else:
            my_query += " AND num_owned = %s"
        my_values.append(filter_attributes.num_owned)

    if min_publication_year != -1:
        if len(my_values) == 0:
            my_query += " WHERE publication_year >= %s"
        else:
            my_query += " AND publication_year >= %s"
        my_values.append(min_publication_year)

    if max_publication_year != -1:
        if len(my_values) == 0:
            my_query += " WHERE publication_year <= %s"
        else:
            my_query += " AND publication_year <= %s"
        my_values.append(max_publication_year)
    cur.execute(my_query, my_values)

    search_results = []
    for (isbn, title, author, publication_year, publisher, num_owned) in cur:
        search_results.append(
            Book(isbn, title, author, publication_year, publisher, num_owned))
    return search_results


def get_filtered_users(filter_attributes: User = None, use_patterns: bool = False) -> list[User]:
    """
    filter_attributes - A User object containing attributes to filter users in the database. If an attribute is None,
        then it should not be considered for the search. e.g. if filter_attributes.name = "John" then all users returned
        should have their name == "John". If filter_attributes.address = None, then we do not care what the address is when
        filtering. Additionally, many attributes may be used as a filter simultaneously. filter_attributes will never be
        None, but any attribute not being used as a filter will be None. It is also possible all the attributes in
        filter_attributes to be None, if that is the case then all rows should be returned.
    use_patterns - If True, then the string attributes in filter_attributes may contain string patterns rather than typical
        string literals, so the search should handle this accordingly. e.g. if filter_attributes.name = "John%" and
        use_patterns = True, then all Users returned should have their name start with "John". If use_patterns = False, then
        all users returned should have their name == "John%".

    returns a list of User objects with users who meet the qualifications of the filters. If no users meet the requirements,
     then an empty list is returned.
    """

    my_query = "SELECT account_id, name, address, phone_number, email FROM User"
    my_values = []

    if filter_attributes.account_id is not None:
        if len(my_values) == 0:
            my_query += " WHERE account_id"
        else:
            my_query += " AND account_id"
        if use_patterns:
            my_query += " LIKE %s"
        else:
            my_query += " = %s"
        my_values.append(filter_attributes.account_id)

    if filter_attributes.name is not None:
        if len(my_values) == 0:
            my_query += " WHERE name"
        else:
            my_query += " AND name"
        if use_patterns:
            my_query += " LIKE %s"
        else:
            my_query += " = %s"
        my_values.append(filter_attributes.name)

    if filter_attributes.address is not None:
        if len(my_values) == 0:
            my_query += " WHERE address"
        else:
            my_query += " AND address"
        if use_patterns:
            my_query += " LIKE %s"
        else:
            my_query += " = %s"
        my_values.append(filter_attributes.address)

    if filter_attributes.phone_number is not None:
        if len(my_values) == 0:
            my_query += " WHERE phone_number"
        else:
            my_query += " AND phone_number"
        if use_patterns:
            my_query += " LIKE %s"
        else:
            my_query += " = %s"
        my_values.append(filter_attributes.phone_number)

    if filter_attributes.email is not None:
        if len(my_values) == 0:
            my_query += " WHERE email"
        else:
            my_query += " AND email"
        if use_patterns:
            my_query += " LIKE %s"
        else:
            my_query += " = %s"
        my_values.append(filter_attributes.email)

    cur.execute(my_query, my_values)

    search_results = []
    for (account_id, name, address, phone_number, email) in cur:
        search_results.append(
            User(account_id, name, address, phone_number, email))
    return search_results


def get_filtered_loans(filter_attributes: Loan = None,
                       min_checkout_date: str = None,
                       max_checkout_date: str = None,
                       min_due_date: str = None,
                       max_due_date: str = None, ) -> list[Loan]:
    """
    filter_attributes - A Loan object containing attributes to filter loan in the database. If an attribute is None,
        then it should not be considered for the search. e.g. if filter_attributes.isbn = "123456789" then all loans returned
        should have their isbn == "123456789". If filter_attributes.isbn = None, then we do not care what the isbn is, when
        filtering. Additionally, many attributes may be used as a filter simultaneously. filter_attributes will never be
        None, but any attribute not being used as a filter will be None. It is also possible all the attributes in
        filter_attributes to be None, if that is the case then all rows should be returned.
    min_checkout_date - The minimum checkout date (formatted in YYYY-mm-dd) to filter loans by, inclusively. e.g. if
        min_checkout_date = "2025-01-02", then all loans should be checked out after "2025-01-01", not including
        "2025-01-01". If min_checkout_date is not used, it will be None
    max_checkout_date - The maximum checkout date (formatted in YYYY-mm-dd) to filter loans by, inclusively. e.g. if
        max_checkout_date = "2025-01-02", then all loans should be checked out before "2025-01-03", not including
        "2025-01-03". If max_checkout_date is not used, it will be None
    min_due_date - like min_checkout_date but with the due date instead. If min_due_date is not used, it will be None.
    max_due_date - like max_checkout_date but with the due date instead. If max_due_date is not used, it will be None.

    returns a list of Loan objects with loans that meet the qualifications of the filters. If no loans meet the
    requirements, then an empty list is returned.
    """
    my_query = "SELECT isbn, account_id, checkout_date, due_date FROM Loan"
    my_values = []

    if filter_attributes.isbn is not None:
        if len(my_values) == 0:
            my_query += " WHERE isbn = %s"
        else:
            my_query += " AND isbn = %s"
        my_values.append(filter_attributes.isbn)

    if filter_attributes.account_id is not None:
        if len(my_values) == 0:
            my_query += " WHERE account_id = %s"
        else:
            my_query += " AND account_id = %s"
        my_values.append(filter_attributes.account_id)

    if min_checkout_date is not None:
        if len(my_values) == 0:
            my_query += " WHERE checkout_date >= %s"
        else:
            my_query += " AND checkout_date >= %s"
        my_values.append(min_checkout_date)

    if max_checkout_date is not None:
        if len(my_values) == 0:
            my_query += " WHERE checkout_date <= %s"
        else:
            my_query += " AND checkout_date <= %s"
        my_values.append(max_checkout_date)

    if min_due_date is not None:
        if len(my_values) == 0:
            my_query += " WHERE due_date >= %s"
        else:
            my_query += " AND due_date >= %s"
        my_values.append(min_due_date)

    if max_due_date is not None:
        if len(my_values) == 0:
            my_query += " WHERE due_date <= %s"
        else:
            my_query += " AND due_date <= %s"
        my_values.append(max_due_date)

    cur.execute(my_query, my_values)

    search_results = []
    for (isbn, account_id, checkout_date, due_date) in cur:
        search_results.append(
            Loan(isbn, account_id, checkout_date.isoformat(), due_date.isoformat()))
    return search_results


def get_filtered_loan_histories(filter_attributes: LoanHistory = None,
                                min_checkout_date: str = None,
                                max_checkout_date: str = None,
                                min_due_date: str = None,
                                max_due_date: str = None,
                                min_return_date: str = None,
                                max_return_date: str = None) -> list[LoanHistory]:
    """
    filter_attributes - A LoanHistory object containing attributes to filter loan histories in the database. If an attribute is None,
        then it should not be considered for the search. e.g. if filter_attributes.isbn = "123456789" then all rows returned
        should have their isbn == "123456789". If filter_attributes.isbn = None, then we do not care what the isbn is when
        filtering. Additionally, many attributes may be used as a filter simultaneously. filter_attributes will never be
        None, but any attribute not being used as a filter will be None. It is also possible all the attributes in
        filter_attributes to be None, if that is the case then all rows should be returned.
    min_checkout_date - The minimum checkout date (formatted in YYYY-mm-dd) to filter loans by, inclusively. e.g. if
        min_checkout_date = "2025-01-02", then all loans should be checked out after "2025-01-01", not including
        "2025-01-01". If min_checkout_date is not used, it will be None
    max_checkout_date - The maximum checkout date (formatted in YYYY-mm-dd) to filter loans by, inclusively. e.g. if
        max_checkout_date = "2025-01-02", then all loans should be checked out before "2025-01-03", not including
        "2025-01-03". If max_checkout_date is not used, it will be None
    min_due_date - like min_checkout_date but with the due date instead. If min_due_date is not used, it will be None.
    max_due_date - like max_checkout_date but with the due date instead. If max_due_date is not used, it will be None.
    min_return_date - like min_checkout_date but with the return date instead. If min_return_date is not used, it will be
        None.
    max_return_date - like max_checkout_date but with the return date instead. If max_return_date is not used, it will be
        None.

    returns a list of LoanHistory objects with return entries that meet the qualifications of the filters. If no entries
    meet the requirements, then an empty list is returned
    """
    my_query = "SELECT isbn, account_id, checkout_date, due_date, return_date FROM LoanHistory"
    my_values = []

    if filter_attributes.isbn is not None:
        if len(my_values) == 0:
            my_query += " WHERE isbn = %s"
        else:
            my_query += " AND isbn = %s"
        my_values.append(filter_attributes.isbn)

    if filter_attributes.account_id is not None:
        if len(my_values) == 0:
            my_query += " WHERE account_id = %s"
        else:
            my_query += " AND account_id = %s"
        my_values.append(filter_attributes.account_id)

    if min_checkout_date is not None:
        if len(my_values) == 0:
            my_query += " WHERE checkout_date >= %s"
        else:
            my_query += " AND checkout_date >= %s"
        my_values.append(min_checkout_date)

    if max_checkout_date is not None:
        if len(my_values) == 0:
            my_query += " WHERE checkout_date <= %s"
        else:
            my_query += " AND checkout_date <= %s"
        my_values.append(max_checkout_date)

    if min_due_date is not None:
        if len(my_values) == 0:
            my_query += " WHERE due_date >= %s"
        else:
            my_query += " AND due_date >= %s"
        my_values.append(min_due_date)

    if max_due_date is not None:
        if len(my_values) == 0:
            my_query += " WHERE due_date <= %s"
        else:
            my_query += " AND due_date <= %s"
        my_values.append(max_due_date)

    if min_return_date is not None:
        if len(my_values) == 0:
            my_query += " WHERE return_date >= %s"
        else:
            my_query += " AND return_date >= %s"
        my_values.append(min_return_date)

    if max_return_date is not None:
        if len(my_values) == 0:
            my_query += " WHERE return_date <= %s"
        else:
            my_query += " AND return_date <= %s"
        my_values.append(max_return_date)

    cur.execute(my_query, my_values)

    search_results = []
    for (isbn, account_id, checkout_date, due_date, return_date) in cur:
        search_results.append(LoanHistory(isbn, account_id, checkout_date.isoformat(
        ), due_date.isoformat(), return_date.isoformat()))
    return search_results


def get_filtered_waitlist(filter_attributes: Waitlist = None,
                          min_place_in_line: int = -1,
                          max_place_in_line: int = -1) -> list[Waitlist]:
    """
    filter_attributes - A Waitlist object containing attributes to filter waitlists in the database. If an attribute is None,
        then it should not be considered for the search. e.g. if filter_attributes.isbn = "123456789" then all rows returned
        should have their isbn == "123456789". If filter_attributes.isbn = None, then we do not care what the isbn is when
        filtering. Additionally, many attributes may be used as a filter simultaneously. filter_attributes will never be
        None, but any attribute not being used as a filter will be None. It is also possible all the attributes in
        filter_attributes to be None, if that is the case then all rows should be returned.
    min_place_in_line - The minimum place in line for a waitlist to be. e.g. if min_place_in_line = 3 then only entries
        where the place_in_line is greater than or equal to 3 should be included. If min_place_in_line is not used, it will
        be -1.
    max_place_in_line - The minimum place in line for a waitlist to be. e.g. if max_place_in_line = 3 then only entries
        where the place_in_line is less than or equal to 3 should be included. If max_place_in_line is not used, it will be
         -1.

    returns a list of Waitlist objects with waitlist entries that meet the qualifications of the filters. If no entries meet
     the requirements, then an empty list is returned.
    """
    my_query = "SELECT isbn, account_id, place_in_line FROM Waitlist"
    my_values = []

    if filter_attributes.isbn is not None:
        if len(my_values) == 0:
            my_query += " WHERE isbn = %s"
        else:
            my_query += " AND isbn = %s"
        my_values.append(filter_attributes.isbn)

    if filter_attributes.account_id is not None:
        if len(my_values) == 0:
            my_query += " WHERE account_id = %s"
        else:
            my_query += " AND account_id = %s"
        my_values.append(filter_attributes.account_id)

    if min_place_in_line != -1:
        if len(my_values) == 0:
            my_query += " WHERE place_in_line >= %s"
        else:
            my_query += " AND place_in_line >= %s"
        my_values.append(min_place_in_line)

    if max_place_in_line != -1:
        if len(my_values) == 0:
            my_query += " WHERE place_in_line <= %s"
        else:
            my_query += " AND place_in_line <= %s"
        my_values.append(max_place_in_line)

    cur.execute(my_query, my_values)

    search_results = []
    for (isbn, account_id, place_in_line) in cur:
        search_results.append(Waitlist(isbn, account_id, place_in_line))
    return search_results


def number_in_stock(isbn: str = None) -> int:
    """
    isbn - A string containing the ISBN for a book. ISBN will never be None.

    returns the quantity of books available with their ISBN equal to the isbn parameter. The quantity available should be
        calculated as how many copies the branch owns minus how many copies are checked out to users. If the library does
        not own the book, then -1 should be returned.
    """
    cur.execute("SELECT num_owned FROM Book WHERE isbn = %s", [isbn])
    num_owned = cur.fetchone()
    if num_owned is None:
        return -1

    cur.execute("SELECT num_owned - (SELECT COUNT(*) FROM Loan WHERE isbn = %s) "
                "FROM Book WHERE isbn = %s",
                [isbn, isbn])

    num_in_stock = cur.fetchone()
    return num_in_stock[0]


def place_in_line(isbn: str = None, account_id: str = None) -> int:
    """
    isbn - A string containing the ISBN for a book. ISBN will never be None.
    account_id - A string containing the account id for a user. account_id will never be None.

    returns what place in line the user with the corresponding account_id is in for the book with the corresponding ISBN. If
        the user is not on the waitlist for that book, then -1 should be returned.
    """
    cur.execute("SELECT place_in_line FROM Waitlist WHERE isbn = %s AND account_id = %s", [
                isbn, account_id])
    position = cur.fetchone()

    if position is not None:
        return position[0]
    else:
        return -1


def line_length(isbn: str = None) -> int:
    """
    isbn - A string containing the ISBN for a book. ISBN will never be None.

    returns how many people are on the waitlist for the book with the corresponding ISBN. e.g. if there are 5 people on the
        waitlist for a book, 5 should be returned. If there is no waitlist for the book, then 0 should be returned.
    """
    cur.execute("SELECT COUNT(*) FROM Waitlist WHERE isbn = %s", [isbn])
    line_len = cur.fetchone()
    return line_len[0]


def save_changes():
    """
    Commits all changes made to the db.
    """
    conn.commit()


def close_connection():
    """
    Closes the cursor and connection.
    """
    cur.close()
    conn.close()
