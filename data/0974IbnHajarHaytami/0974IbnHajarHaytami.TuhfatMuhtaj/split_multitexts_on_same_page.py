"""Some texts in the corpus contain multiple texts
(often a main text and one or more commentaries)
displayed on the same page.

This script splits these texts into separate files.

In order to work, you have to provide it with a dictionary that contains
the following information for each text:

1. contains the filename that should be given to the text,
2. the regex to be used in a re.findall operation to extract this text
from a page


"""

import re
import os
from shutil import copyfile
from openiti.helper.ara import ar_cnt_file

def clean(text):
    # remove html tags:
    text = re.sub('''<[/a-zA-Z=\-_"' ]+>''', "", text)
    # remove NO_PAGE_NUMBER immediately following a page number:
    text = re.sub("(PageV[^P]+P\w+)[\r\n]*NO_PAGE_NUMBER", r"\1", text)
    # remove paragraph marks without a paragraph:
    text = re.sub(r"[\r\n]+#\s+[\r\n]+", "\n", text)
    text = re.sub("# Page", "Page", text)
    # Remove empty sharh pages (contain only "# . . . . .") :
    text = re.sub("### \|.+[\r\n]+[# .]+[\r\n]+Page.+", "", text)
    # tag subheadings:
    text = re.sub(r"# ([([](?:باب|فرع|فصل)[^\)\]]*[\)\]])\s*#?", r"### | \1\n# ", text)
    # remove the Hashiya tags:
    text = re.sub(r"### \| \[حاشية.+", "", text)

    text = text.strip()
    return text
    

def split_multitext(fp, outfolder, texts_d, clean_text=None):
    """Split a text that contains a matn and one or more commentaries \
    displayed on the same page.

    Args:
        fp (str): path to the text file
        outfolder (str): path to the folder where the files will be stored
        texts_d (dict): dictionary containing information on all
            texts that are displayed on a page:
            key: regex (str): regex that matches the content of this
                text's content on any given page
            val: dict: key-value pairs
                "fn": prospective file name for this text (str)
                "text": list containing the text of this work (list)
        clean_text (func): function to be used to clean the texts
            after they were split off. Default: None
    """
    with open(fp, mode="r", encoding="utf-8") as file:
        text = file.read()
    header, text = re.split("#META#Header#End#", text)
    header += "#META#Header#End#\n\n"

    # remove milestones:
    text = re.sub(" *ms\d+ *", " ", text)   
 
    pages = re.split("([\r\n]*PageV[^P]+P[\w]+[\r\n]*)", text)
    for i, page in enumerate(pages):
        if not page.startswith("Page"):
            try:
                page_no = pages[i+1]
            except:
                page_no = "\nNO_PAGE_NUMBER\n"

            for k in texts_d:
                try:
                    t = re.findall(k, page, flags=re.DOTALL)[0]
                except:
                    t = ""
                texts_d[k]["text"].append(t+page_no)

    yml_fp = fp + ".yml"
    uri = re.split(r"[/\\]", fp)[-1]
    with open(yml_fp, mode="r", encoding="utf-8") as file:
        yml_str = file.read()

    for d in texts_d.values():
        outfp = os.path.join(outfolder, d["fn"])
        with open(outfp, mode="w", encoding="utf-8") as file:
            t = header + "".join(d["text"])
            file.write(t)
        with open(outfp+".yml", mode="w", encoding="utf-8") as file:
            file.write(re.sub(uri, d["fn"], yml_str))

    print("original Arabic character count:", ar_cnt_file(fp, incl_editor_sections=True))
    total = sum([ar_cnt_file(os.path.join(outfolder, d["fn"]), incl_editor_sections=True) \
                 for d in texts_d.values()])
    print("sum of the Arabic character count in export files:", total)
    print("NB: if Arabic character count does not agree, something went wrong!")

    if clean_text:
        for d in texts_d.values():
            fp = os.path.join(outfolder, d["fn"])
            with open(fp, mode="r", encoding="utf-8") as file:
                text = file.read()
            text = clean_text(text)
            with open(fp, mode="w", encoding="utf-8") as file:
                file.write(text)
    

if __name__ == "__main__":
    fp = "0974IbnHajarHaytami.TuhfatMuhtaj.Shamela0009059-ara1"
    texts_d = {
        r"\A.*?(?=### \| \[حاشية)": {
            "fn": "0974IbnHajarHaytami.TuhfatMuhtaj.Shamela0009059BK1-ara1",
            "text": [],
            },
        r"(### \| \[حاشية +الشرواني.+?)(?=### \| \[حاشية|\Z)": {
            "fn": "1118CabdHamidShirwani.HashiyaCalaTuhfatMuhtaj.Shamela0009059BK2-ara1",
            "text": []
            },
        r"(### \| \[حاشية +ابن +قاسم.+?)(?=### \| \[حاشية|\Z)": {
            "fn": "0992IbnQasimMisri.HashiyaCalaTuhfatMuhtaj.Shamela0009059BK3-ara1",
            "text": []
            },
        }
    split_multitext(fp, "split", texts_d, clean_text=clean)
