from analyze import Analyzer, db

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

    def test_get_flows_slow_nclass(self):
        pats = db.Patent.query.filter_by(gyear=1975).filter_by(nclass=2).limit(20)
        msubcat, mnclass = self.a.get_flows_slow(pats)
        # total flow should sum to the number of patents
        total_flow = mnclass.sum()
        assert round(total_flow, 1) == 20.0, total_flow
        # should have self refs
        assert mnclass[1,1] > 0.0, mnclass

    def get_get_flows_slow_subcat(self):
        pats = db.Patent.query.filter_by(gyear=1975).filter_by(subcat=13).limit(20)
        msubcat, mnclass = self.a.get_flows_slow(pats)
        # total flow should sum to the number of patents
        total_flow = msubcat.sum()
        assert round(total_flow, 1) == 20.0, total_flow
        # should have self refs and subcat 13 is col 3
        assert msubcat[2,2] > 0.0, msubcat

    def test_get_flows_by_year(self):
        year = 1975
        exptotal = 20
        matrix, mnclass = self.a.get_flows_by_year(year, limit=exptotal)
        total = round(matrix.sum(),0)
        assert total == exptotal, total

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
        print out['p2_id'] == 3357959

