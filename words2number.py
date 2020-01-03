#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
import json
import sys
import re
from multiprocessing import Process
from words2num import words2num, NumberParseException
from num2words import num2words

number_blocks = [
    'trillion','billion', 'million', 'thousand', 'hundred'
]

digits = [
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'zero', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'
]

decades = [
    'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'
]

dnb=digits+number_blocks
dd=digits+decades
den=number_blocks+decades

getallen = {
    'zero': 0,
    'and': 0,
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'eleven': 11,
    'twelve': 12,
    'thirteen': 13,
    'fourteen': 14,
    'fifteen': 15,
    'sixteen': 16,
    'seventeen': 17,
    'eighteen': 18,
    'nineteen': 19,
    'twenty': 20,
    'thirty': 30,
    'forty': 40,
    'fifty': 50,
    'sixty': 60,
    'seventy': 70,
    'eighty': 80,
    'ninety': 90,
    'hundred': 100,
    'thousand': 1000,
    'million': 1000000,
    'billion': 1000000000,
    'trillion': 1000000000000
}

looked=False
line=''

class Transcript:

    def __init__(self):
        self.words = []
        self.ident = ''
        self.event = ''
        self.channel = []
        self.start = []
        self.duration = []
        self.pp = []
        self.result = []
        self.offset = []
        self.valid = False

    def isValid(self):
        return self.valid

    def __byteify(self, input):
        if isinstance(input, dict):
            return {byteify(key): byteify(value)
                    for key, value in input.iteritems()}
        elif isinstance(input, list):
            return [byteify(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input

    def readInput(self, inputstring):
        global looked
        global line

        if not looked:
            # line = sys.stdin.readline()
            line = inputstring
        else:
            looked = False
        if not line:
            self.valid = False
            return

        self.valid = True

        while re.match(r'^(\S+)\s+\S+\s+[0-9.]+\s+[0-9.]+\s+\S+(\s+[0-9.]+)?$', line):
            # print("line is : ",line)
            # For a CTM file read all lines with the same file descriptor (column 1)
            parts = line.strip().split()
            # print("parts is: ",parts)
            if (not self.ident) or (parts[0] == self.ident):
                # treat the ctm as a single line for each identifier string
                self.ident = parts[0]
                self.channel.append(parts[1])
                self.start.append(float(parts[2]))
                self.duration.append(float(parts[3]))
                self.words.append(parts[4])
                if len(parts) > 5:
                    self.pp.append(float(parts[5]))
                line = sys.stdin.readline()
                # print("linne here : "+line)
                if not line:
                    break
            else:
                # new identifier
                looked = True
                break

        if not self.ident:
            # file is either JSON or plaintext
            try:
                self.event = json.loads(line)
                # We assume that JSON content follows the format that is produced
                # by the Kaldi-ASR system. This script can be used as a post processing step,
                # for example in 'live' recognition
                # pull apart to process each entry
                for hypo in self.event["result"]["hypotheses"]:
                    line = self.__byteify(hypo["transcript"])
                    line = re.sub(r'(\S)(\.|,)', r'\1 \2', line)
                    self.words.extend(line.strip().split())
                    self.words.append("ENDTRANSCRIPT")
                    if hypo["transcript"]:
                        # sometimes we get empty transcripts and therefore empty alignments.
                        for word in hypo["word-alignment"]:
                            self.words.append(self.__byteify(word["word"]))
                            self.start.append(float(word["start"]))
                            self.duration.append(float(word["length"]))
                            self.pp.append(float(word["confidence"]))
                    self.words.append("ENDHYPO")
            except:
                # plaintext input may have certain punctuation that may interfere with the detection of numbers
                line = re.sub(r'(\S)(\.|,)', r'\1 \2', line)
                self.words = line.strip().split()

    def convertBlock(self, words):

        # Convert a list of words into an integer value.
        # The input list should only contain numeric terms

        value = 0
        nomatch = True
        # print("words: ",words)
        result = words2num(" ".join(words))
        # print("result: ",result)
        return result

        # for i, w in enumerate(den):
        #     try:
        #         index = words.index(den[i])
        #         if index == 0:
        #             value = 1
        #         else:
        #             value = self.convertBlock(words[0:index])
        #             print("value in else is : ",value)
        #         rest = self.convertBlock(words[index + 1:])
        #         print("value rest is : ",rest)
        #         value = (value * getallen[w]) + rest
        #         print("value final is : ",value)
        #         nomatch = False
        #         break
        #     except:
        #         continue

        # if nomatch:
        #     for w in words:
        #         value += getallen[w]
        # print("at end ",value)
        # return value

    def convert(self):
        numbers = []
        for w in self.words:
            # print("w here :   ",w)
            if (w in dd and len(numbers)>0 and numbers[-1] in dd):
                # print("in first if")
                # print("number -1 is ", numbers[-1])
                if(w in digits and len(numbers)>0 and numbers[-1] in decades):
                    numbers.append(w)
                else:
                    self.result.append(str(self.convertBlock(numbers)))
                    # print("self result is: ",self.result)
                    self.offset.append(len(numbers))
                    # print("lenth is ",len(numbers))
                    # print("w in first if is : "+ w)
                    numbers = []
                    numbers.append(w)
                    # print("numbers in first if ",numbers)
            elif (w in digits and len(numbers) > 1 and numbers[-1] == 'and' and numbers[-2] in ['hundred', 'thousand']):
                # print("in first elif")
                numbers.append(w)
            elif (w in dnb and len(numbers)>1 and numbers[-1]=='and' and numbers[-2] in dnb) or (w=='and' and len(numbers)>0 and numbers[-1] not in dnb):
                # print("in second elif")
                self.result.append(str(self.convertBlock(numbers)))
                self.offset.append(len(numbers)-1)
                self.result.append('and')
                self.offset.append(1)
                numbers=[]
                numbers.append(w)
                # print("number in second elif is : ", numbers)
            elif (w=='and' and len(numbers)==0):
                # print("in third elif")
                self.result.append('and')
                self.offset.append(1)
            elif w in getallen:
                # print("in fourth elif")
                # print("w here is : "+w)
                numbers.append(w)
                # print("number in fourth elif is : ", numbers)
            else:
                # print("in else")
                if len(numbers):
                    # print("in else then if")
                    self.result.append(str(self.convertBlock(numbers)))
                    if numbers[-1]=='and':
                        # print("in else then if then if")
                        self.result.append('and')
                        self.offset.append(len(numbers)-1)
                        self.offset.append(1)
                    else: self.offset.append(len(numbers))
                    numbers = []
                self.result.append(w)
                self.offset.append(1)
        if len(numbers):
            self.result.append(str(self.convertBlock(numbers)))
            self.offset.append(len(numbers))

    def handleCommas(self):
        # remove spaces for individual digits after a comma (used as a period in Dutch)
        # and replace the word comma with an actual comma
        i=1
        while i<(len(self.result)-1):
            if self.result[i]=='komma' and re.match(r'\d+', self.result[i-1]) and re.match(r'\d+', self.result[i+1]):
                # print("in while if")
                self.result[i-1]=self.result[i-1] + ',' + self.result[i+1]
                self.offset[i-1]+=1 + self.offset[i+1]
                del self.result[i: i+2]
                del self.offset[i: i+2]
                while len(self.result)>i and re.match(r'^\d$', self.result[i]):
                    # after a comma, add any additional individual digits
                    self.result[i-1]=self.result[i-1] + self.result[1]
                    self.offset[i-1]+=self.offset[i]
                    del self.result[i]
                    del self.offset[i]
            else:
                i+=1

    def handleCombos(self):
        # Typically a combination of two 2-digit terms refers to either a calendar year or part of a Dutch zipcode
        # We combine them if possible, but beware that this may introduce mistakes here and there
        i = 1
        while i < (len(self.result)):
            if re.match(r'^\d{2}$', self.result[i-1]) and re.match(r'^\d{2}$', self.result[i]):
                if (i>1 and re.match(r'^\d{2}$', self.result[i-2])) or (i<(len(self.result)-1) and re.match(r'^\d{2}$', self.result[i+1])):
                    # don't do anything if it's not just two two-digit groups
                    # print("combo if")
                    i+=1
                else:
                    # print("combo else")
                    self.result[i-1]=self.result[i-1]+self.result[i]
                    self.offset[i-1]+=self.offset[i]
                    del self.result[i]
                    del self.offset[i]
            else:
                i+=1

    def words2num(self):
        self.convert()
        self.handleCommas()
        self.handleCombos()

    def getResult(self):
        output=''

        if self.ident:
            # if the input was a .ctm file, recreate it
            i = 0
            ii = 0
            while i < len(self.result):
                output += "%s %s %.2f %.2f %s" % ( self.ident, self.channel[ii], self.start[ii], sum(self.duration[ii:ii+self.offset[i]]), self.result[i] )
                if len(self.pp):
                    output +=  "%.3f\n" % ( min(self.pp[ii:ii+self.offset[i]]) )
                else:
                    output += "\n"
                ii+=self.offset[i]
                i+=1

        elif self.event:
            # rebuild the json string, be non-destructive
            event = self.event.copy()
            result = self.result[:]
            offset = self.offset[:]
            duration = self.duration[:]
            start = self.start[:]
            pp = self.pp[:]

            i = 0
            hypno = 0
            while len(result):
                wa=0
                # rewrite the transcript part
                while result[0]!="ENDTRANSCRIPT":
                    output += result[0] + ' '
                    del result[0]
                    del offset[0]
                del result[0]
                del offset[0]

                # get rid of the extra space before some punctuation
                output = re.sub(r'\s(\.|,)', r'\1', output)
                event["result"]["hypotheses"][hypno]["transcript"]=output.strip()
                output = ''
                # rewrite the individual words
                while result[0]!="ENDHYPO":
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["word"]=result[0]
                    del result[0]
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["start"]=start[0]
                    del start[:offset[0]]
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["length"]=sum(duration[:offset[0]])
                    del duration[:offset[0]]
                    event["result"]["hypotheses"][hypno]["word-alignment"][wa]["confidence"] = min(pp[:offset[0]])
                    del pp[:offset[0]]
                    wa += 1
                    del offset[0]
                try:
                    while 1: del event["result"]["hypotheses"][hypno]["word-alignment"][wa]
                except:
                    pass
                del result[0]
                del offset[0]
                hypno+=1
            output = json.dumps(event)

        else:
            # or just output plaintext
            if len(self.result)>0:
                output=' '.join(self.result)
            else:
                output=''
            # get rid of the extra space before some punctuation
            output=re.sub(r'\s(\.|,)', r'\1', output)

        # print(output)
        if(re.search(r'\d[\s\d]*\d',output)):
            regstring=re.findall(r'\d[\s\d]*\d',output)
            # print("???? ",regstring)
            if(len(regstring)>0):
                for x in regstring:
                    # print(x)
                    output=output.replace(x,x.replace(" ",""))
  
            # re.sub(r'\d[\s\d]*',regstring.replace(" ",""),output)
        return output

def main():
    while True:
        transcript = Transcript()
        transcript.readInput()
        if transcript.isValid():
            transcript.words2num()
            print(transcript.getResult())
            # sys.stdout.flush()
        else:
            break

if __name__ == "__main__":
    main()