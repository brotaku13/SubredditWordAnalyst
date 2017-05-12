import config
import praw
import os
import nltk
from nltk.collocations import *


PATH = 'C:\\Users\\brian\\Documents\\Programming\\Python\\python projects\\SubredditWordAnalyst'


def login():
    '''
    creates a reddit instance using confidential login information
    :return: a reddit instance r
    '''
    print('logging in...')
    r = praw.Reddit(client_id=config.client_id,
                    client_secret=config.client_secret,
                    user_agent=config.user_agent,
                    username=config.username,
                    password=config.password)
    print('logged in!')
    return r

def get_submissions(r, sub_list, lmt):
    '''
    Creates a file system for storing data. also goes through top {} of each subreddit listed and reads post ids
    for later analysis
    :param r: reddit instance
    :param sub_list: a list of subreddits defined by the user
    :param lmt: post limit, must manually set to None if limit is not wanted or needed, if None is specified then the bot gets around 1000 posts
    :return: void
    '''

    temp_list = []

    for subreddit in sub_list:
        print('accessing', subreddit)
        # checks if path exists and if it does not then creates a new path
        if not os.path.exists('{}/{}'.format(PATH, subreddit)):
            os.mkdir(subreddit)
            print('path did not exist')

        print('creating file...')

        outfile = open('{}/{}/{}.txt'.format(PATH, subreddit, subreddit + 'submissionid'), 'w')

        print('parsing submissions')
        for submission in r.subreddit(subreddit).hot(limit=lmt):  # must manually change to None if you don't want a limit
            outfile.write(submission.id)
            outfile.write('\n')
            temp_list.append(submission.id)
        outfile.close()

def get_words(r):
    '''
    iterates through submissionid.txt files, visits each submission and records all of the comments into a new file,
    stores this file under the same directory
    :param r: reddit instnace
    :return: void
    '''

    for dirName, subdirList, fileList in os.walk(PATH):
        print('Found directory: %s' % dirName)

        # getting each file
        for file in fileList:
            if file.endswith('.txt'):  # limiting to txt files
                openfile = open('{}/{}'.format(dirName, file), 'r')
                lines = openfile.read()
                submission_list = lines.split('\n')

                # split each file into a list of submission_IDs
                for submission_id in submission_list:
                    comments_file = open('{}/{}.txt'.format(dirName, submission_id), 'w')
                    try:
                        post = r.submission(id=submission_id)
                        print(post.title)

                        post.comments.replace_more(limit=None)  # removing replace more comments objects, i've ound that this step t
                                                             #takes the longest, especially if posts are larger than a few hundred comments
                        for comment in post.comments.list():  # accessing comments
                            try:
                                commentstring = comment.body.strip('!@#$%^&*().,?/\\{}[]:;"\'')
                                commentstring = commentstring.strip('\n')
                                comments_file.write(commentstring)
                            except UnicodeEncodeError:
                                pass
                                print('error found, passing')

                    except ValueError:
                        pass  # stops this loop from creating a new text file based on the \n at end of id file, messy i know


def analyze_words(common_words_dict):
    '''
    opens comments in submission.txt files and uses the NLTK package to analyze pairs of words
    :param common_words_dict: dictionary in format [subreddit][common pairs]
    :return: void
    '''

    # creating word analytics components
    bigram_measures = nltk.collocations.BigramAssocMeasures()
    trigram_measures = nltk.collocations.TrigramAssocMeasures()


    for dirName, subdirList, fileList in os.walk(PATH):
        print('Found directory: %s' % dirName)

        # getting each file
        bigram_list = []
        for file in fileList:
            if not file.endswith('id.txt') and file.endswith('.txt'):  # excludes posts with submission ids
                directory = dirName.split('\\')  # splitting directory for later use as dictionary
                with open('{}/{}'.format(dirName, file)) as readFile:
                    text = readFile.read()

                    # turn text into tokens for analysis
                    tokens = nltk.wordpunct_tokenize(text)
                    finder = BigramCollocationFinder.from_words(tokens)

                    # limit to words that are paired together 3 or more times
                    finder.apply_freq_filter(3)

                    # appending top 10 bigrams to list
                    bigram_list += (finder.nbest(bigram_measures.pmi, 10))


                    common_words_dict[directory[-1]] = bigram_list


def main():
    r = login()

    subreddit_list = []
    common_words_dict = {}

    ## obtains subreddits to parse (please spell correctly!
    while True:
        sub = input('enter a sub you would like to parse or -1 to quit')
        if sub == '-1':
            break
        subreddit_list.append(sub)

    get_submissions(r, subreddit_list, 5)
    get_words(r)
    analyze_words(common_words_dict)
    print(common_words_dict)


main()