import os
import sqlobject

dbUri = 'postgres://rgrp@localhost/patent'
connection = sqlobject.connectionForURI(dbUri)
sqlobject.sqlhub.processConnection = connection

class Patent(sqlobject.SQLObject):
    gyear = sqlobject.IntCol(default=None)
    gdate = sqlobject.IntCol(default=None)
    appyear = sqlobject.IntCol(default=None)
    country = sqlobject.StringCol(length=3, default=None)
    postate = sqlobject.StringCol(length=3, default=None)
    assignee = sqlobject.IntCol(default=None)
    asscode = sqlobject.IntCol(default=None)
    claims = sqlobject.IntCol(default=None)
    nlass = sqlobject.IntCol(default=None)
    cat = sqlobject.IntCol(default=None)
    subcat = sqlobject.IntCol(default=None)
    cmade = sqlobject.IntCol(default=None)
    creceive = sqlobject.IntCol(default=None)
    ratiocit = sqlobject.DecimalCol(size=7,precision=4,default=None)
    general = sqlobject.DecimalCol(size=7,precision=4,default=None)
    original = sqlobject.DecimalCol(size=7,precision=4,default=None)
    fwdaplag = sqlobject.DecimalCol(size=7,precision=4,default=None)
    bckgtlag = sqlobject.DecimalCol(size=7,precision=4,default=None)
    selfctub = sqlobject.DecimalCol(size=7,precision=4,default=None)
    selfctlb = sqlobject.DecimalCol(size=7,precision=4,default=None)
    secdupbd = sqlobject.DecimalCol(size=7,precision=4,default=None)
    seclwbd = sqlobject.DecimalCol(size=7,precision=4,default=None)

class Citation(sqlobject.SQLObject):
    citing = sqlobject.ForeignKey('Patent')
    cited = sqlobject.IntCol(default=None)

Patent.createTable(ifNotExists=True)
Citation.createTable(ifNotExists=True)

def cleanPatentFile(filePath):
    # you should first have cleaned the file by doing this
    cmdDeleteFirstLine = "sed --in-place -e '1d' %s" % filePath
    cmdReplaceQuote = "sed --in-place -e 's/\"//g' %s" % filePath

def loadPatents(filePath):
    cmd = """psql -c "\copy patent from STDIN WITH DELIMITER AS ',' NULL AS ''" -d patent < %s""" % (filePath)
    os.system(cmd)
    # add one extra patent which seems to be missing: 4326083 (in cited stuff)
    # select setval('patent_id_seq', 6009555)
    # 4328291, 4380968, 4401173 4402520
    # select distinct citing_id into missing_patent from citation_without_serial where citing_id > 4401173 and not exists (select 1 from patent where patent.id = citing_id);
    # insert into patent (id) select * from missing_patent ;
    # select distinct cited into missing_cited from citation where not exists (select 1 from patent where patent.id = cited);


def loadCitations(filePath):
    psqlCmds = ["""create table citation_without_serial ( citing_id integer, cited_id integer );""",
                """\copy citation_without_serial from %s WITH DELIMITER AS ',' exit
                NULL AS ''""" % filePath,
                """INSERT INTO citation select nextval('citation_id_seq'), * from citation_without_serial;""",
                # 'drop table citation_without_serial;'
               ]
    for psqlCmd in psqlCmds:
        cmd = 'psql -c "%s" -d patent' % psqlCmd
        if os.system(cmd):
            print cmd

def loadPatentsSlowly(fileObj):
    import csv
    reader = csv.reader(fileObj)
    for row in reader:
        print row
        Patent( id=int(row[0]),
                number=int(row[0]),
                grantYear=int(row[1]),
                grantDate=int(row[2]),
                applicationYear=int(row[3]),
                country=row[4],
                state=row[5],
                assignee=int(row[6]),
                assocde=int(row[7]),
                numberOfClaims=int(row[8]),
                patentClass=int(row[9]),
                category=int(row[10]),
                subCategory=int(row[11])
              )
        print x.__dict__

import unittest
import StringIO
class TestCreateDb(unittest.TestCase):
    
    def testCreateDb(self):
        # create a patent and then delete it
        number = 1756906
        Patent(id=number)
        x = Patent.get(number)
        Patent.delete(x.id)
    
    def testLoadPatents(self):
        filePath = 'shortlist.txt'
        filePath2 = 'shortlist_cite.txt'
        loadPatents(filePath)
        loadCitations(filePath2)
    
    def testLoadPatentsSlowly(self):
        return
        # first and last patent but with numbers changed so they don't overlap with any existing patents
        inString = '3070801,1963,1096,,"BE","",,1,,269,6,69,,1,,0,,,,,,,'
        inString += '\n'
        inString += '6009545,1999,14606,1998,"JP","",379245,3,,714,2,22,9,0,1,,0.7407,,6.6667,0.1111,0.1111,,'
        fileLikeObject = StringIO.StringIO(inString)
        loadPatentsSlowly(fileLikeObject)
        pat = Patent.byNumber(3070801)
        Patent.delete(pat.id)
        pat = Patent.byNumber(6009545)
        Patent.delete(pat.id)

if __name__ == '__main__':
    # unittest.main()
    # loadPatents('pat63_99.txt')
    loadCitations('cite75.99.dat')
    

patentList

citationList = list of tuples

newCitationList:

for citation in citationList:
    citing = citation[0]
    cited = citation[1]
    distance1 = citation[2]
    newCited = getAllPatentsCitedBy(cited)
    for newCite,distance2 in newCited:
        newDistance = distance1 + distance2
        currentDistance = checkPreviousDistance(citing, newCite)
        if currentDistance == 0:
            insertIntoTransitionMatrix(citing, newCite, newDistance)
        elif currentDistance > newDistance:
            repalceInTransitionMatrix(citing, newCite, newDistance)
            
A, B, distance

haveChanged = True
while haveChanged:
    haveChanged = False
    for ii in len(matrix.rows):
        for col in row:
            if matrix(row, col) != 0:
                targetRow = matrix[jj]
                newRow = addToAllNonzero(targetRow, matrix(row,col))
                result = combineRow(row, newRow)
                matrix[ii] = result[0]
                haveChanged = haveChanged or result[1]
            
def combineRow(....):
    haveChanged = False
    for ii in len(row):
        if row(ii) == 0 or row[ii] > newRow[ii]:
            outRow[ii] = newRow[ii]
            flag = True
    return (outRow, haveChanged)
