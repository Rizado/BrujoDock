# utils.py
def pluralize(n, forms):
    """
    Форматирует число по русским правилам.
    forms = ('окно', 'окна', 'окон')
    """
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return forms[0]
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return forms[1]
    else:
        return forms[2]

def format_window_count(count):
    if count == 0:
        return "нет окон"
    elif count == 1:
        return "1 окно"
    else:
        return f"{count} {pluralize(count, ('окно', 'окна', 'окон'))}"