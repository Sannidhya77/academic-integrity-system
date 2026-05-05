from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast
import difflib


def text_similarity(a, b):

    docs = [a, b]

    vectorizer = TfidfVectorizer(stop_words="english")

    tfidf = vectorizer.fit_transform(docs)

    score = cosine_similarity(tfidf[0:1], tfidf[1:2])

    return float(score[0][0])


def code_similarity(code1, code2):

    try:

        tree1 = ast.parse(code1)
        tree2 = ast.parse(code2)

        dump1 = ast.dump(tree1)
        dump2 = ast.dump(tree2)

        return text_similarity(dump1, dump2)

    except:

        return text_similarity(code1, code2)


def highlight_matches(text1, text2):

    seq = difflib.SequenceMatcher(None, text1.split(), text2.split())

    highlighted1 = ""
    highlighted2 = ""

    for opcode, a0, a1, b0, b1 in seq.get_opcodes():

        if opcode == "equal":

            part1 = " ".join(text1.split()[a0:a1])
            part2 = " ".join(text2.split()[b0:b1])

            if len(part1.strip()) > 20:

                highlighted1 += f"<span style='background:yellow'>{part1}</span>"
                highlighted2 += f"<span style='background:yellow'>{part2}</span>"

            else:

                highlighted1 += part1
                highlighted2 += part2

        else:

            highlighted1 += text1[a0:a1]
            highlighted2 += text2[b0:b1]

    return highlighted1, highlighted2