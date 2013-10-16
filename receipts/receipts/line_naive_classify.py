import re
import string

__author__ = 'Roland'

days = ['luni', 'marti', 'miercuri','joi', 'vineri', 'sambata', 'duminica']
def classify(receipt):
    labels = []
    for i, line in enumerate(receipt):
            line = str(line)
            a_chars = count(line, string.ascii_letters)
            num_chars = count(line, string.digits)
            punct_chars = count(line, string.punctuation)

            if 'bon fiscal' in line.lower():
                labels.append('unknown')
            #if 'subtotal' in line.lower():
            #    labels.append('unknown')

            elif (re.search('S\.?C\.?(.+?)(S.?R.?L.?)|(S[:.]?A[:.]?)', line, re.IGNORECASE) or\
                any(x in line.lower() for x in ['kaufland'])) and i < 5 and 'shop' not in labels:
                labels.append('shop')
            elif (re.search('(C.?U.?I.?)|(C.?F.?)|(C.?I.?F.?)|(COD FISCAL).+? (\d){4,}', line) or\
                  re.search('\d{8}', line)) and i < 6:
                labels.append('cui')
            elif (re.search('(STR)|(CALEA)|(B-DUL).(.+?)', line, re.IGNORECASE) and i < 7) or\
                (re.search('(NR).(\d+)', line, re.IGNORECASE) and i < 3):
                labels.append('address')


            elif 'TVA' in line:
                labels.append('tva')
            elif 'TOTAL' in line and 'SUBTOTAL' not in line:
                labels.append('total')
            elif re.search('DATA?.+?\d{2,4}[.\\-]\d{2,4}[.\\-]\d{2,4}', line, re.IGNORECASE) or\
                 re.search('\d{2}[./\\-]\d{2}[./\\-]\d{2,4}', line, re.IGNORECASE):
                labels.append('data')
            elif a_chars > 0 and num_chars/a_chars > 1 and 2 < i < len(receipt) - 7 and \
                 all(x not in line.lower() for x in ['tel', 'fax']) and 'total' not in labels:
                labels.append('price')
            elif 3 < i < len(receipt) - 8 and a_chars+punct_chars > 5 and 'total' not in labels and ((\
                 all(not re.search('(\W|^)'+x, line.lower()) for x in ['tel', 'fax', 'subtotal', 'numerar', 'brut', 'net'] +
                 days)\
                and not re.search('\d{5}', line)) or labels[-1] == 'price'):

                labels.append('name')
            else:
                labels.append('unknown')
    return labels

count = lambda l1, l2: len(list(filter(lambda c: c in l2, l1)))


