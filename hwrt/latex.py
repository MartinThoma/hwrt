#!/usr/bin/env python

"""Normalize mathematical formulae written with LaTeX."""

import string


def chunk_math(text):
    """
    Parameters
    ----------
    text : string
        A mathematical context

    Returns
    -------
    list :
        A list of single LaTeX entities

    Examples
    --------
    >>> chunk_math('\sum_i^n i^2')
    ['\\\\sum', '_', 'i', '^', 'n', ' ', 'i', '^', '2']

    >>> chunk_math('\sum_{i}^n i^2')
    ['\\\\sum', '_', '{', 'i', '}', '^', 'n', ' ', 'i', '^', '2']

    >>> chunk_math((r'\\Delta F_0 &= \\sqrt{\\sum_{i=1}^n\\left('
    ...             r'\\frac{\delta F_0}{\delta x_i}'
    ...             r'\Delta x_i\\right)^2}\\[0.2cm]'
    ...             r'\Delta F_0 &= \sqrt{6.044 \cdot  10^{-6}\\text{m}^2}'))
    ['\\\\Delta', ' ', 'F', '_', '0', ' ', '&', '=', ' ', '\\\\sqrt', '{', '\\\\sum', '_', '{', 'i', '=', '1', '}', '^', 'n', '\\\\left', '(', '\\\\frac', '{', '\\\\delta', ' ', 'F', '_', '0', '}', '{', '\\\\delta', ' ', 'x', '_', 'i', '}', '\\\\Delta', ' ', 'x', '_', 'i', '\\\\right', ')', '^', '2', '}', '\\\\', '[', '0', '.', '2', 'c', 'm', ']', '\\\\Delta', ' ', 'F', '_', '0', ' ', '&', '=', ' ', '\\\\sqrt', '{', '6', '.', '0', '4', '4', ' ', '\\\\cdot', ' ', '1', '0', '^', '{', '-', '6', '}', '\\\\text', '{', 'm', '}', '^', '2', '}']

    >>> chunk_math(r'\\left\\{a\\right\\}')
    ['\\\\left', '\\\\{', 'a', '\\\\right', '\\\\}']

    >>> chunk_math(r'\\sqrt{b^2-4ac}')
    ['\\\\sqrt', '{', 'b', '^', '2', '-', '4', 'a', 'c', '}']

    >>> chunk_math('y^{2}')
    ['y', '^', '{', '2', '}']

    >>> chunk_math(r'2+3\\\\6 5 4')
    ['2', '+', '3', '\\\\\\\\', '6', ' ', '5', ' ', '4']
    """

    # Fail when '{' and '}' don't match - be aware of escaped symbols!
    opened_braces = 0
    last_char = ''
    for char in text:
        if char == '{' and last_char != '\\':
            opened_braces += 1
        if char == '}' and last_char != '\\':
            opened_braces -= 1
            if opened_braces < 0:
                raise ValueError("Braces don't match: %s" % text)
        last_char = char
    if opened_braces != 0:
        raise ValueError("%i braces are still open" % opened_braces)

    # Parse
    single_symbol = ['_', '^', '&', '{', '}']
    breaking_chars = ['\\', ' '] + single_symbol

    chunks = []
    current_chunk = ''

    for char in text:
        if current_chunk == '':
            current_chunk = char
            continue
        if char == '\\':
            if current_chunk == '\\':
                current_chunk += char
                chunks.append(current_chunk)
                current_chunk = ''
            else:
                chunks.append(current_chunk)
                current_chunk = char
        elif current_chunk == '\\' and char in breaking_chars:  # escaped
            current_chunk += char
            chunks.append(current_chunk)
            current_chunk = ''
        elif char in breaking_chars:
            chunks.append(current_chunk)
            current_chunk = char
        elif char in string.letters+string.digits and current_chunk[0] == '\\':
            current_chunk += char
        else:
            chunks.append(current_chunk)
            current_chunk = char

    # Add the last chunk
    if current_chunk != '':
        chunks.append(current_chunk)
    filtered = []
    for chunk in chunks:
        if len(filtered) > 0 and filtered[-1] == ' ' and chunk == ' ':
            continue
        filtered.append(chunk)
    return filtered


def chunks_to_string(chunks):
    """
    Parameters
    ----------
    chunks : list of strings
        A list of single entities in order

    Returns
    -------
    string :
        A LaTeX-parsable string

    Examples
    --------
    >>> chunks_to_string(['\\\\sum', '_', 'i', '^', 'n', 'i', '^', '2'])
    '\\\\sum_{i}^{n}i^{2}'
    >>> chunks_to_string(['\\\\sum', '_', '{', 'i', '}', '^', 'n', 'i', '^',
    ...                   '2'])
    '\\\\sum_{i}^{n}i^{2}'
    """
    string = ''
    began_context = False
    context_depth = 0
    context_triggers = ['_', '^']
    for chunk in chunks:
        if began_context and chunk != '{':
            string += '{' + chunk + '}'
            began_context = False
        elif began_context and chunk == '{':
            began_context = False
            string += chunk
        else:
            if chunk in context_triggers:
                began_context = True
                context_depth += 1
            string += chunk
    return string


def normalize(latex):
    """Normalize a math-mode LaTeX string.

    Parameters
    ----------
    latex : string

    Returns
    -------
    string : normalized LaTeX code

    Examples
    --------
    >>> normalize('\sum_i n^i')
    '\\\\sum_{i} n^{i}'
    >>> normalize('Carsten Wilhelm')
    'Carsten Wilhelm'
    >>> normalize(r'\\Delta F')
    '\\\\Delta F'
    >>> normalize(r'\\sqrt{b^2-4ac}')
    '\\\\sqrt{b^{2}-4ac}'
    >>> normalize(r'y^{2}')
    'y^{2}'
    """
    return chunks_to_string(chunk_math(latex))


if __name__ == '__main__':
    import doctest
    doctest.testmod()
