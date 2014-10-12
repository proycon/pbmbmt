# PBMBMT: PHRASE-BASED MEMORY-BASED MACHINE TRANSLATOR
# by Maarten van Gompel (proycon)
#   proycon AT anaproy DOT NL
#   http://proylt.anaproy.nl
# Licensed under the GNU Public License v3

#MAYBE TODO: Migrate to pynlpl?
import random

def validate_alignment(alignment, begin,length,tbegin,tlength):
    """Check if the found phrase-alignment does not conflict with the word-alignment"""
    for i in xrange(begin,length):
        if alignment[i] != None:
            if (alignment[i] < tbegin) or (alignment[i] >= tbegin+tlength):
                return False #alignment goes out of bounds, discard
    return True #alignment is valid



def get_train_phrases_phrasetable(sourcewords, targetwords, alignment, phrasetable, strict=True, MAXPHRASELENGTH=6, MINPHRASELENGTH=2,bestonly=True):
    """Extract phrases for training using a Phrase Table (P) and  Word Alignment (A)"""

    sourcelength = len(sourcewords)
    targetlength = len(targetwords)
    #Generate possible phrases and see if anything matches with the phrasetable
    for begin in xrange(0,sourcelength):
       for length in xrange(MINPHRASELENGTH,sourcelength - begin + 1):
        if length > MAXPHRASELENGTH:
            break
        phrase = sourcewords[begin:begin+length]
        phrasestring = " ".join(phrase)

        aligned_phrases = [] #list of extracted aligned phrases, list of (tbegin,tlength,score,null_aligments) tuples:
        # tbegin: index in targetwords where aligned-phrase begins
        # tlength: the length of the target phrase (in words in targetwords)
        # score: P(source|target)
        # null_alignments: how many words in the target phrase are not aligned with a source word?

        if phrasestring in phrasetable:
          #we have a match, now check if the targetphrase exists as well
          #for translation, Pst, Pts, null_alignments in phrasetable[phrasestring]:
          for translation, scores in phrasetable[phrasestring]:
            Pst = scores[0]
            Pts = scores[2]
            null_alignments = 0

            translation = translation.split(" ")
            tlength = len(translation)

            for tbegin in xrange(0,targetlength):
              if targetwords[tbegin:tbegin+tlength] == translation:
                #found!
                if not strict:
                    aligned_phrases.append( (tbegin,tlength,Pst,Pts,null_alignments) )
                elif validate_alignment(alignment, begin,length,tbegin,tlength): #strict mode, validate
                    aligned_phrases.append( (tbegin,tlength,Pst,Pts,null_alignments) )

        if aligned_phrases:
            if len(aligned_phrases) > 1:

                #ok, we have a problem. We have multiple aligned phrases for the same input sample. Outputting the same features with different classes would not be very sensible, so we try to select the 'best' phrase:
                if bestonly:
                    best_score = max([  x[3] for x in aligned_phrases ]) #Uses Pts
                    aligned_phrases = [ x for x in aligned_phrases if x[3] == best_score ]

                    if len(aligned_phrases) > 1:
                        least_null_alignments = min([ x[4] for x in aligned_phrases ])
                        aligned_phrases = [ x for x in aligned_phrases if x[4] == least_null_alignments ]

                    tbegin, tlength, Pst, Pts, null_alignments = aligned_phrases[0]
                    yield begin,length,tbegin,tlength, Pst, Pts
                else:
                    for tbegin, tlength, Pst, Pts, null_alignments in aligned_phrases:
                        yield begin,length,tbegin,tlength, Pst, Pts

                #(if we still have multiple options we now just grab the first one)
            else:
                tbegin, tlength, Pst, Pts, null_alignments = aligned_phrases[0]
                yield begin,length,tbegin,tlength, Pst, Pts







