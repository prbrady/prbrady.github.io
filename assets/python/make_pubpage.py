import ads
import requests
import math
import json,os,datetime,shutil,sys
from optparse import OptionParser

# use like:
# python python/make_pubpage.py -l cgca -d _includes/

# look at https://github.com/adsabs/ads-examples/tree/master/library_csv

format='%ZEncoding:html%ZLinelength:0<li>%3.3M %Y, <A href="%u">%T</A>, %J, <strong>%V</strong>, %p. <a href="https://arxiv.org/abs/%X">%X</a>. DOI: <a href="https://doi.org/%d">%d</a>.</li>\n'
# when there is no DOI this messes things up
#format='%ZEncoding:html%ZLinelength:0<li>%3.3M %Y, <A href="%u">%T</A>, %J, <strong>%V</strong>, %p.</li>\n'

libraries={'kaplan': 'AtijQpcVQomL3joNFBVn2A',
           'cgca': 'rPiNON1ZQjawuMxyDLfKTA'}

token=None

def get_config():
    """
    Load ADS developer key from file
    :return: str
    """
    global token
    if token is None:
        try:
            with open(os.path.expanduser('~/.ads/dev_key')) as f:
                token = f.read().strip()
        except IOError:
            print('The script assumes you have your ADS developer token in the'
                  'folder: {}'.format())

    return {
        'url': 'https://api.adsabs.harvard.edu/v1/biblib',
        'headers': {
            'Authorization': 'Bearer:{}'.format(token),
            'Content-Type': 'application/json',
        }
    }

def get_library(library_id, num_documents=0):
    """
    Get the content of a library when you know its id. As we paginate the
    requests from the private library end point for document retrieval,
    we have to repeat requests until we have all documents.
    :param library_id: identifier of the library
    :type library_id:
    :param num_documents: number of documents in the library
    :type num_documents: int
    :return: list
    """

    config = get_config()

    start = 0
    rows = 25
    if num_documents>0:
        num_paginates = int(math.ceil(num_documents / (1.0*rows)))
    else:
        num_paginates=1

    documents = []
    r = requests.get(
        '{}/libraries/{id}?start={start}&rows={rows}'.format(
        config['url'],
        id=library_id,
        start=start,
        rows=rows
        ),
        headers=config['headers']
        )
    if num_documents==0:
        num_documents=r.json()['solr']['response']['numFound']
        num_paginates = int(math.ceil(num_documents / (1.0*rows)))
        #print num_documents,num_paginates
        
    # Get all the documents that are inside the library
    try:
        data = r.json()['documents']
    except ValueError:
        raise ValueError(r.text)
    
    documents.extend(data)

    start += rows

    for i in range(1,num_paginates):
        #print('Pagination {} out of {}'.format(i+1, num_paginates))

        r = requests.get(
            '{}/libraries/{id}?start={start}&rows={rows}'.format(
                config['url'],
                id=library_id,
                start=start,
                rows=rows
            ),
            headers=config['headers']
        )
        if num_documents==0:
            num_documents=r.json()['solr']['response']['numFound']
            num_paginates = int(math.ceil(num_documents / (1.0*rows)))
            #print num_documents,num_paginates

        # Get all the documents that are inside the library
        try:
            data = r.json()['documents']
        except ValueError:
            raise ValueError(r.text)

        documents.extend(data)

        start += rows

    return documents



parser = OptionParser()
parser.add_option("-l", "--library", dest="library",
                  default='kaplan',
                  choices=libraries.keys(),
                  help="Library to process [deault=%default]")
parser.add_option('-r','--reload',default=False,dest='reload',
                  action='store_true',
                  help='Force reload')
parser.add_option('-d','--directory',
                  dest='directory',default='_includes/',
                  help='Output directory [default=%default]')
parser.add_option('-i','--imagedirectory',
                  dest='imagedirectory',default='./assets/imgs/publications/',
                  help='Image output directory [default=%default]')
parser.add_option('-y','--years',
                  dest='years',default=5,
                  help='Number of years for recent list [default=%default]')

