# coding: utf-8

from __future__ import division, print_function

from nltk.tokenize import word_tokenize

import models
import data

import theano
import sys
import re
from io import open

import theano.tensor as T
import numpy as np


numbers = re.compile(r'\d')
is_number = lambda x: len(numbers.sub('', x)) / len(x) < 0.6

class PunctuateRestore:

    def __init__(self):
        self.valid = False

    def to_array(self,arr, dtype=np.int32):
        # minibatch of 1 sequence as column
        return np.array([arr], dtype=dtype).T

    def convert_punctuation_to_readable(self,punct_token):
        if punct_token == data.SPACE:
            return ' '
        elif punct_token.startswith('-'):
            return ' ' + punct_token[0] + ' '
        else:
            return punct_token[0] + ' '

    def punctuate(self, predict, word_vocabulary, punctuation_vocabulary, reverse_punctuation_vocabulary, reverse_word_vocabulary, words, show_unk):
        finalstring="";

        if len(words) == 0:
            sys.exit("Input text from stdin missing.")

        if words[-1] != data.END:
            words += [data.END]

        i = 0

        while True:

            subsequence = words[i:i+data.MAX_SEQUENCE_LEN]

            if len(subsequence) == 0:
                break

            converted_subsequence = [word_vocabulary.get(
                    "<NUM>" if is_number(w) else w.lower(),
                    word_vocabulary[data.UNK])
                for w in subsequence]

            if show_unk:
                subsequence = [reverse_word_vocabulary[w] for w in converted_subsequence]

            y = predict(self.to_array(converted_subsequence))
            
            finalstring+=subsequence[0].title()

            last_eos_idx = 0
            punctuations = []
            for y_t in y:

                p_i = np.argmax(y_t.flatten())
                punctuation = reverse_punctuation_vocabulary[p_i]

                punctuations.append(punctuation)

                if punctuation in data.EOS_TOKENS:
                    last_eos_idx = len(punctuations) # we intentionally want the index of next element

            if subsequence[-1] == data.END:
                step = len(subsequence) - 1
            elif last_eos_idx != 0:
                step = last_eos_idx
            else:
                step = len(subsequence) - 1

            for j in range(step):
                current_punctuation = punctuations[j]
                finalstring += self.convert_punctuation_to_readable(current_punctuation)

                if j < step - 1:
                    if current_punctuation in data.EOS_TOKENS:
                        finalstring+=subsequence[1+j].title()

                    else:
                        finalstring+=subsequence[1+j]


            if subsequence[-1] == data.END:
                # break
                return finalstring

            i += step

            


    def restore(self,modelpath, isshowunnk, text):

        if len(modelpath) > 1:
            model_file = modelpath
        else:
            print("Model file path argument missing")

        show_unk = False
        if len(isshowunnk):
            show_unk = bool(int(isshowunnk))

        x = T.imatrix('x')

        print("Loading model parameters...")
        net, _ = models.load(model_file, 1, x)

        print("Building model...")
        predict = theano.function(inputs=[x], outputs=net.y)
        word_vocabulary = net.x_vocabulary
        punctuation_vocabulary = net.y_vocabulary
        reverse_word_vocabulary = {v:k for k,v in net.x_vocabulary.items()}
        reverse_punctuation_vocabulary = {v:k for k,v in net.y_vocabulary.items()}

        human_readable_punctuation_vocabulary = [p[0] for p in punctuation_vocabulary if p != data.SPACE]
        tokenizer = word_tokenize
        untokenizer = lambda text: text.replace(" '", "'").replace(" n't", "n't").replace("can not", "cannot")

        words = [w for w in untokenizer(' '.join(tokenizer(text))).split()
                 if w not in punctuation_vocabulary and w not in human_readable_punctuation_vocabulary]

        finalstring = self.punctuate(predict, word_vocabulary, punctuation_vocabulary, reverse_punctuation_vocabulary, reverse_word_vocabulary, words, show_unk)

        return finalstring

def main():
    text = "good afternoon share that stance and insurance i just touching base with you i wanted to see if you had a chance to look at that email that i had sent over with regard to me technologies i'm posting number. oh gosh i don't even it. anyway sorry are seven zero zero five eight zero in regard to the data breach in the cyber information that one of his clients is requesting that he has coverage for a so if you could just give me a bus back let me know your thoughts i'm making the assumption that it's going to go beyond. i'm limits and coverage that and indie can provide for him but i just need to confirm that with you and also confirmed that he is classed properly on his policy can be called you have the moment a seven eight one eight three three two zero zero thank you bye"
    pun = PunctuateRestore()
    finalstring = pun.restore("Demo-Europarl-EN.pcl","0",text)
    print(finalstring)    

if __name__ == "__main__":
    main()
    
