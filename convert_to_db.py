'''
Setup:

1. Create db as specified by dburi:
    $ sudo -u postgres createdb --owner rgrp patent

NOTES:

  * The citation data contains duplicate entries (~3600 of them)
  * there are some citing patents in the cite data which do not exist in the
    patent db. There are approx 550 such and removing them takes the number of
    citations entries from 16516269 to 16512783 
'''
import os
from sqlalchemy import *
import sqlalchemy.orm as orm

missing_fn = 'missing_patents.txt'

dburi = 'postgres://rgrp:pass@localhost/patent'
engine = create_engine(dburi)
metadata = MetaData(bind=engine)

patent = Table('patent', metadata, 
    Column('id', Integer, primary_key=True),
    Column('gyear', Integer),
    Column('gdate', Integer),
    Column('appyear', Integer),
    Column('country', String(3)),
    Column('postate', String(3)),
    Column('assignee', Integer),
    Column('asscode', Integer),
    Column('claims', Integer),
    Column('nlass', Integer),
    Column('cat', Integer),
    Column('subcat', Integer),
    Column('cmade', Integer),
    Column('creceive', Integer),
    Column('ratiocit', Float(4)),
    Column('general', Float(4)),
    Column('original', Float(4)),
    Column('fwdaplag', Float(4)),
    Column('bckgtlag', Float(4)),
    Column('selfctub', Float(4)),
    Column('selfctlb', Float(4)),
    Column('secdupbd', Float(4)),
    Column('seclwbd', Float(4)),
)

citation = Table('citation', metadata,
    Column('citing', Integer, ForeignKey('patent.id'), primary_key=True),
    Column('cited', Integer, primary_key=True),
)

# existence of duplicates means we need table without primary key stuff
citation_tmp = Table('citation_tmp', metadata,
    Column('citing', Integer),
    Column('cited', Integer)
)

# class Patent(object):
#     pass
# 
# class Citation(object):
#     pass
# 
# orm.mapper(Patent, patent)
# orm.mapper(Citation, citation)
# 
# Session = orm.scoped_session(orm.sessionmaker(
#     autoflush=True,
#     transactional=False,
#     bind=engine
# ))


class PatentLoader(object):
    cmd_delete_first_line = 'sed -e "1d"'

    def __init__(self, engine):
        self.engine = engine

    def initdb(self):
        metadata.create_all(bind=self.engine)
    
    def cleandb(self):
        metadata.drop_all(bind=self.engine)

    def load_patents(self, filepath):
        # you should first have cleaned the file by doing this
        cmdReplaceQuote = """sed -e 's/\\"//g'"""

        pgcmd = '''psql --echo-all -c "\copy patent from STDIN WITH DELIMITER AS ',' NULL AS ''" -d patent '''
        catcmd = 'cat %s ' % filepath
        cmd = catcmd + ' | ' + self.cmd_delete_first_line + ' | ' + cmdReplaceQuote + ' | '  + pgcmd
        print cmd
        os.system(cmd)
        # add one extra patent which seems to be missing: 4326083 (in cited stuff)
        # select setval('patent_id_seq', 6009555)
        # 4328291, 4380968, 4401173 4402520
        # select distinct citing_id into missing_patent from citation_without_serial where citing_id > 4401173 and not exists (select 1 from patent where patent.id = citing_id);
        # insert into patent (id) select * from missing_patent ;
        # select distinct cited into missing_cited from citation where not exists (select 1 from patent where patent.id = cited);


    def load_citations(self, filepath):
        pgcmdbase = 'psql -c "%s" -d patent'
        pgcmd = pgcmdbase % "\copy citation_tmp from STDIN WITH DELIMITER AS ',' NULL AS ''"
        cmddeleteline = 'sed -e "%sd"'
        catcmd = 'cat %s' % filepath
        loadcmd = catcmd + ' | ' + self.cmd_delete_first_line + ' | ' + pgcmd
        copycmd = pgcmdbase % 'insert into citation select distinct * from citation_tmp;'

        cmds = [
            # pgcmdbase % 'create table citation_tmp( citing integer, cited integer );',
            # loadcmd,
            # copycmd,
            # pgcmdbase % 'drop table citation_tmp;',
            ]
        os.system(loadcmd)
        self.find_missing_patents()
        self.delete_citations_with_no_patent()
        print copycmd
        os.system(copycmd)

    def find_duplicates(self):
        # whole bunch of duplicates in citation table! 
        # 3474!
        # select citing, cited, count(*) from citation_tmp group by citing, cited having count(*) > 1;
        myt = citation_tmp
        q = select([myt.c.citing, myt.c.cited, func.count('*')])
        q = q.group_by(myt.c.citing)
        q = q.group_by(myt.c.cited)
        q = q.having(func.count('*') > 1)
        # q = q.having(func.count(myt.c.citing
        print q
        out = q.execute().fetchall()
        print len(out)
        print out

    def find_missing_patents(self):
        '''Some citing id are missing from patent table so remove them from
        citations. Approx 550.
        
        select distinct citing from citation_tmp where citing > 4326083 and not exists (select 1 from patent where patent.id = citing);
        '''
        # use this info to speed things up
        firstone = 4326083
        q = select([citation_tmp.c.citing])
        q = q.where(citation_tmp.c.citing > firstone -1)
        rawexists = 'select 1 from patent where patent.id = citing'
        q = q.where(not_(
            func.exists(rawexists)
            ))
        q = q.distinct()
        # have to do it by hand as exists clause does not substitute correctly
        # have quotes around select ...
        # out = q.execute().fetchall()
        rawq = str(q)
        rawq = rawq % { 'citing_1' : firstone -1, 'exists_1' : rawexists }
        # print rawq
        conn = engine.connect()
        out = conn.execute(rawq).fetchall()
        out = [ x[0] for x in out ]
        # list of ids
        fo = file(missing_fn, 'w')
        for id in out:
            fo.write(id)
            fo.write('\n')
        return out

    def delete_citations_with_no_patent(self):
        idsdata = open(missing_fn).read()
        ids = [ int(line) for line in idsdata ]
        for id in ids:
            q = citation_tmp.delete()
            q = q.where(citation_tmp.c.citing == id)
            print 'Deleting: %s' % id
            q.execute()

