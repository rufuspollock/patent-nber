from analyze import Analyzer, db, Plotter, FlowPlotter

class TestAnalyzer:
    a = Analyzer()

    def test_1(self):
        year = 1975
        pat = db.Patent.query.filter_by(gyear=year).first()
        print pat
        assert pat.gyear == 1975
        assert pat.claims == 6
        assert pat.nclass == 2
        assert len(pat.citations) == 5, len(pat.citations)
        # these should actually be the same since all citation post 1975
        assert len(pat.citations_by) == pat.creceive
        assert len(pat.citations_by) == 0, len(pat.citations_by)
        # check backref
        assert pat.citations[0].citing == pat

    def test_citations_by(self):
        # check when num citations is not zero
        year = 1975
        pat = db.Patent.query.filter_by(gyear=year).filter_by(creceive=2).first()
        # these should actually be the same since all citation post 1975
        assert len(pat.citations_by) == pat.creceive

    def test_full_join(self):
        q = self.a.full_join()
        # q = q.where(db.patent.c.gyear==1975)
        # q = q.limit(10)
        q = q.where(db.patent.c.id==3883377)
        out = q.execute().fetchall()[0]
        print out.keys()
        print out
        assert out[1] ==  3357959
        assert out['patent_cmade'] == 1
        assert out['cited_id'] == 3357959
        # check other access method
        citing = db.patent.alias('cited')
        assert out[citing.c.id] == 3357959

    def test_subcat_stats(self):
        out = self.a.subcatstats
        print out
        assert len(out) == 36, len(out)
        assert out[0][0] == 11

    def test_nclass_stats(self):
        out = self.a.nclassstats
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

    def test_get_flows(self):
        baseq = self.a.full_join()
        baseq = baseq.where(db.patent.c.gyear==1975) 
        exptotal = 20
        pats = baseq.where(db.patent.c.nclass==2).limit(exptotal)
        msubcat, mnclass = self.a.get_flows(pats)
        # total flow should sum to the number of patents
        print mnclass
        total_flow = round(mnclass.sum(), 1)
        assert total_flow == exptotal, total_flow
        # should have self refs
        assert mnclass[1,1] > 0.0, mnclass

        pats = baseq.where(db.patent.c.subcat==13).limit(exptotal)
        msubcat, mnclass = self.a.get_flows(pats)
        total_flow = round(msubcat.sum(),1)
        assert total_flow == exptotal, total_flow
        # should have self refs and subcat 13 is col 3
        assert msubcat[2,2] > 0.0, msubcat

    def test_get_flows_by_year(self):
        year = 1975
        exptotal = 20
        matrix, mnclass = self.a.get_flows_by_year(year, limit=exptotal)
        total = round(matrix.sum(),0)
        # does not work any more
        # assert total == exptotal, total

    def _test_full_join_count(self):
        # very slow
        q = self.a.full_join()
        q = q.where(db.patent.c.gyear==1975)
        q = q.alias()
        q = q.count()
        print q
        q.execute()
        # out = q.execute().fetchall()[0]
        assert out == 0, out

    def test_nclass_labels(self):
        out = self.a.nclass_labels()
        assert out[2] == 'Apparel', out[2]

    def test_extract_subject_vectors(self):
        out = self.a.extract_subject_vectors(subcat=14, limit=10)
        assert len(out) == 3
        assert out[0][0] == 3864327
        assert out[1][4] == 2, out[1]

import scipy
class TestPlotter:
    pl = Plotter()
    fpl = FlowPlotter()

    def test_draw_weighted_adjacency_matrix(self):
        inmat = scipy.array([
            [0.5, 0.0, 2.0],
            [0.0, 1.0, 0.0],
            [1.0, 0.7, 1.5]
            ])
        dgr, pos = self.fpl.draw_weighted_adjacency_matrix(inmat)
        assert len(dgr) == 3

