import datetime

# List of US Presidents with birth dates and last day of term
# (Name, Birthdate, Last Day of Term)
presidents = [
    ("George Washington", "1732-02-22", "1797-03-04"),
    ("John Adams", "1735-10-30", "1801-03-04"),
    ("Thomas Jefferson", "1743-04-13", "1809-03-04"),
    ("James Madison", "1751-03-16", "1817-03-04"),
    ("James Monroe", "1758-04-28", "1825-03-04"),
    ("John Quincy Adams", "1767-07-11", "1829-03-04"),
    ("Andrew Jackson", "1767-03-15", "1837-03-04"),
    ("Martin Van Buren", "1782-12-05", "1841-03-04"),
    ("William Henry Harrison", "1773-02-09", "1841-04-04"),
    ("John Tyler", "1790-03-29", "1845-03-04"),
    ("James K. Polk", "1795-11-02", "1849-03-04"),
    ("Zachary Taylor", "1784-11-24", "1850-07-09"),
    ("Millard Fillmore", "1800-01-07", "1853-03-04"),
    ("Franklin Pierce", "1804-11-23", "1857-03-04"),
    ("James Buchanan", "1791-04-23", "1861-03-04"),
    ("Abraham Lincoln", "1809-02-12", "1865-04-15"),
    ("Andrew Johnson", "1808-12-29", "1869-03-04"),
    ("Ulysses S. Grant", "1822-04-27", "1877-03-04"),
    ("Rutherford B. Hayes", "1822-10-04", "1881-03-04"),
    ("James A. Garfield", "1831-11-19", "1881-09-19"),
    ("Chester A. Arthur", "1829-10-05", "1885-03-04"),
    ("Grover Cleveland", "1837-03-18", "1897-03-04"),
    ("Benjamin Harrison", "1833-08-20", "1893-03-04"),
    ("William McKinley", "1843-01-29", "1901-09-14"),
    ("Theodore Roosevelt", "1858-10-27", "1909-03-04"),
    ("William Howard Taft", "1857-09-15", "1913-03-04"),
    ("Woodrow Wilson", "1856-12-28", "1921-03-04"),
    ("Warren G. Harding", "1865-11-02", "1923-08-02"),
    ("Calvin Coolidge", "1872-07-04", "1929-03-04"),
    ("Herbert Hoover", "1874-08-10", "1933-03-04"),
    ("Franklin D. Roosevelt", "1882-01-30", "1945-04-12"),
    ("Harry S. Truman", "1884-05-08", "1953-01-20"),
    ("Dwight D. Eisenhower", "1890-10-14", "1961-01-20"),
    ("John F. Kennedy", "1917-05-29", "1963-11-22"),
    ("Lyndon B. Johnson", "1908-08-27", "1969-01-20"),
    ("Richard Nixon", "1913-01-09", "1974-08-09"),
    ("Gerald Ford", "1913-07-14", "1977-01-20"),
    ("Jimmy Carter", "1924-10-01", "1981-01-20"),
    ("Ronald Reagan", "1911-02-06", "1989-01-20"),
    ("George H. W. Bush", "1924-06-12", "1993-01-20"),
    ("Bill Clinton", "1946-08-19", "2001-01-20"),
    ("George W. Bush", "1946-07-06", "2009-01-20"),
    ("Barack Obama", "1961-08-04", "2017-01-20"),
    ("Donald Trump", "1946-06-14", "2021-01-20"),
    ("Joe Biden", "1942-11-20", "2025-01-20")
]

def calculate_age(birthdate, end_date):
    b = datetime.datetime.strptime(birthdate, "%Y-%m-%d")
    e = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    age = e.year - b.year - ((e.month, e.day) < (b.month, b.day))
    return age

presidents_with_age = []
for name, birth, end in presidents:
    age = calculate_age(birth, end)
    presidents_with_age.append((name, age))

presidents_with_age.sort(key=lambda x: x[1], reverse=True)

for name, age in presidents_with_age:
    print(f"{name}: {age}")