import unittest
import StringIO
class TestCreateDb:
    loader = PatentLoader(engine)
    filepath = 'data/shortlist.txt'
    filepath2 = 'data/shortlist_cite.txt'
    pdata = \
'''"PATENT","GYEAR","GDATE","APPYEAR","COUNTRY","POSTATE","ASSIGNEE","ASSCODE","CLAIMS","NCLASS","CAT","SUBCAT","CMADE","CRECEIVE","RATIOCIT","GENERAL","ORIGINAL","FWDAPLAG","BCKGTLAG","SELFCTUB","SELFCTLB","SECDUPBD","SECDLWBD"
3070801,1963,1096,,"BE","",,1,,269,6,69,,1,,0,,,,,,,
3070802,1963,1096,,"US","TX",,1,,2,6,63,,0,,,,,,,,,
3070803,1963,1096,,"US","IL",,1,,2,6,63,,9,,0.3704,,,,,,,
3070804,1963,1096,,"US","OH",,1,,2,6,63,,3,,0.6667,,,,,,,
3070805,1963,1096,,"US","CA",,1,,2,6,63,,1,,0,,,,,,,
'''
    # head of citation data modded for tests
    Cdata = \
'''"CITING","CITED"
3070801,956203
3070801,1324234
3070801,3070804
3070801,3557384
3070801,3634889
3070804,1515701
3070804,3319261
3070804,3668705
'''

    def setUp(self):
        self.loader.cleandb()
        self.loader.initdb()
        file(self.filepath, 'w').write(self.pdata)
        file(self.filepath2, 'w').write(self.cdata)
    
    def test_created_ok(self):
        # create a patent and then delete it
        number = 1756906
        ins = patent.insert({'id': number})
        ins.execute()
        q = patent.count()
        q = q.where(patent.c.id==number)
        out = q.execute().fetchall()[0][0]
        assert out == 1, out
    
    def test_load_patents(self):
        self.loader.load_patents(self.filepath)
        q = patent.count()
        out = q.execute().fetchall()[0][0]
        assert out == 5, out
        out = patent.select().execute().fetchall()[0]
        assert out.id == 3070801
        assert out.gyear == 1963
        assert out.gdate == 1096

    def test_load_citations(self):
        self.loader.load_patents(self.filepath)
        self.loader.load_citations(self.filepath2)
        # TODO: test


def main():
    loader = PatentLoader(engine)
    loader.initdb()
    patfile = 'data/apat63_99.txt'
    citefile = 'data/cite75_99.txt'
    loader.load_patents(patfile)
    loader.load_citations(citefile)

if __name__ == '__main__':
    loader = PatentLoader(engine)
    # a = PatentAnalyzer(engine)

