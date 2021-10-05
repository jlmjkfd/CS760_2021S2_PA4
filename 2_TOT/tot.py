# Copyright 2015 Abhinav Maurya

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# import library
import copy
import fileinput
import random
import scipy.special
import math
import numpy as np
import scipy.stats
import pickle
from math import log

class TopicsOverTime:
    
    def GetPnasCorpusAndDictionary(self, documents_path, timestamps_path, stopwords_path):
        
        # initialise variables
        documents = []
        timestamps = []
        dictionary = set()
        stopwords = set()
        
        # read stopwords from stopwords file into a set of stopwords
        for line in fileinput.input(stopwords_path):
            stopwords.update(set(line.lower().strip().split()))
            
        # read words from documents file, tokenise each document into a list of words
        # append each word list to var `documents` to form a list of word lists
        # append each word list to var `dictionary` to form a uniuqe set of words
        for doc in fileinput.input(documents_path):
            words = [word for word in doc.lower().strip().split() if word not in stopwords]
            documents.append(words)
            dictionary.update(set(words))
        
        # recognise the earliest date as 0s, then count the dates after in seconds
        for timestamp in fileinput.input(timestamps_path):
            num_titles = int(timestamp.strip().split()[0])
            timestamp = float(timestamp.strip().split()[1])
            timestamps.extend([timestamp for title in range(num_titles)])
            
        # normalise each date, range from 0 to 1
        first_timestamp = timestamps[0]
        last_timestamp = timestamps[len(timestamps)-1]
        timestamps = [1.0*(t-first_timestamp)/(last_timestamp-first_timestamp) for t in timestamps]
        
        # convert var `dictionary` from set to list
        dictionary = list(dictionary)
        
        # if condition returns True, nothing happens
        # else, AssertionError is raised
        assert len(documents) == len(timestamps)
        
        # return output
        return documents, timestamps, dictionary

    def CalculateCounts(self, par):
        for d in range(par['D']):              # for each document
            for i in range(par['N'][d]):         # for each word in each document
                topic_di = par['z'][d][i]          # topic in doc d at word i
                word_di = par['w'][d][i]           # word ID in doc d at word i
                par['m'][d][topic_di] += 1         # distribution for topic,if word i in document d is assigned to this topic, +1 for this topic
                par['n'][topic_di][word_di] += 1   # distribution for word, if word i was assigned to this topic, +1 for specific word for this topic
                par['n_sum'][topic_di] += 1

    def InitializeParameters(self, documents, timestamps, dictionary):
        par = {}                        # dictionary of all parameters
        par['dataset'] = 'pnas'         # dataset name
        par['max_iterations'] = 5     # max number of iterations in gibbs sampling
        par['D'] = len(documents)       # number of documents
        par['T'] = 10                   # number of topics
        par['V'] = len(dictionary)      # number of unique words in dictionary
        par['N'] = [len(doc) for doc in documents]              # length of each document in documents
        par['alpha'] = [50.0/par['T'] for _ in range(par['T'])] # alpha = 50 / number of topics. len(par['alpha']) = num of topics
        par['beta'] = [0.1 for _ in range(par['V'])]            # beta = 0.1. len(par['beta']) = num of unique words in `dictionary`.
        par['beta_sum'] = sum(par['beta'])                      # this is for TopicsOverTimeGibbsSampling()
        par['psi'] = [[1 for _ in range(2)] for _ in range(par['T'])] # parameter of Beta distribution, this step is for initialisation
        par['betafunc_psi'] = [scipy.special.beta( par['psi'][t][0], par['psi'][t][1] ) for t in range(par['T'])] # Beta distribution of time specific to topic
        par['word_id'] = {dictionary[i]: i for i in range(len(dictionary))} # assign id for each word in dictionary
        par['word_token'] = dictionary # assign a set of unique words from `dictionary` to `word_token`
        par['z'] = [[random.randrange(0,par['T']) for _ in range(par['N'][d])] for d in range(par['D'])] # initialise - assign a random topic to each word in each document
        par['t'] = [[timestamps[d] for _ in range(par['N'][d])] for d in range(par['D'])] # initialise - assign a random timestamp to each word in each document
        par['w'] = [[par['word_id'][documents[d][i]] for i in range(par['N'][d])] for d in range(par['D'])] # assign word id to each word in each document
        par['m'] = [[0 for t in range(par['T'])] for d in range(par['D'])] # initialise theta: proportion of topics in each document)
        par['n'] = [[0 for v in range(par['V'])] for t in range(par['T'])] # initialise phi: word distribution for each topic
        par['n_sum'] = [0 for t in range(par['T'])] # ?
        np.set_printoptions(threshold=np.inf) # when the set has many elements, ensure that `...` is not printed
        np.seterr(divide='ignore', invalid='ignore') # ignore zero division error
        self.CalculateCounts(par)
        return par

    def GetTopicTimestamps(self, par):
        
        topic_timestamps = []
        
        # for each topic in all topics
        for topic in range(par['T']):
            
            current_topic_timestamps = []
            
            # if topic of word i in current doc d == current topic, then timestamp for word i in doc d remains the same
            # if not, then timestamp for word i in doc d is updated to 0
            current_topic_doc_timestamps = [[ (par['z'][d][i]==topic)*par['t'][d][i] for i in range(par['N'][d])] for d in range(par['D'])]
            
            # for each document in all documents
            for d in range(par['D']):
                # keep only timestamps that do not equal to 0. Use list(current_topic_doc_timestamps[d]) to see remaining values
                current_topic_doc_timestamps[d] = filter(lambda x: x!=0, current_topic_doc_timestamps[d])
            
            # create a list of non-zero timestamps for each topic
            for timestamps in current_topic_doc_timestamps:
                current_topic_timestamps.extend(timestamps)
            
            # if condition returns True, nothing happens
            # else, AssertionError is raised
            assert current_topic_timestamps != []
            
            # create a list of timestamps for all topics
            topic_timestamps.append(current_topic_timestamps)
            
        return topic_timestamps
        # topic timestamps exclude timestamps of the first few data rows (given their timestamps = 0)

    def GetMethodOfMomentsEstimatesForPsi(self, par):
        """
        estimate value of psi
        psi is distribution of words
        :param par: a dictionary for all parameters
        :return: value of psi
        """
        # get topic timestamps
        topic_timestamps = self.GetTopicTimestamps(par)
        # make a list of topic timestamps, each element is [1,1]
        psi = [[1 for _ in range(2)] for _ in range(len(topic_timestamps))]
        # for length of topic timestamps list
        for i in range(len(topic_timestamps)):
            # get current topic timestamp
            current_topic_timestamps = topic_timestamps[i]
            # get current topic timestamp mean
            timestamp_mean = np.mean(current_topic_timestamps)
            # get current topic timestamp variance
            timestamp_var = np.var(current_topic_timestamps)
            # set varaince to be non-zero
            if timestamp_var == 0:
                timestamp_var = 1e-6
            # beta distribution comes from formula from orginal paper
            common_factor = timestamp_mean*(1-timestamp_mean)/timestamp_var - 1
            # + 1 to make sure Beta parameters larger than 0 (Beta distribution needs parameters > 0)
            # Beta(a,b), a is psi[i][0], b is psi[i][1]
            psi[i][0] = 1 + timestamp_mean*common_factor
            psi[i][1] = 1 + (1-timestamp_mean)*common_factor
        return psi

    def ComputePosteriorEstimatesOfThetaAndPhi(self, par):
        """
        estimate value of theta and phi
            theta is porporiton of topics in each document
            phi is word distribution for each topic
        :param par: a dictionary for all parameters
        :return: value of psi
        """
        
        theta = copy.deepcopy(par['m'])
        phi = copy.deepcopy(par['n'])
        
        # for each document in document
        for d in range(par['D']):
            # for a document without any topic
            # make its distribution to be [1/num_topics for i in range(num_topics)]
            if sum(theta[d]) == 0:
                theta[d] = np.asarray([1.0/len(theta[d]) for _ in range(len(theta[d]))])
            # normalise each topic proportion, so the sum of all topic proportions is 1
            else:
                theta[d] = np.asarray(theta[d])
                theta[d] = 1.0*theta[d]/sum(theta[d])
        theta = np.asarray(theta)
        
        # for each topic in topics
        for t in range(par['T']):
            # for a topic without any words
            # make its distribution to be [1/num_words for i in range(num_words)]
            if sum(phi[t]) == 0:
                phi[t] = np.asarray([1.0/len(phi[t]) for _ in range(len(phi[t]))])
            # normalise each word's probability under a topic, so the sum of word probabilities equal to 1
            else:
                phi[t] = np.asarray(phi[t])
                phi[t] = 1.0*phi[t]/sum(phi[t])
        phi = np.asarray(phi)

        return theta, phi

    def TopicsOverTimeGibbsSampling(self, par):
        """
        TOT uses Gibbs sampling 
        :param par: a dictionary for all parameters
        :return: value of psi
        """
        for iteration in range(par['max_iterations']):
            # for each document in documents
            for d in range(par['D']):
                for i in range(par['N'][d]):
                    word_di = par['w'][d][i]
                    t_di = par['t'][d][i]

                    # initialise `m`, `n`, `n_sum`
                    old_topic = par['z'][d][i]
                    par['m'][d][old_topic] -= 1
                    par['n'][old_topic][word_di] -= 1
                    par['n_sum'][old_topic] -= 1

                    # formula from original paper, without the -1 operation
                    # removing the -1 operation should not impact the results too much
                    topic_probabilities = []
                    for topic_di in range(par['T']):
                        psi_di = par['psi'][topic_di] # psi is parameter of Beta distribution of time specific to topic
                        topic_probability = 1.0 * (par['m'][d][topic_di] + par['alpha'][topic_di]) #
                        topic_probability *= ((1-t_di)**(psi_di[0]-1)) * ((t_di)**(psi_di[1]-1))
                        topic_probability /= par['betafunc_psi'][topic_di]
                        topic_probability *= (par['n'][topic_di][word_di] + par['beta'][word_di])
                        topic_probability /= (par['n_sum'][topic_di] + par['beta_sum'])
                        topic_probabilities.append(topic_probability)
                    sum_topic_probabilities = sum(topic_probabilities)
                    if sum_topic_probabilities == 0:
                        topic_probabilities = [1.0/par['T'] for _ in range(par['T'])]
                    else:
                        topic_probabilities = [p/sum_topic_probabilities for p in topic_probabilities]
                    
                    # for each word, according to above probabilities of topic, randomly assign a new topic
                    new_topic = list(np.random.multinomial(1, topic_probabilities, size=1)[0]).index(1)
                    par['z'][d][i] = new_topic
                    par['m'][d][new_topic] += 1
                    par['n'][new_topic][word_di] += 1
                    par['n_sum'][new_topic] += 1
                
                # print an iteration status message for every 1000 iterations
                if d%1000 == 0:
                    print('Done with iteration {iteration} and document {document}'.format(iteration=iteration, document=d))
            
            par['psi'] = self.GetMethodOfMomentsEstimatesForPsi(par)
            par['betafunc_psi'] = [scipy.special.beta( par['psi'][t][0], par['psi'][t][1] ) for t in range(par['T'])]
        
        par['m'], par['n'] = self.ComputePosteriorEstimatesOfThetaAndPhi(par)
        
        return par['m'], par['n'], par['psi']