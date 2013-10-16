import re
from line_naive_classify import classify

__author__ = 'Roland'


def process_receipt(lines):
    labels = classify(lines)
    props = {'shop': '', 'address': '', 'cui': '', 'items': [], 'data': '', 'total': ''}
    items = []
    for line, label in zip(lines, labels):
        if label in ['shop', 'cui', 'data', 'total']:
            props[label] = line
        elif label == 'address':
            props[label] += line
        elif label in ['price', 'name']:
            items.append((line, label))
    it = iter(items)
    groups = []
    for pr, na in zip(it, it):
        if pr[1] == 'name' and na[1] == 'price':
            pr, na = na, pr
        regex = re.search(r'([0-9,.]+?) *?x *?([0-9,.]+)', pr[0])
        if regex:
            grs = regex.groups()
            if len(grs) == 2:
                quantity = grs[0].replace(',','.')
                price = grs[1].replace(',','.')
                tprice = round(float(quantity)*float(price), 2)
            elif len(grs) == 1:
                tprice = round(float(grs[0].replace(',','.')), 2)
            tprst = str(tprice).replace('.', ',')
            if tprst in na[0]:
                groups.append((na[0][:na[0].index(tprst)], tprice))
            else:
                groups.append((na[0], tprice))
        else:
            print(pr, na)

    props['items'] = groups
    return props

