'''Things we want to do:

    1. Get basic count data by category
    2. Do citation anlysis (forward and back) by time and category
    3. Do citation analysis over time for a particular item
        * or just: what is distribution of lag times for citations
        * take all patents in 1975 and run citation data through ...
    3. Do a PCA analysis using some data

Links/Flows = Citations. However have extra attributes derived from patents
    * year it occurred + difference in age
    * Direction 

Patents = Technologies:
    * location of patents in technology space, patent = some vector of characteristics e.g.
        * adjacency matrix vector
        * class, subcat, etc
    * value of patents
        * no. citations, no. claims etc

Ideas:

    * knowledge flows: cite from x -> y is flow from y -> x. Equate x and y
      with their technological areas and ...
      * multi-graph with weighted links
    * 

'''
import os
import simplejson as sj
import sqlalchemy.sql as sql

import convert_to_db as db
datadir = os.path.abspath('data')
outdir = os.path.abspath('out')

class Analyzer(object):
    subcat_list = os.path.join(datadir, 'subcat_summary.js')
    nclass_list = os.path.join(datadir, 'nclass_summary.js')

    def __init__(self):
        self.s = db.Session()
        self.subcats = None
        if not os.path.exists(self.subcat_list):
            self._get_subcat_stats() 
        self.subcats = sj.load(file(self.subcat_list))
        if not os.path.exists(self.nclass_list):
            self._get_nclass_stats() 
        self.nclasss = sj.load(file(self.nclass_list))

    def extract_citation_matrix(self, subcat, year):
        pass

    def _get_subcat_stats(self):
        # hand-crafted sql is probably faster
        q = sql.select([db.patent.c.subcat, sql.func.count('*')])
        q = q.group_by(db.patent.c.subcat)
        data = q.execute().fetchall()
        data = [ list(x) for x in data ]
        data.sort()
        sj.dump(data, file(self.subcat_list, 'w'), indent=4)

    def _get_nclass_stats(self):
        q = sql.select([db.patent.c.nclass, sql.func.count('*')])
        q = q.group_by(db.patent.c.nclass)
        data = q.execute().fetchall()
        data = [ list(x) for x in data ]
        data.sort()
        sj.dump(data, file(self.nclass_list, 'w'), indent=4)

    def all_cite_counts(self):
        cached = 'data/cite_counts_by_year.js'
        if not os.path.exists(cached):
            res = []
            for year in range(1975, 1995):
                res.append([year, self.cite_counts(year)])
            sj.dump(res, file(cached, 'w'))
        else:
            res = sj.load(file(cached))
        return res

    def cite_counts(self, year):
        # if not self.cite_counts
        t = db.patent.c
        results = {}
        def ddist(col):
            q = sql.select([col, sql.func.count('*')]) # ([col, sql.func.count('*'), t.gyear])
            q = q.where(t.gyear==year)
            q = q.group_by(col)
            q = q.order_by(col)
            cursor = q.execute()
            out = [ [x[0], x[1] ] for x in cursor ]
            return out
        results['cmade'] = ddist(t.cmade)
        results['creceive'] = ddist(t.creceive)
        return results

    def get_citation_matrix(self, patent_query):
        # patent_set = sql.select(d
        # sql.
        patent_set = patent_query.execute()
        for patent in patent_set:
            for cite in patent.citations:
                results.append([patent.id, cite.cited, patent.gyear])
            # in fact since both patent and pother must be in patent_set
            # can ignore this since we will already have it
            # (question is do we care about directionality ...
            # for pother in patent.cited_by:
            #    if pother in patent_set:
            #        results.append([patent, pother, pother.gyear])

    def get_citation_matrix_fast(self, subcat, years=None):
        # select citing_id, cited_id gyear
        # q = sql.select(
        pass

    def get_flows_by_subcat(self, start, end):
        '''
        Return an NxN matrix with N(i,j) = flow from area i to area j

        Add one unknown class to deal with cases where we don't know dest
        patent

        '''
        patents = db.Patent.filter_by(start <= db.Patent.gyear <= end)
        self.get_flows(self, patents)

    def get_flows(self, patents):
        for p in patents:
            for cite in p.citations:
                dest = cite.cited



class TestStuff:
    a = Analyzer()

    def test_1(self):
        year = 1975
        pat = db.Patent.query.filter_by(gyear=year).first()
        print pat
        assert pat.gyear == 1975
        assert pat.claims == 6
        assert pat.nclass == 2
        assert len(pat.citations) == 5, len(pat.citations)
        assert len(pat.citations_by) == 0, len(pat.citations_by)

    def test_subcat_stats(self):
        out = self.a.subcats
        print out
        assert len(out) == 36, len(out)
        assert out[0][0] == 11

    def test_nclass_stats(self):
        out = self.a.nclasss
        print out
        assert len(out) == 418, len(out)
        assert out[0][0] == 1
        assert out[0][1] == 96

    def test_all_cite_counts(self):
        out = self.a.all_cite_counts()
        assert len(out) == 20, len(out)
        assert 'cmade' in out[0][1]
        y1975 = out[0][1]['cmade']
        assert y1975[0][0] == 0

import pylab
def main():
    a = Analyzer()
    def doplot(stats, fname):
        stats = zip(*stats)
        pylab.bar(stats[0], stats[1])
        # TODO: labels bars -- see data/subcategories.csv or data/list_of_classes.txt
        print fname
        fn = os.path.join(outdir, '%s.png' % fname)
        pylab.savefig(fn)
        pylab.clf()
    doplot(a.subcats, 'subcat_stats')
    doplot(a.nclasss, 'nclass_stats')

def plot_ddist(year):
    a = Analyzer()
    c = a.all_cite_counts()
    c = dict(c)
    counts = c[year]['creceive']
    counts = zip(*counts)
    pylab.title('Distbn of Citations Received (%s)' % year)
    pylab.xlabel('No. Citations Received')
    pylab.ylabel('No. of Patents')
    pylab.bar(counts[0], counts[1], log=True)
    fn = os.path.join(outdir, 'creceive_ddist_%s.png' % year)
    pylab.savefig(fn)
    pylab.clf()

if __name__ == '__main__':
    # main()
    plot_ddist(1975)
    plot_ddist(1985)
    plot_ddist(1994)


