import sys
import xml.etree.ElementTree as ET
import urllib2
import csv
from os import path
import os
import re


def detag(text):
    regex = re.compile(r'<.*?>')
    regex_tag_containing_newline = re.compile(r'<.*?\n.*?>')

    text = regex.sub(' ', text)
    text = regex_tag_containing_newline.sub(' ', text)

    return text

def remove_bad_chars(text):
    regex = re.compile(r'&nbsp;')
    return regex.sub(' ', text)

SEC_SEARCH_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=%s&count=100&type=S-1&output=xml"
HERE = path.abspath(path.dirname(__file__))
S1_ROOT_DIR = path.dirname(HERE)
OUTPUT_PATH = path.join(S1_ROOT_DIR, "data2")
print(OUTPUT_PATH)

exist_file = os.listdir(OUTPUT_PATH)



with open(sys.argv[1]) as csvfile:
    reader = csv.DictReader(csvfile)
    failed_to_get_filings = 0
    failed_to_get_txt_file = 0
    got_txt_file = 0
    total_companies_tried = 0
    failed_ticker = []
    for row in reader:
        total_companies_tried += 1
        ticker = row['Symbol']
        filename = ticker + '.txt'
        if filename not in exist_file:
            print("looking up ticker: " + ticker)

            #getting a link to the S-1 by searching on the SEC website
            try:
                site = urllib2.urlopen(SEC_SEARCH_URL % ticker)
                data = site.read()
                root = ET.fromstring(data)
                results = root.findall('results')
                filings = results[0].findall('filing')
                link = filings[-1].find('filingHREF').text
            except:
                try:
                    SEC_SEARCH_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=%s&count=100&type=424&output=xml"
                    site = urllib2.urlopen(SEC_SEARCH_URL % ticker)
                    data = site.read()
                    root = ET.fromstring(data)
                    results = root.findall('results')
                    filings = results[0].findall('filing')
                    link = filings[-1].find('filingHREF').text
                except:
                    print("failed to get filings")
                    failed_to_get_filings += 1
                    failed_ticker.append(ticker)
                    continue

                #get the text of the s-1 directly instead of going to the index page
            link = link.split('-index')[0] + '.txt'
            print("trying url: " + link)
            

            try:
                s1_site = urllib2.urlopen(link)
                text = s1_site.read()
                whole_text = detag(text)
                whole_text = remove_bad_chars(whole_text)
                # regex = re.compile(r'RISK FACTORS[\S\s]*?SPECIAL NOTE REGARDING FORWARD[- ]LOOKING STATEMENTS')
                # match = regex.search(whole_text)

                # if match:
                #     tex = match.group()
                # else:
                #     whole_text = detag(str(soup))
                #     whole_text = remove_bad_chars(whole_text)
                #     li = whole_text.split('\n')
                #     p = li.index('                                  RISK FACTORS')
                #     q = li.index('                                DIVIDEND POLICY')
                #     li = li[p + 1: q]
                #     tex = ' '.join([i.strip() for i in li])
                with open(path.join(OUTPUT_PATH, filename), 'w') as f:
                    f.write(whole_text)
                got_txt_file += 1
                    # try:
                    #     print("preparing to write to: " + path.join(OUTPUT_PATH,filename))
                    # with open(path.join(OUTPUT_PATH, filename), 'w') as f:
                    #     f.write(s1_site.read())
                    #     print('AAA')
                    # got_txt_file += 1
                    # except:
                    #     print("failed to write")
                    #     failed_to_get_txt_file += 1
                    #os.system('wget -O ' + filename + ' ' + link)
            except:
                print("failed to get txt file")
                failed_to_get_txt_file += 1
                failed_ticker.append(ticker)

    print("Total companies tried: " + str(total_companies_tried))
    print("Failed to get filings list: " + str(failed_to_get_filings))
    print("Failed to get text file: " + str(failed_to_get_txt_file))
    print("Succeeded in getting text file: " + str(got_txt_file))
    success_fail_test = total_companies_tried == failed_to_get_filings + failed_to_get_txt_file + got_txt_file
    print("Total failures plus total successes adds up to total tries? " + str(success_fail_test))
    print("Failed ticker:", failed_ticker)
