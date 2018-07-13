oldfile='/Users/dlk/newcgcaweb/people.html'
lines=open(oldfile).readlines()

entry=""
i=0
istart=None
istop=None
entries=[]
while i<len(lines):
    line=lines[i]
    if '<div class="col-2">' in line  and not '<!--' in line:
        istart=i
    if line.strip().startswith('</div>') and istart is not None:
        istop=i
        entry=''.join(lines[istart:istop+1])
        entries.append(entry)

    i+=1

f=open('commands.txt','w')
for entry in entries:
    phone='414-229-XXXX'
    office='KIRC XXXX'
    lines=entry.split('\n')
    for line in lines:
        if 'src=' in line and not 'email' in line:
            image=line.split('src="')[1].split('"')[0]
        if 'alt=' in line:
            name=line.split('alt="')[1].split('"')[0].strip()
        if 'javascript' in line:
            emailname=line.split("address('")[1].split("'")[0]
            emaildomain=line.split(",")[1].split(")")[0].replace("'","").strip()
        if 'medium' in line:
            position=line.split('>')[1].split('<')[0].strip()
        if '414-' in line:
            phone=line.split('>')[1].split('<')[0].strip()
        if 'KIRC' in line:
            office=line.split('>')[1].split('<')[0].strip()
    print '- name: ',name
    print '  emailname: ', emailname
    print '  emaildomain: ',emaildomain
    print '  position: ',position
    print '  phone: ',phone
    print '  office: ',office
    f.write('\mv ~/newcgcaweb/%s assets/imgs/people/%s.png\n' % (image,emailname))
    
    
    #print '--------------------------------------------------'
           
f.close()
