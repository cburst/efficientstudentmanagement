mysp=__import__("my-voice-analysis")
import re
import sys
import os

# Get the filename from the command-line argument
filename = os.path.basename(sys.argv[1])

# Remove the file extension
filename_without_ext = os.path.splitext(filename)[0]



p=filename_without_ext
c=r"~/Downloads/my-voice-analysis-master/speakingsamples/"


mysp.myspsyl(p,c)
mysp.mysppaus(p,c)
mysp.myspsr(p,c)
mysp.myspatc(p,c)
mysp.myspst(p,c)
mysp.myspod(p,c)
mysp.myspbala(p,c)
