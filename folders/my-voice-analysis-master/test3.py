mysp=__import__("my-voice-analysis")
import re
import sys
import os

filename = filename = os.path.basename(sys.argv[1])

filename_without_ext = os.path.splitext(filename)[0]


p=os.path.splitext(filename)[0]


# Get the directory of the current script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Set the path to the 'speakingsamples' directory
c = os.path.join(script_directory, 'speakingsamples')


mysp.myspsyl(p,c)
mysp.mysppaus(p,c)
mysp.myspsr(p,c)
mysp.myspatc(p,c)
mysp.myspst(p,c)
mysp.myspod(p,c)
mysp.myspbala(p,c)
mysp.myspf0mean(p,c)
mysp.myspf0sd(p,c)
mysp.myspf0med(p,c)
mysp.myspf0min(p,c)
mysp.myspf0max(p,c)
mysp.myspf0q25(p,c)
mysp.myspf0q75(p,c)
mysp.mysppron(p,c)
