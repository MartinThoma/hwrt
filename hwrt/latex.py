#!/usr/bin/env python

"""Normalize mathematical formulae written with LaTeX."""


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
    ['\\\\sum', '_', 'i', '^', 'n', 'i', '^', '2']

    >>> chunk_math('\sum_{i}^n i^2')
    ['\\\\sum', '_', '{', 'i', '}', '^', 'n', 'i', '^', '2']

    >>> chunk_math((r'\\Delta F_0 &= \\sqrt{\\sum_{i=1}^n\\left('
    ...             r'\\frac{\delta F_0}{\delta x_i}'
    ...             r'\Delta x_i\\right)^2}\\[0.2cm]'
    ...             r'\Delta F_0 &= \sqrt{6.044 \cdot  10^{-6}\\text{m}^2}'))
    ['\\\\Delta', 'F', '_', '0', '&', '=', '\\\\sqrt', '{', '\\\\sum', '_', '{', 'i=1', '}', '^', 'n', '\\\\left(', '\\\\frac', '{', '\\\\delta', 'F', '_', '0', '}', '{', '\\\\delta', 'x', '_', 'i', '}', '\\\\Delta', 'x', '_', 'i', '\\\\right)', '^', '2', '}', '\\\\[0.2cm]', '\\\\Delta', 'F', '_', '0', '&', '=', '\\\\sqrt', '{', '6.044', '\\\\cdot', '10', '^', '{', '-6', '}', '\\\\text', '{', 'm', '}', '^', '2', '}']

    >>> chunk_math(r'\\left\\{a\\right\\}')
    ['\\\\left', '\\\\{', 'a', '\\\\right', '\\\\}']
    """
    single_symbol = ['_', '^', '&', '{', '}']
    breaking_chars = ['\\', ' '] + single_symbol
    # print(breaking_chars)
    chunks = []
    current_chunk = ''
    for char in text:
        if char in breaking_chars:
            if current_chunk != '' and not (current_chunk == '\\'):
                chunks.append(current_chunk)
                current_chunk = ''
            current_chunk += char
            if current_chunk in single_symbol:
                chunks.append(current_chunk)
                current_chunk = ''
            if current_chunk == ' ':
                current_chunk = ''
            if current_chunk.startswith('\\') and len(current_chunk) > 1:
                chunks.append(current_chunk)
                current_chunk = ''
        else:
            current_chunk += char
            # print("%s (%s was not breaking)" % (current_chunk, char))
    if current_chunk != '':  # Add the last chunk
        chunks.append(current_chunk)
    return chunks


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
    '\\\\sum_{i}n^{i}'
    """
    return chunks_to_string(chunk_math(latex))


if __name__ == '__main__':
    import doctest
    doctest.testmod()