def get_train_phrases_phraselist(sourcewords,targetwords,alignment,phraselist_source, phraselist_target=None, MAXPHRASELENGTH = 6):
    """Extract phrases for training using a Phraselist"""

    sourcelength = len(sourcewords)
    targetlength = len(targetwords)
    #Generate possible phrases and see if anything matches with the phrasetable
    for begin in xrange(0,sourcelength - 1):
       for length in xrange(2,sourcelength - begin):
        if length > MAXPHRASELENGTH:
            break
        phrase = sourcewords[begin:begin+length]
        phrasestring = " ".join(phrase)

        if phrasestring in phraselist_source:
            phrase_alignments = [] #will hold a of alignments for the phrase
            #can we estimate an aligned phrase based on the word-alignment?
            for i in xrange(begin,begin+length):
                if alignment[i] != None:
                    phrase_alignments.append(alignment[i])
                #else:
                #    #we encountered a None alignment in the source phrase, break off
                #    phrase_alignments = []
                #    break
            #print "ALIGNMENT DEBUG: ", phrase_alignments
            if phrase_alignments: #do we have a list of alignments?
                tbegin = min(phrase_alignments)
                tend = max(phrase_alignments)
                tlength = (tend - tbegin) + 1
                #check if the alignments constitute a consecutive range without missing elements
                for i in xrange(tbegin, tend):
                    if not (i in phrase_alignments):
                        #no, we miss a part
                        phrase_alignments =  []
                        break
                if phrase_alignments:
                    aligned_phrase = targetwords[tbegin:tbegin+tlength]
                    aligned_phrase_string = " ".join(aligned_phrase)
                    accept = False
                    if not phraselist_target:
                        #all is okay, accept the aligned phrase
                        accept = True
                        #print >> sys.stderr, "ALIGNMENT FOUND: ",phrasestring, " -> ", aligned_phrase_string,"\t",phrase_alignments
                    else:
                        #accept the aligned phrase if it occurs in the target phraselist
                        if phraselist_target:
                            if aligned_phrase_string in phraselist_target:
                                accept = True
                    if accept:
                        yield begin,length,tbegin,tlength


def align_chunks(sourcewords, targetwords, wordalignment,source_chunks,target_chunks):

    #create 2D alignment matrix
    m = [ [ 0 for y in xrange(0,len(target_chunks)) ] for x in xrange(0,len(source_chunks)) ]

    #for each source-chunk, find the best target chunk, the one that is aligned with most words in the sourcechunk
    for i, (begin,length) in enumerate(source_chunks):
        #find alignment for source_chunk
        for j, (tbegin, tlength) in enumerate(target_chunks):
            alignscore = 0
            for k in xrange(begin,begin+length):
                if wordalignment[k]:
                    if (wordalignment[k] >= tbegin and wordalignment[k] < tbegin+tlength):
                        alignscore += 1
            alignscore = alignscore / float(length)
            m[i][j] = alignscore
            #print "S2T DEBUG: ", sourcewords[begin:begin+length], " -> ", targetwords[tbegin:tbegin+tlength], "\t",alignscore


    #compute reverse of word alignments
    rev_wordalignment = []
    for j in xrange(0,len(targetwords)):
        sourcealigned = None
        for i, aligned in enumerate(wordalignment):
            if aligned == j:
                sourcealigned = i
        rev_wordalignment.append(sourcealigned)


    #for each target-chunk, find the best source chunk, the one that is aligned with most words in the target
    for j, (tbegin,tlength) in enumerate(target_chunks):
        #find alignment for source_chunk
        for i, (begin, length) in enumerate(source_chunks):
            if m[i][j] > 0: #no need to bother if source doesn't align
                alignscore = 0
                for k in xrange(tbegin,tbegin+tlength):
                    if rev_wordalignment[k]:
                        if (rev_wordalignment[k] >= begin and rev_wordalignment[k] < begin+length):
                            alignscore += 1
                alignscore = alignscore / float(tlength)
                m[i][j] *= alignscore     #compute intersection
                #print "T2S DEBUG: ", sourcewords[begin:begin+length], " -> ", targetwords[tbegin:tbegin+tlength], "\t",alignscore

    #now grab the best alignments
    chunk_alignments = []
    for i, (begin,length) in enumerate(source_chunks):
        bestalign = bestscore = 0
        for j, (tbegin, tlength) in enumerate(target_chunks):
            if m[i][j] > bestscore:
                bestscore = m[i][j]
                bestalign = j

        if bestscore > 0:
            chunk_alignments.append(bestalign)
        else:
            chunk_alignments.append(None)

    return chunk_alignments


