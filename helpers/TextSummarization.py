# imports
from nltk.tokenize import word_tokenize, sent_tokenize
import torch
from pytorch_pretrained_bert import BertTokenizer, BertModel
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin_min
import numpy as np
# import language_check
import torch
import math
import json
import os
from fpdf import FPDF
from transformers import T5Tokenizer, T5ForConditionalGeneration, T5Config


def bertSent_embeding(sentences):

    # Add sentence head and tail as BERT requested
    marked_sent = ["[CLS] " + item + " [SEP]" for item in sentences]

    # USE Bert tokenizization
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    tokenized_sent = [tokenizer.tokenize(item) for item in marked_sent]

    # index to BERT vocabulary
    indexed_tokens = [tokenizer.convert_tokens_to_ids(
        item) for item in tokenized_sent]
    tokens_tensor = [torch.tensor([item]) for item in indexed_tokens]

    # add segment id as BERT requested
    segments_ids = [[1] * len(item) for ind, item in enumerate(tokenized_sent)]
    segments_tensors = [torch.tensor([item]) for item in segments_ids]

    # load BERT base model and set to evaluation mode
    bert_model = BertModel.from_pretrained('bert-base-uncased')
    bert_model.eval()

    # Output 12 layers of latent vector
    assert len(tokens_tensor) == len(segments_tensors)
    encoded_layers_list = []
    for i in range(len(tokens_tensor)):
        with torch.no_grad():
            encoded_layers, _ = bert_model(
                tokens_tensor[i], segments_tensors[i])
        encoded_layers_list.append(encoded_layers)

    # Use only the last layer vetcor, other choice available
    token_vecs_list = [layers[11][0] for layers in encoded_layers_list]

    # Pooling word vector to sentence vector, use mean pooling, other choice available
    sentence_embedding_list = [torch.mean(
        vec, dim=0).numpy() for vec in token_vecs_list]

    return sentence_embedding_list


def kmeans_sumIndex(sentence_embedding_list):

    n_clusters = np.ceil(len(sentence_embedding_list)**0.5)
    kmeans = KMeans(n_clusters=int(n_clusters))
    kmeans = kmeans.fit(sentence_embedding_list)

    sum_index, _ = pairwise_distances_argmin_min(
        kmeans.cluster_centers_, sentence_embedding_list, metric='euclidean')

    sum_index = sorted(sum_index)

    return sum_index


def bertSummarize(text):

    sentences = sent_tokenize(text)
    # print(sentences)
    sentence_embedding_list = bertSent_embeding(sentences)
    # print(sentence_embedding_list)
    # print("hi")
    sum_index = kmeans_sumIndex(sentence_embedding_list)
    summary = ' '.join([sentences[ind] for ind in sum_index])

    return summary


def extractive_summary(text):
    a = bertSummarize(text)
    # # tool = language_check.LanguageTool('en-US')
    # # matches1 = tool.check(a)
    # return language_check.correct(a, matches1)
    return a


def abstractive_summary(text, minlength=100, maxlength=250) -> str:
    model = T5ForConditionalGeneration.from_pretrained('t5-small')
    tokenizer = T5Tokenizer.from_pretrained('t5-small')
    device = torch.device('cpu')
    preprocess_text = text.strip().replace("\n", "")
    t5_prepared_Text = "summarize: "+preprocess_text
    tokenized_text = tokenizer.encode(
        t5_prepared_Text, return_tensors="pt").to(device)
    # summmarize
    summary_ids = model.generate(tokenized_text, num_beams=3, no_repeat_ngram_size=1, min_length=min(minlength, math.floor(
        0.2*len(preprocess_text))), max_length=min(maxlength, math.floor(0.5*len(preprocess_text))), early_stopping=True)
    #tool = language_check.LanguageTool('en-US')
    output = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    #matches2 = tool.check(output)
    # return language_check.correct(output, matches2)
    return output


