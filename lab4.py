import bs4 as bs
import networkx as nx
import urllib.request as urllib2
import re
import matplotlib.pyplot as plt
import os
import pandas as pd
import threading, queue

q = queue.Queue()
maxThreads = 50
nextUrl = queue.Queue()
crawledUrls = []


def getLinksFromPage(url):
    urllist = []
    try:
        res = urllib2.urlopen(url)
        htmlpage = res.read()
    except:

        return urllist

    try:
        page = bs.BeautifulSoup(htmlpage, "html.parser")
    except:
        return urllist

    pattern = re.compile(r"https://*.*.*/*")
    refs = page.findAll("a", href=pattern)
    for a in refs:
        try:
            link = a['href']
            if str(link).find("www.gazeta.ru") != -1:
                urllist.append(link)
        except:
            pass

    return urllist


def findLinks(urlTuple, graph):
    # Crawls to a given depth using a tuple structure to tag urls with their depth
    global crawledUrls, nextUrl, max_depth
    url = urlTuple[0]
    depth = urlTuple[1]
    if (depth < 2):
        links = getLinksFromPage(url)
        for link in links:
            # These two lines create the graph
            graph.add_node(link)
            graph.add_edge(url, link)
            # If the link has not been crawled yet, add it in the queue with additional depth
            if link not in crawledUrls:
                nextUrl.put((link, depth + 1))
                crawledUrls.append(link)
    return


class crawlerThread(threading.Thread):
    def __init__(self, queue, graph):
        threading.Thread.__init__(self)
        self.to_be_crawled = queue
        self.graph = graph
        while self.to_be_crawled.empty() is False:
            findLinks(self.to_be_crawled.get(), self.graph)


def drawGraph(graph, graphFileName):
    nx.draw(graph, with_labels=False)
    nx.write_dot(graph, os.cwd() + graphFileName + '.dot')
    plt.savefig(os.cwd() + graphFileName + '.png')


def calculatePageRank(url):
    print(str(url))
    root_url = url

    nextUrl.put((root_url, 0))
    crawledUrls.append(root_url)
    g = nx.Graph()
    g.add_node(root_url)
    threads = []

    for i in range(maxThreads):  # changed
        t = crawlerThread(nextUrl, g)
        t.daemon = True
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    pagerank = nx.pagerank_numpy(g, alpha=0.5, personalization=None, weight='weight', dangling=None)
    pg = sorted(pagerank)
    k = 1
    for i in pg:
        if k <= 10:
            print(str(i) + " " + str(pagerank.get(i)))
            k += 1

    edgeNumber = g.number_of_edges()
    nodeNumber = g.number_of_nodes()
    nodesize = [g.degree(n) * 10 for n in g]
    pos = nx.spring_layout(g, iterations=20)

    nx.draw(g, with_labels=False)
    nx.draw_networkx_nodes(g, pos, node_size=nodesize, node_color='r')
    nx.draw_networkx_edges(g, pos)
    plt.figure(figsize=(5, 5))
    plt.show()

    return pd.Series([pagerank.get(url), edgeNumber, nodeNumber], index=['pagerank', 'edges', 'nodes'])


url = 'https://www.gazeta.ru/'
calculatePageRank(url)