def get_train_phrases_markerbased(sourcewords, targetwords, alignment, markerlist_source, markerlist_target, MAXPHRASELENGTH=9):
    """Extract phrases as marker-based chunks"""
    sourcelength = len(sourcewords)
    targetlength = len(targetwords)

    source_chunks = [ (begin, length) for begin,length in get_chunks(sourcewords,markerlist_source) ]
    target_chunks = [ (tbegin, tlength) for tbegin,tlength in get_chunks(targetwords,markerlist_target) ]

    chunk_alignment = align_chunks(sourcewords,targetwords,alignment,source_chunks, target_chunks)

    for i,(begin,length) in enumerate(source_chunks):
        if chunk_alignment[i] and length <= MAXPHRASELENGTH:
            tbegin,tlength = target_chunks[chunk_alignment[i]]
            #print "DEBUG: ", sourcewords[begin:begin+length], " --> ", targetwords[tbegin:tbegin+tlength] #DEBUG
            yield begin,length,tbegin,tlength


    """#for i,(begin,length) in enumerate(source_chunks):
    for begin,length in get_chunks(sourcewords,markerlist_source):
        #find alignment for source_chunk
        for tbegin, tlength in target_chunks:
            aligns = True
            nullalignments = 0
            for j in xrange(begin,begin+length):
                if alignment[j]:
                    if not (alignment[j] >= tbegin and alignment[j] < tbegin+tlength):
                        aligns = False
                        break
                else:
                    nullalignments += 1
            aligns = (aligns and nullalignments < length)
            if aligns:
                #print "DEBUG: ", sourcewords[begin:begin+length], " --> ", targetwords[tbegin:tbegin+tlength] #DEBUG
                yield begin,length,tbegin,tlength
    """

def get_test_phrases_markerbased(words, markerlist_source, MAXPHRASELENGTH=9):
    for begin,length in get_chunks(words,markerlist_source):
        if length <= MAXPHRASELENGTH:
            yield begin, length



def get_test_phrases_phrasetable(words, phrasetable,  MAXPHRASELENGTH=6, MINPHRASELENGTH=2):
    #Generate possible phrases and see if anything matches with the phrasetable
    words_len = len(words)
    for begin in xrange(0,words_len):
       for length in xrange(MINPHRASELENGTH,words_len - begin + 1):
        if length > MAXPHRASELENGTH:
            break

        phrase = words[begin:begin+length]
        phrasestring = " ".join(phrase)

        if phrasestring in phrasetable:
            bestscore = 0
            for target,Pst,Pts,null_alignments in phrasetable[phrasestring]:
                if Pts > bestscore:
                    bestscore = Pts
                    final_Pst = Pst
                    final_Pts = Pts
            yield begin, length, final_Pst, final_Pts

def get_baseline_phrasetable(words, phrasetable,  MAXPHRASELENGTH=6, MINPHRASELENGTH=2):
    #Tie phrasetable results directly to test data, without classifier
    words_len = len(words)
    for begin in xrange(0,words_len):
       for length in xrange(MINPHRASELENGTH,words_len - begin + 1):
        if length > MAXPHRASELENGTH:
            break

        phrase = words[begin:begin+length]
        phrasestring = " ".join(phrase)

        if phrasestring in phrasetable:
            #for target,Pst,Pts,null_alignments in phrasetable[phrasestring]:
            yield begin, length,phrasetable[phrasestring]

def get_test_phrases_phraselist(words, phraselist,  MAXPHRASELENGTH=6, MINPHRASELENGTH=2):
    #Generate possible phrases and see if anything matches with the phrasetable
    words_len = len(words)
    for begin in xrange(0,words_len - 1):
       for length in xrange(MINPHRASELENGTH,words_len - begin):
        if length > MAXPHRASELENGTH:
            break

        phrase = words[begin:begin+length]
        phrasestring = " ".join(phrase)

        if phraselist.exists(phrasestring):
            yield begin, length



