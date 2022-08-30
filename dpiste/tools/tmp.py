import pandas as pd
from mkhtmltable import build_table
from dpiste.utils import get_home

def get_table(fpath: str) -> pd.DataFrame:
    return pd.read_html(fpath)[0]


def find_attribute_with_different_path(df: pd.DataFrame):
    alltags = get_list_of_tags(df)
    dejavu, leaves = remove_leaves(find_dejavu(alltags))
    
    allpaths = []
    for k in dejavu.keys():
        allpaths.append(get_all_paths(df, k))
    
    allpaths = remove_false_positives(allpaths)

    for i in allpaths:
        with open('res.txt', 'a') as f:
            f.write(f'{len(i)}\n')
            for j in i:
                f.write(f'{j}\n')
            f.write('\n\n')
    with open('res.txt', 'a') as f:
        f.write(f'Total: {len(allpaths)}')


def find_dejavu(alltags):
    checked = []
    dejavu = {}
    for tags in alltags:
        if len(tags) > 1:
            if tags[-1] in checked:
                dejavu[tags[-1]] = '/'.join(tags[:-1])
            else:
                checked.append(tags[-1])
        else:
            if tags[0] in checked:
                dejavu[tags[0]] = 'Leaf'
            else:
                checked.append(tags[0])
    return dejavu


def get_list_of_tags(df: pd.DataFrame) -> list:
    alltags = []
    for i in df.index:
        tags = []
        colname = df['column'][i]
        words = colname.split('_')
        for w in words:
            if w.startswith('0x'):
                tags.append(w)
        alltags.append(tags) if tags else None
    return alltags


def remove_leaves(dejavu: dict) -> dict:
    keys_to_del = []
    for k, v in dejavu.items():
        if v == 'Leaf':
            keys_to_del.append(k)
    for k in keys_to_del:
        dejavu.pop(k)
    return dejavu, keys_to_del


def get_all_paths(df: pd.DataFrame, tag: str) -> list:
    allpaths = []
    for i in df.index:
        colname = df['column'][i]
        if tag in colname:
            allpaths.append(colname)
    return allpaths


def remove_false_positives(allpaths: list) -> list:
    index2rm = []
    for a in range(len(allpaths)):
        do_rm = True
        for i in range(1, len(allpaths[a])):
            if count_diff_btw_str(allpaths[a][i], allpaths[a][i-1]) != 1:
                do_rm = False
        if do_rm:
            index2rm.append(a)
    for i, index in enumerate(sorted(index2rm)):
        allpaths.pop(index - i)
    return allpaths


def count_diff_btw_str(s1, s2):
    return sum(1 for a, b in zip(s1, s2) if a != b) + abs(len(s1) - len(s2))

df = get_table(get_home('resources/rapport-all-dcm2.html'))
find_attribute_with_different_path(df)