def generate_pdf(extractive, abstractive):
    file1 = open("myfile1.txt", "w+", encoding="latin-1")
    l = []
    b = ""
    j = 0
    for i in range(len(extractive)):
        if j == 130:
            if(extractive[i] == " "):
                b = b+extractive[i]
                l.append(b)
                b = ""
            else:
                l.append(b)
                l.append("-")
                b = extractive[i]
            l.append("\n")
            j = 1
        else:
            b = b+extractive[i]
        j = j+1
    l.append(b)
    file1.writelines(l)
    file1.close()
    file2 = open("myfile2.txt", "w+", encoding="latin-1")
    l = []
    b = ""
    j = 0
    for i in range(len(abstractive)):
        if j == 130:
            if(abstractive[i] == " "):
                b = b+abstractive[i]
                l.append(b)
                b = ""
            else:
                l.append(b)
                l.append("-")
                b = abstractive[i]
            l.append("\n")
            j = 1
        else:
            b = b+abstractive[i]
        j = j+1
    l.append(b)
    file2.writelines(l)
    file2.close()
    # Python program to convert
    # text file to pdf file

    from fpdf import FPDF
    # Python program to convert
    # text file to pdf file
    # save FPDF() class into
    # a variable pdf
    pdf = FPDF()
    # Add a page
    pdf.add_page()
    # set style and size of font
    # that you want in the pdf
    f = open("myfile1.txt", "r", encoding="latin-1")
    pdf.set_font("Arial", "U", size=20)
    # open the text file in read mode
    print(os.getcwd())
    pdf.image('./helpers/collaboration-icon.jpg', 10, 8, 33)
    pdf.image('./helpers/focus.jpg', 170, 8, 35)
    pdf.set_text_color(255, 0, 0)
    pdf.set_font('Arial', 'B', 30)
    pdf.cell(190, 10, txt="You Summarizer", ln=1, align='C')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'I', 17)
    pdf.cell(190, 10, txt="AI Powered Summarisation Tool", ln=1, align='C')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", size=10)
    pdf.cell(190, 15, txt="_______________________________________________________________________________________________________________", ln=3, align='C')

    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, txt="Thank you for choosing You Summarizer. You have been provided with a short summary of the meet as well as a more detailed", ln=5, align='')
    pdf.cell(190, 8, txt="Notes of the Video. Do provide us with your valuable suggestions regarding Smart Meet.  ", ln=5, align='C')

    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, txt=" ", ln=5, align='')

    pdf.set_font("Times", "B", size=15)
    pdf.cell(190, 10, txt="Short Summary of Video ", ln=5, align='C')

    # insert the texts in pdf
    pdf.set_font("Times", size=10)
    for x in f:
        pdf.cell(190, 10, txt=x, ln=7, align='J')
    # save the pdf with name .pdf

    pdf.set_font("Times", "B", size=10)
    pdf.cell(190, 10, txt="*   END   *", ln=9, align='C')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", size=10)
    pdf.cell(190, 10, txt="_____________________________________", ln=3, align='C')

    pdf.set_font("Arial", "B", size=15)

    #     Second page

    pdf.add_page()
    pdf.image('./helpers/collaboration-icon.jpg', 10, 8, 33)
    pdf.image('./helpers/focus.jpg', 170, 8, 35)
    pdf.set_text_color(255, 0, 0)
    pdf.set_font('Arial', 'B', 30)
    pdf.cell(190, 10, txt="You Summarizer", ln=1, align='C')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'I', 17)
    pdf.cell(190, 10, txt="AI Powered Summarisation Tool", ln=1, align='C')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", size=10)
    pdf.cell(190, 10, txt="_______________________________________________________________________________________________________________", ln=3, align='C')

    pdf.set_font("Times", "B", size=15)
    pdf.cell(190, 10, txt="Detailed Summary of the Video ", ln=5, align='C')

    pdf.set_font("Times", size=10)
    f = open("myfile2.txt", "r", encoding="latin-1")
    for x in f:
        pdf.cell(190, 10, txt=x, ln=13, align='J')

    pdf.set_font("Times", "B", size=10)
    pdf.cell(190, 10, txt="*   END   *", ln=9, align='C')

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Times", size=10)
    pdf.cell(190, 10, txt="_____________________________________", ln=3, align='C')

    pdf.output("./static/notes.pdf")

#text = """A computer is a machine that can be programmed to carry out sequences of arithmetic or logical operations automatically. Modern computers can perform generic sets of operations known as programs. These programs enable computers to perform a wide range of tasks. A computer system is a "complete" computer that includes the hardware, operating system (main software), and peripheral equipment needed and used for "full" operation. This term may also refer to a group of computers that are linked and function together, such as a computer network or computer cluster."""
# print(abstractive_summary(text))