def get_left_context(words, index, size):
    context = []
    for i in xrange(index - size,index):
        if i < 0:
            context.append("__")
        else:
            context.append(words[i])
    return context

def get_right_context(words, nextindex, size):
    context = []
    length = len(words)
    for i in xrange(nextindex,nextindex+size):
        if i > length - 1:
            context.append("__")
        else:
            context.append(words[i])
    return context

def validate_pos_tags(tags):
    newtags = []
    for tag in tags:
        if tag:
            newtags.append(":POS:" + tag[:tag.find("(")])
        else:
            newtags.append(":POS:" + "%032x" % random.getrandbits(128)) #no pos tag found, add a random 128 bit number
    return newtags

def validate_lemma_tags(tags):
    newtags = []
    for tag in tags:
        if tag:
            newtags.append(":LEMMA:" + tag)
        else:
            newtags.append(":LEMMA:" + "%032x" % random.getrandbits(128)) #no lemma found, add a random 128 bit number
    return newtags

def make_train_ngram(sourcewords,targetwords,begin,length,tbegin,tlength, nfeatleft = 1, nfeatright = 1,nclassleft=1, nclassright=1,return_nfocus=False, phrase_singlefeature = False, fixedfeatures=False, npos=None, nlemma=None,taggeddata=None,score=0, usealignprob=False, alignprobfeature=False):
    #Note, taggeddata is result from Taggerdata.align()

    pos_focus = ""
    lemma_focus = ""
    if taggeddata and npos != None:
        pos_focus = validate_pos_tags([ x[2] for x in taggeddata[begin:begin+length] ])
    if taggeddata and nlemma != None:
        lemma_focus = validate_lemma_tags([ x[1] for x in taggeddata[begin:begin+length] ])

    features = ""

    features_leftcontext = " ".join(get_left_context(sourcewords,begin,nfeatleft))
    if phrase_singlefeature:
        features_focus = "_".join(sourcewords[begin:begin+length])
        if pos_focus:
            pos_focus = "_".join(pos_focus)
        if lemma_focus:
            lemma_focus = "_".join(lemma_focus)
    elif fixedfeatures > 0:
        features = "n="+str(length) + " " #first feature is length!
        if length > fixedfeatures:
            raise Exception("Not enough fixed features to span phrase of length %d!" % length)
        features_focus = " ".join(sourcewords[begin:begin+length] + ["^"] * (fixedfeatures - length))
        if pos_focus:
            pos_focus = " ".join(pos_focus + ["^"] * (fixedfeatures - length))
        if lemma_focus:
            lemma_focus = " ".join(lemma_focus + ["^"] * (fixedfeatures - length))
    else:
        features_focus = " ".join(sourcewords[begin:begin+length])
        if pos_focus:
            pos_focus = " ".join(pos_focus)
        if lemma_focus:
            lemma_focus = " ".join(lemma_focus)
    features_rightcontext = " ".join(get_right_context(sourcewords,begin+length,nfeatright))

    if alignprobfeature:
        features += str(score) + " "
    if features_leftcontext:
        features += features_leftcontext + " "
    features += features_focus + " "
    if features_rightcontext:
        features += features_rightcontext + " "

    if taggeddata and npos != None:
        if npos > 0: features += " ".join(validate_pos_tags(get_left_context([ x[2] for x in taggeddata],begin,npos))).encode('utf-8') + ' '
        features += pos_focus.encode('utf-8') + ' '
        if npos > 0: features += " ".join(validate_pos_tags(get_right_context([ x[2] for x in taggeddata],begin+ length,npos))).encode('utf-8') + ' '
    if taggeddata and nlemma != None:
        if nlemma > 0: features += " ".join(validate_lemma_tags(get_left_context([ x[1] for x in taggeddata],begin,npos))).encode('utf-8') + ' '
        features += lemma_focus.encode('utf-8') + ' '
        if nlemma > 0: features += " ".join(validate_lemma_tags(get_right_context([ x[1] for x in taggeddata],begin+ length,npos))).encode('utf-8') + ' '

    class_leftcontext = "^".join(get_left_context(targetwords,tbegin,nclassleft))
    class_focus = "_".join(targetwords[tbegin:tbegin+tlength])
    class_rightcontext = "^".join(get_right_context(targetwords,tbegin+tlength,nclassright))

    out = features
    if class_leftcontext:
        out += class_leftcontext + "^"
    out += class_focus
    if class_rightcontext:
        out += "^" + class_rightcontext

    if usealignprob:
        out += " " + str(score)

    #return "%s %s %s %s^%s^%s" % (features_leftcontext, features_focus, features_rightcontext, class_leftcontext, class_focus, class_rightcontext)
    if return_nfocus:
        return out, len(sourcewords[begin:begin+length])
    else:
        return out


