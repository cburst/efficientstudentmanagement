"""
This script analyzes all text files (with the .txt suffix only) in a single folder or directory.  

It counts the occurrences of the following 9 structures in each text: words (W), sentences (S), verb phrases (VP), clauses (C), T-units (T), dependent clauses (DC), complex T-units (CT), coordinate phrases (CP), and complex nominals (CN). 

These frequency counts are then used to compute the following 14 syntactic complexity indices of each text: mean length of sentence (MLS), mean length of T-unit (MLT), mean length of clause (MLC), clauses per sentence (C/S), verb phrases per T-unit (VP/T), clauses per T-unit (C/T), dependent clauses per clause (DC/C), dependent clauses per T-unit (DC/T), T-units per sentence (T/S), complex T-unit ratio (CT/T), coordinate phrases per T-unit (CP/T), coordinate phrases per clause (CP/C), complex nominals per T-unit (CN/T), and complex nominals per clause (CN/C). 

To run the script, type the following at the command line:
python analyzeText.py inputFileDirectory outputFileName

inputFileDirectory is the path to the directory or folder that contains the text files you want to analyze (e.g., /home/inputFiles/). The path should end with a slash, as in the example. outputFileName is the name you want to assign to the output file. Both must be provided. 

The first line of the output file will be a comma-delimited list of 24 fields (including Filename, abbreviations of the 9 structures, and abbreviations of the 14 syntactic complexity indices). The subsequent lines of the file will each provide a comma-delimited list of 24 values for one input file (including the name of the file, frequency counts of the 9 structures, and the values of the 14 syntactic complexity indices). This format may be hard to read but allows easy import to Excel or SPSS. 
"""

import sys, os, subprocess, glob, re

#a function to divide two numbers from strings
def division(x,y):
    if float(x)==0 or float(y)==0:
        return 0
    return float(x)/float(y)

#the following is a list of tregex patterns for various structures

#sentence (S)
s="'ROOT !> __'"

#verb phrase (VP)
vp="'VP > S|SINV|SQ'"
vp_q="'MD|VBZ|VBP|VBD > (SQ !< VP)'" 

#clause (C)
c="'S|SINV|SQ [> ROOT <, (VP <# VB) | <# MD|VBZ|VBP|VBD | < (VP [<# MD|VBP|VBZ|VBD | < CC < (VP <# MD|VBP|VBZ|VBD)])]'"

#T-unit (T)
t="'S|SBARQ|SINV|SQ > ROOT | [$-- S|SBARQ|SINV|SQ !>> SBAR|VP]'"

#dependent clause (DC)
dc="'SBAR < (S|SINV|SQ [> ROOT <, (VP <# VB) | <# MD|VBZ|VBP|VBD | < (VP [<# MD|VBP|VBZ|VBD | < CC < (VP <# MD|VBP|VBZ|VBD)])])'"

#complex T-unit (CT)
ct="'S|SBARQ|SINV|SQ [> ROOT | [$-- S|SBARQ|SINV|SQ !>> SBAR|VP]] << (SBAR < (S|SINV|SQ [> ROOT <, (VP <# VB) | <# MD|VBZ|VBP|VBD | < (VP [<# MD|VBP\
|VBZ|VBD | < CC < (VP <# MD|VBP|VBZ|VBD)])]))'"

#coordinate phrase (CP)
cp="'ADJP|ADVP|NP|VP < CC'"

#complex nominal (CN)
cn1="'NP !> NP [<< JJ|POS|PP|S|VBG | << (NP $++ NP !$+ CC)]'"
cn2="'SBAR [<# WHNP | <# (IN < That|that|For|for) | <, S] & [$+ VP | > VP]'"
cn3="'S < (VP <# VBG|TO) $+ VP'"

#fragment clause
fc="'FRAG > ROOT !<< (S|SINV|SQ [> ROOT <, (VP <# VB) | <# MD|VBZ|VBP|VBD | < (VP [<# MD|VBP|VBZ|VBD | < CC < (VP <# MD|VBP|VBZ|VBD)])])'"

#fragment T-unit
ft="'FRAG > ROOT !<< (S|SBARQ|SINV|SQ > ROOT | [$-- S|SBARQ|SINV|SQ !>> SBAR|VP])'"

#list of patterns to search for
patternlist=[s,vp,c,t,dc,ct,cp,cn1,cn2,cn3,fc,ft,vp_q]

#location of the Stanford parser
parserPath="stanford-parser-full-2020-11-17/lexparser.sh"

#path to the directory or folder containing input files
directoryPath=sys.argv[1]

#output file name
outputFile=open(sys.argv[2],"w")

#write a list of 24 comma-delimited fields to the output file
fields="Filename,W,S,VP,C,T,DC,CT,CP,CN,MLS,MLT,MLC,C/S,VP/T,C/T,DC/C,DC/T,T/S,CT/T,CP/T,CP/C,CN/T,CN/C"
outputFile.write(fields+"\n")

#process text files in the directory one by one
for filename in glob.glob( os.path.join(directoryPath, '*.txt') ):
    print('Processing '+filename+'...')

    #Extract the name of the file being processed
    output=filename.split('/')[-1]

    #name a temporary file to hold the parse trees of the input file
    parsedFile=filename+".parsed"

    #parse the input file
    command=parserPath + " " + filename + " > " + parsedFile
    a=subprocess.getoutput(command).split('\n')[-1].split()

    #list of counts of the patterns
    patterncount=[]

    #query the parse trees using the tregex patterns
    for pattern in patternlist:
        command = "./tregex.sh " + pattern + " " + parsedFile + " -C -o"
        count = subprocess.getoutput(command).split('\n')[-1]
        patterncount.append(int(count))

    #update frequencies of complex nominals, clauses, and T-units
    patterncount[7]=patterncount[-4]+patterncount[-5]+patterncount[-6]
    patterncount[2]=patterncount[2]+patterncount[-3]
    patterncount[3]=patterncount[3]+patterncount[-2]
    patterncount[1]=patterncount[1]+patterncount[-1]
        
    #word count
    infile=open(parsedFile,"r")
    content=infile.read()
    w = len(re.findall("\\([A-Z]+\\$? [^\\)\\(-]+\\)", content))
    infile.close()
        
    #add frequencies of words and other structures to output string
    output+=","+str(w) #number of words
    for count in patterncount[:8]:
        output+=","+str(count)

    #list of frequencies of structures other than words
    [s,vp,c,t,dc,ct,cp,cn]=patterncount[:8]

    #compute the 14 syntactic complexity indices
    mls=division(w,s)
    mlt=division(w,t)
    mlc=division(w,c)
    c_s=division(c,s)
    vp_t=division(vp,t)
    c_t=division(c,t)
    dc_c=division(dc,c)
    dc_t=division(dc,t)
    t_s=division(t,s)
    ct_t=division(ct,t)
    cp_t=division(cp,t)
    cp_c=division(cp,c)
    cn_t=division(cn,t)
    cn_c=division(cn,c)

    #add syntactic complexity indices to output string
    for ratio in [mls,mlt,mlc,c_s,vp_t,c_t,dc_c,dc_t,t_s,ct_t,cp_t,cp_c,cn_t,cn_c]:
        output+=","+str("%.4F" % ratio)

    #write output string to output file
    outputFile.write(output+"\n")

    #delete the temporary file holding the parse trees
    command="rm "+parsedFile
    os.popen(command)

outputFile.close()

print('Done. Output was saved to ' + sys.argv[2] +'.')