(options, args) = parser.parse_args()
bibcodefile=os.path.join(options.directory,options.library+'.bibcodes')
if not os.path.exists(bibcodefile) or options.reload:
    bibcodes = get_library(
        library_id=libraries[options.library],
        num_documents=0
        )
    try:
        f=open(bibcodefile,'w')
        f.write(' '.join(bibcodes) + '\n')
        f.close()
    except:
        print('Error writing %s' % bibcodefile)
        sys.exit(1)
else:
    try:
        with open(bibcodefile) as f:
            bibcodes = f.read().strip().split()
    except IOError:
        print('Error reading bibcodes from %s' % bibcodefile)
        sys.exit(1)
        
# do this to get metrics summaries
# would be better to import pythonically, but that's harder
runpath=os.path.split(os.path.realpath(__file__))[0]
command='python %s/ads-examples/metrics/plot_metrics.py --bibcodes `cat %s` --plot -f png --save-to-file csv -o %s' % (runpath,bibcodefile,options.directory)
os.system(command)
metrics_plot=os.path.join(options.directory,'metrics.png')
metrics_file=os.path.join(options.directory,'metrics.txt')
if not os.path.exists(metrics_plot):
    print('Metrics plot %s does not exist' % metrics_plot)
    sys.exit(1)
if not os.path.exists(metrics_file):
    print('Metrics file %s does not exist' % metrics_file)
    sys.exit(1)

firstyear=datetime.datetime.now().year-options.years
years=[int(bibcode[:4]) for bibcode in bibcodes]
#articles = [list(ads.SearchQuery(bibcode=bibcode))[0] for bibcode in bibcodes]
bibcodes_toprint=[]
for bibcode,year in zip(bibcodes,years):
    if year>=firstyear:
        bibcodes_toprint.append(bibcode)
content=''
numbertograb=50
for i in xrange(0,len(bibcodes_toprint),numbertograb):    
    print('Reading bibcodes %d to %d...' % (i,i+numbertograb))
    payload={"bibcode": bibcodes_toprint[i:(i+numbertograb)],
             "format": format}
    config = get_config()
    r = requests.post("https://api.adsabs.harvard.edu/v1/export/custom", 
                      headers=config['headers'],
                      data=json.dumps(payload))
    content+=r.json()['export'].encode('utf-8').strip()

# change format of arXiv record slightly to make it work as URL
content=content.replace('abs/arXiv:','abs/')

try:
    with open(metrics_file) as f:
        lines=f.readlines()
except IOError:
    print('Error reading metrics file %s' % metrics_file)
for line in lines:
    if line.startswith('Number of papers'):
        number_of_papers=int(line.split()[-2])
    if line.startswith('Total citations'):
        total_citations=int(line.split()[-2])
    if line.startswith('H Index'):
        h_index=int(line.split()[-2])

try:
    shutil.copyfile(metrics_plot, os.path.join(options.imagedirectory,os.path.split(metrics_plot)[-1]))
except:
    print('Unable to copy file %s to %s' % (metrics_plot,
                                            options.imagedirectory))
    sys.exit(1)
    
    
outfile=os.path.join(options.directory,'publications.html')
try:
    f=open(outfile,'w')
except IOError:
    print('Unable to write %s' % outfile)

f.write("""<main role="main">
      
<div class="container marketing">
<h3 class="featurette-heading">Recent Publications: <span
class="text-muted">(last %d years)</span></h3>\n\n""" % options.years)
f.write('<a href="%s/%s"><img class="float-right img-responsive" width="50%%" src="%s/%s"></a>\n' % (options.imagedirectory,
                                                                                                     os.path.split(metrics_plot)[-1],
                                                                                                     options.imagedirectory,
                                                                                                     os.path.split(metrics_plot)[-1]))
                                                                                                  
f.write('Total papers: %d<br>\n' % number_of_papers)
f.write('Total citations: %d<br>\n' % total_citations)
f.write('H-index: %d<br>\n' % h_index)
f.write('<p><small><span class="text-muted">Publications via <a href="https://ui.adsabs.harvard.edu/#/public-libraries/%s"><span class="s1">ADS Library</span></a></small>.</p>\n' % libraries[options.library])


f.write('<ol>\n')
f.write(content)
f.write('</ol>\n')
f.write("""<!-- /END THE FEATURETTES -->       
     </div><!-- /.container -->""")
f.close()    

    
sys.exit(0)