def make_test_ngram(words,begin,length, nleft=1,nright=1, return_nfocus=False, phrase_singlefeature = False,fixedfeatures = False, npos=None, nlemma=None,taggeddata=None,  score=0, usealignprob=False, alignprobfeature=False):
        instance = ""

        pos_focus = ""
        lemma_focus = ""
        if taggeddata and npos != None:
            pos_focus = validate_pos_tags([ x[2] for x in taggeddata[begin:begin+length] ])
        if taggeddata and nlemma != None:
            lemma_focus = validate_lemma_tags([ x[1] for x in taggeddata[begin:begin+length] ])


        features_leftcontext = " ".join(get_left_context(words,begin,nleft))
        if phrase_singlefeature:
            features_focus = "_".join(words[begin:begin+length])
            if pos_focus:
                pos_focus = "_".join(pos_focus)
            if lemma_focus:
                lemma_focus = "_".join(lemma_focus)
        elif fixedfeatures > 0:
            instance = "n="+str(length) + " " #first feature is length!
            if length > fixedfeatures:
                raise Exception("Not enough fixed features to span phrase of length %d!" % length)
            features_focus = " ".join(words[begin:begin+length] + ["^"] * (fixedfeatures - length))
            if pos_focus:
                pos_focus = " ".join(pos_focus + ["^"] * (fixedfeatures - length))
            if lemma_focus:
                lemma_focus = " ".join(lemma_focus + ["^"] * (fixedfeatures - length))
        else:
            features_focus = " ".join(words[begin:begin+length])
            if pos_focus:
                pos_focus = " ".join(pos_focus)
            if lemma_focus:
                lemma_focus = " ".join(lemma_focus)
        features_rightcontext = " ".join(get_right_context(words,begin+length,nright))

        if alignprobfeature:
            instance += str(score) + " "
        if features_leftcontext:
            instance += features_leftcontext + " "
        instance += features_focus + " "
        if features_rightcontext:
            instance += features_rightcontext + " "

        if taggeddata and npos != None:
            if npos > 0: instance += " ".join(validate_pos_tags(get_left_context([ x[2] for x in taggeddata],begin,npos))).encode('utf-8') + ' '
            instance += pos_focus.encode('utf-8') + ' '
            if npos > 0: instance += " ".join(validate_pos_tags(get_right_context([ x[2] for x in taggeddata],begin+ length,npos))).encode('utf-8') + ' '
        if taggeddata and nlemma != None:
            if nlemma > 0: instance += " ".join(validate_lemma_tags(get_left_context([ x[1] for x in taggeddata],begin,npos))).encode('utf-8') + ' '
            instance += lemma_focus.encode('utf-8') + ' '
            if nlemma > 0: instance += " ".join(validate_lemma_tags(get_right_context([ x[1] for x in taggeddata],begin+ length,npos))).encode('utf-8') + ' '


        instance += "?"

        if usealignprob:
            instance += " 0" #dummy scores are needed when training file contains scores

        #return "%s %s %s ?" % (features_leftcontext, features_focus, features_rightcontext)
        if return_nfocus:
            return instance, len(words[begin:begin+length])
        else:
            return instance




