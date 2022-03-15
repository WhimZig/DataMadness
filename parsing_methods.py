# I'm adding everything to a separate file, so that it's easier to debug. Bugs, woo!!
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from typing import List, Tuple


def getGeneralInfo(wrestlerID: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
        If it returns 0, then there was success, if it returns 1 then there was a failure

        Arguments:
            wrestlerID: wrestlingdata index for this wrestler, minimum is 1, maximum is 30195

        Returns:
            success, GeneralInfo, Facts
    """
    A = requests.get('https://www.wrestlingdata.com/index.php?befehl=bios&wrestler=%d' % wrestlerID)
    #print(wrestlerID)
    wrestler = BeautifulSoup(A.text, 'html.parser')
    if wrestler.find(title="General Information") is None:
        return 1, None, None

    children = list(wrestler.find(title="General Information").parent.parent.children)
    GeneralInfo = {c.attrs['title']: [list(c.children)[3].text.strip('\n')] for c in
                   wrestler.find(title="General Information").parent.parent.children if
                   'attrs' in c.__dict__ and 'title' in c.attrs}
    wrestler_name = list(wrestler.find(style="width:100%;", cellpadding="4", cellspacing="2").children)[1].find(
        style="font-size: 14px;").text.strip('\n')
    res = pd.DataFrame(GeneralInfo, index=[wrestlerID])
    res['wrestler_name'] = [wrestler_name]
    tables2 = wrestler.find(title='Facts')
    B = pd.read_html(str(list(list(tables2.parent.parent.parent.parent.parent.children)[3].children)[1].table))
    return 0, res.transpose(), B[0]


def get50wrestlers(top_index: int) -> List[int]:
    """
        Arguments:
            top_index: the index of the 'Rankings' page, minimum is 1, maximum is 105

        Returns:
            A list of wrestlerID's corresponding to the list of wrestlers on the Rankings page with the given page number "top_index"
    """
    B = requests.get('https://www.wrestlingdata.com/index.php?befehl=bios&letter=2&seite=%d' % top_index)
    wrestlerlist = BeautifulSoup(B.text, 'html.parser')

    result_list = []

    # I modified the parsing loop because it had issues in cases where the wrestler didn't have a hyperlink
    # This should work?
    for i in range(len(list(wrestlerlist.find(title="Liste der Wrestler").children)[3:])):
        x = list(wrestlerlist.find(title="Liste der Wrestler").children)[3:][i]
        if len(list(list(x.children)[2].children)) > 1:
            resulting_int = int(list(list(x.children)[2].children)[1].attrs['href'][32:])
        result_list.append(resulting_int)

    return result_list


def getSample(sample_indices: List[int]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
        Arguments:
            sample_indices: A list of wrestlerID's to be used as index for this sample

        Returns:
            generalInfo, allFacts
    """
    sample_GeneralInfo = [None for _ in range(len(sample_indices))]
    sample_Facts = [None for _ in range(len(sample_indices))]
    for i in range(len(sample_indices)):
        print(i)
        run_res, temp_gen_info, temp_facts = getGeneralInfo(sample_indices[i])
        # There are codes for which there's no wrestler
        # This is the amazing way I deal with that!
        if run_res == 0:
            sample_GeneralInfo[i], sample_Facts[i] = temp_gen_info, temp_facts

        #sample_GeneralInfo[i], sample_Facts[i] = getGeneralInfo(sample_indices[i])
    # Because there can now be empty wrestlers, I need to clean things up.
    # Shitty, but it works
    sample_GeneralInfo = [x for x in sample_GeneralInfo if x is not None]
    sample_Facts = [x for x in sample_Facts if x is not None]

    generalInfo = pd.concat([x.transpose() for x in sample_GeneralInfo])

    res = pd.Index([])
    for x in sample_Facts:
        res = pd.concat([pd.Series(res), pd.Series(x[0].value_counts().index)])
    fact_columns = res.value_counts().index
    likely_columns = [x for x in fact_columns if len(x) < 40]
    ts = [None for _ in generalInfo.index]
    for i in range(len(generalInfo.index)):
        t = sample_Facts[i].groupby(0).agg(**{"%d" % generalInfo.index[i]: (1, set)})
        ts[i] = t.loc[t.index.intersection(likely_columns)].transpose()
    allFacts = pd.concat(ts)
    return generalInfo, allFacts