def make_baseline_ngram(words,translations,begin,length, nleft=1,nright=1, return_nfocus=False, phrase_singlefeature = False,fixedfeatures = False, npos=None, nlemma=None,taggeddata=None):
        instance = ""

        pos_focus = ""
        lemma_focus = ""
        if taggeddata and npos != None:
            pos_focus = validate_pos_tags([ x[2] for x in taggeddata[begin:begin+length] ])
        if taggeddata and nlemma != None:
            lemma_focus = validate_lemma_tags([ x[1] for x in taggeddata[begin:begin+length] ])


        features_leftcontext = " ".join(get_left_context(words,begin,nleft))
        if phrase_singlefeature:
            features_focus = "_".join(words[begin:begin+length])
            if pos_focus:
                pos_focus = "_".join(pos_focus)
            if lemma_focus:
                lemma_focus = "_".join(lemma_focus)
        elif fixedfeatures > 0:
            instance = "n="+str(length) + " " #first feature is length!
            if length > fixedfeatures:
                raise Exception("Not enough fixed features to span phrase of length %d!" % length)
            features_focus = " ".join(words[begin:begin+length] + ["^"] * (fixedfeatures - length))
            if pos_focus:
                pos_focus = " ".join(pos_focus + ["^"] * (fixedfeatures - length))
            if lemma_focus:
                lemma_focus = " ".join(lemma_focus + ["^"] * (fixedfeatures - length))
        else:
            features_focus = " ".join(words[begin:begin+length])
            if pos_focus:
                pos_focus = " ".join(pos_focus)
            if lemma_focus:
                lemma_focus = " ".join(lemma_focus)
        features_rightcontext = " ".join(get_right_context(words,begin+length,nright))


        if features_leftcontext:
            instance += features_leftcontext + " "
        instance += features_focus + " "
        if features_rightcontext:
            instance += features_rightcontext + " "

        if taggeddata and npos != None:
            if npos > 0: instance += " ".join(validate_pos_tags(get_left_context([ x[2] for x in taggeddata],begin,npos))).encode('utf-8') + ' '
            instance += pos_focus.encode('utf-8') + ' '
            if npos > 0: instance += " ".join(validate_pos_tags(get_right_context([ x[2] for x in taggeddata],begin+ length,npos))).encode('utf-8') + ' '
        if taggeddata and nlemma != None:
            if nlemma > 0: instance += " ".join(validate_lemma_tags(get_left_context([ x[1] for x in taggeddata],begin,npos))).encode('utf-8') + ' '
            instance += lemma_focus.encode('utf-8') + ' '
            if nlemma > 0: instance += " ".join(validate_lemma_tags(get_right_context([ x[1] for x in taggeddata],begin+ length,npos))).encode('utf-8') + ' '


        translations = sorted(translations, key=lambda x: x[2], reverse=True) #uses P(t|s) to sort

        classes = "? " + translations[0][0].replace(' ','_') + ' { ' #best class
        factor = 1/float(translations[-1][2]) #let's adhere exactly to the timbl +vdb standard where all scores are >=1.0 (uses P(t|s) )
        #add distribution
        for i, (target, Pst,Pts, null_alignments) in enumerate(translations):
            if i > 0:
                classes += ', '
            classes += target.replace(' ','_') + ' ' + str(int(round(Pts*factor))) + '.00000'
        classes += ' }'

        instance += classes

        if return_nfocus:
            return instance, len(words[begin:begin+length])
        else:
            return instance



def get_ngrams(words,n=3,eos=True):
    if eos:    #include ngrams with begin/end-of-sentence markers?
        begin = 0
        end = len(words) + (n - 1) #non-inclusive
    else:
        begin = n-1
        end = len(words)

    ngrams = []
    for i in xrange(begin,end):
        ngram = []
        for j in xrange(i-(n-1),i+1):
            if j < 0 or j >= len(words):
                ngram.append("__")
            else:
                ngram.append(words[j])
        ngrams.append(ngram)
    return ngrams


def get_chunks(words,markerlist):
    last_was_marker = False
    begin = 0
    for i, word in enumerate(words):
        if word in markerlist:
            if not last_was_marker and i > begin:
                yield begin,i-begin
                begin = i
        last_was_marker = (word in markerlist)
    length = len(words) - begin
    yield begin,length #return last chunk
