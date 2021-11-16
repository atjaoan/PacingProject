import itertools

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from sklearn.cluster import OPTICS
import os


class PacingProject:
    def __init__(self):
        self.df = pd.DataFrame()
        self.directory = 'Varvetresultat'
        self.files = os.listdir(self.directory)
        self.timeColumns = ['Time','5km','10km','15km','20km']
        self.relativePaces = ['5KmRelativePace', '10KmRelativePace', '15KmRelativePace', '20KmRelativePace',
                         '21KmRelativePace']
        self.boxLimits = [0.98,1.02]
        self.boxLimits.append(10)

    def MakeCSVs(self):

        #read and merge all results csvs
        for file in self.files:
            temp = pd.read_csv(self.directory+'/'+file, header=0, sep=";")
            #drop not used cols
            temp.drop(['ResultId','RaceId','CountryIso','County','Municipality','ActualStartTime','Place','PlaceClass','PlaceTotal'], axis=1, inplace=True)
            #drop not a number
            temp = temp.dropna()
            self.df = pd.concat([self.df, temp],ignore_index=True)
        #rename to easier names
        self.df = self.df.rename(columns={"RaceName":"Year","FinishNetto":"Time","_5Km":"5km","_10Km":"10km","_15Km": "15km", "_20Km": "20km"})

        #transform timestring to int of with number of seconds
        for timeColumn in self.timeColumns:
            self.df[timeColumn] = pd.to_timedelta(self.df[timeColumn])
            self.df[timeColumn] = self.df[timeColumn].dt.seconds

        #transform datatypes to int64 to avoid storing as float
        self.df['Year'] = self.df['Year'].str[-4:].astype(int)
        self.df['Year'] = self.df['Year'].astype("Int64")
        self.df['AthleteId'] = self.df['AthleteId'].astype("Int64")
        self.df['Birthyear'] = self.df['Birthyear'].astype("Int64")

        #save all results in file
        self.df.to_csv("AllResult.csv",index = False)


        #save everyone that has run all 10 races to smaller csv to use in testing
        self.df = self.df.groupby("AthleteId").filter(lambda x: len(x) > 9)
        self.df.to_csv("SmallTestResult.csv",index = False)


    def ReadLargeCsv(self): #read large file
        self.df = pd.read_csv('AllResult.csv')

    def ReadSmallTestCsv(self): #read small file
        self.df = pd.read_csv('SmallTestResult.csv')


    def AddPaces(self):
        self.df['5kmPace'] = (self.df['5km']/5)
        self.df['10kmPace'] = ((self.df['10km'] - self.df['5km']) / 5)
        self.df['15kmPace'] = ((self.df['15km'] - self.df['10km']) / 5)
        self.df['20kmPace'] = ((self.df['20km'] - self.df['15km']) / 5)
        self.df['21kmPace'] = ((self.df['Time'] - self.df['20km']) / 1.0975)
        self.df['TotalPace'] = (self.df['Time']/21.0975)

        self.df['5KmRelativePace'] = self.df['5kmPace']/self.df['TotalPace']
        self.df['10KmRelativePace'] = self.df['10kmPace']/self.df['TotalPace']
        self.df['15KmRelativePace'] = self.df['15kmPace']/self.df['TotalPace']
        self.df['20KmRelativePace'] = self.df['20kmPace']/self.df['TotalPace']
        self.df['21KmRelativePace'] = self.df['21kmPace']/self.df['TotalPace']

    def RemoveFaultyData(self):


        print('Removing data containg errors')

        pd.set_option("display.max_rows", None, "display.max_columns", None,'display.expand_frame_repr', False)
        #print(str((self.df['Time'] == 0).sum())+' runners with 00:00:00 as finish time')
        #print(self.df[self.df['Time'] == 0])
        self.df = self.df[self.df['Time'] != 0]


        #print('std of last km relative pace')
        #print(np.std(self.df['21KmRelativePace']))


        #print(str((self.df['21KmRelativePace'] > 3).sum())+' runners with 3xslowdown 20-21km')
        #print(self.df[self.df['21KmRelativePace'] > 3])
        self.df = self.df[self.df['21KmRelativePace'] < 3]

        #print(str((self.df['20KmRelativePace'] > 3).sum())+' runners with 3xslowdown 15-20km')
        #print(self.df[self.df['20KmRelativePace'] > 3])

        #print(str((self.df['15KmRelativePace'] > 3).sum())+' runners with 3xslowdown 10-15km')
        #print(self.df[self.df['15KmRelativePace'] > 3])

        #print(str((self.df['10KmRelativePace'] > 3).sum())+' runners with 3xslowdown 5-10km')
        #print(self.df[self.df['10KmRelativePace'] > 3])

        #print(str((self.df['5KmRelativePace'] > 3).sum())+' runners with 3xslowdown 0-5km')
        #print(self.df[self.df['5KmRelativePace'] > 3])


    def PrintStat(self,groupBy,):
        pass


    def ShowDistributions(self):

        #All
        fig, axs = plt.subplots(5, 1)
        for ax,relativePace in zip(axs,self.relativePaces):
            ax.hist(self.df[relativePace],bins=200,range=[0.75,1.25])
        plt.tight_layout()

        #Split on gender
        fig, axs = plt.subplots(5, 1)
        masks = [(self.df['Gender'] == 'M'),(self.df['Gender'] == 'F')]
        colors = ['r','b']
        for ax,relativePace in zip(axs,self.relativePaces):

            for color,mask in zip(colors,masks):
                ax.hist(self.df[mask][relativePace],bins=200,range=[0.75,1.25],histtype='step',color=color,density=1)
        plt.tight_layout()

        #Split on age
        fig, axs = plt.subplots(5, 1)
        masks = [(self.df['Year'] - self.df['Birthyear'] > 20) & (self.df['Year'] - self.df['Birthyear'] > 29),(self.df['Year'] - self.df['Birthyear'] > 30) & (self.df['Year'] - self.df['Birthyear'] > 39),(self.df['Year'] - self.df['Birthyear'] > 40) & (self.df['Year'] - self.df['Birthyear'] > 49),(self.df['Year'] - self.df['Birthyear'] > 50) & (self.df['Year'] - self.df['Birthyear'] > 100)]
        colors = [(0.0, 0.0, 0.0),(0.5, 0.0, 0.0),(1.0, 0.0, 0.0),(1.0, 0.5, 0.5)]
        for ax,relativePace in zip(axs,self.relativePaces):

            for color,mask in zip(colors,masks):
                ax.hist(self.df[mask][relativePace],bins=200,range=[0.75,1.25],histtype='step',color=color,density=1)
        plt.tight_layout()


        #Split on racetime
        fig, axs = plt.subplots(5, 1)
        masks = [(self.df['Time'] < 5400),(self.df['Time'] > 5401) & (self.df['Time'] < 7200),(self.df['Time'] > 7201) & (self.df['Time'] < 9000),(self.df['Time'] > 9000)]
        colors = [(0.0, 0.0, 0.0),(0.5, 0.0, 0.0),(1.0, 0.0, 0.0),(1.0, 0.5, 0.5)]
        for ax,relativePace in zip(axs,self.relativePaces):

            for color,mask in zip(colors,masks):
                ax.hist(self.df[mask][relativePace],bins=200,range=[0.75,1.25],histtype='step',color=color,density=1)
        plt.tight_layout()


        #hot years 2010,2013
        #Split on racetime
        fig, axs = plt.subplots(5, 1)
        masks = [(self.df['Year'] == 2010) | (self.df['Year'] == 2013),(self.df['Year'] != 2010) & (self.df['Year'] != 2013)]
        colors = ['r','b']
        for ax,relativePace in zip(axs,self.relativePaces):

            for color,mask in zip(colors,masks):
                ax.hist(self.df[mask][relativePace],bins=200,range=[0.75,1.25],histtype='step',color=color,density=1)
        plt.tight_layout()
        plt.show()


    def PaceClassification(self):

        '''
        X = self.df[self.relativePaces]
        kmeans = KMeans(n_clusters=3, random_state=0).fit(X)
        print('KMeans clusters')
        print(kmeans.cluster_centers_)

        distorsions = []
        for k in range(2, 10):
            print(k)
            kmeans = KMeans(n_clusters=k)
            kmeans.fit(X)
            distorsions.append(kmeans.inertia_)

        plt.plot(range(2, 10), distorsions)
        plt.title('Elbow curve')
        plt.show()
        '''


        combinations = list(itertools.product(range(len(self.boxLimits)), repeat=len(self.relativePaces)))

        pacingStrategyDict = {}
        cumSum = 0

        for combination in combinations:
            temp = self.df
            keyString = ''

            for (itemIndex,item) in enumerate(combination):
                previousLimit = 0


                for (boxIndex,limit) in enumerate(self.boxLimits):

                    if item == boxIndex:
                        if boxIndex == 0:
                            keyString += '<'+ str(limit)
                        elif boxIndex == len(self.boxLimits)-1:
                            keyString += '>'+ str(previousLimit)
                        else:
                            keyString += str(previousLimit)+'-'+str(limit)

                        temp = temp[temp[self.relativePaces[itemIndex]] > previousLimit]
                        temp = temp[temp[self.relativePaces[itemIndex]] <= limit]

                    previousLimit = limit
                keyString += '  '

            pacingStrategyDict[keyString] = len(temp)

        print(sorted(pacingStrategyDict, key=pacingStrategyDict.get, reverse=True))


        '''
        db = DBSCAN(eps=0.05, min_samples=2*5).fit(X)
        labels = db.labels_
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise_ = list(labels).count(-1)

        print("Estimated number of clusters: %d" % n_clusters_)
        print("Estimated number of noise points: %d" % n_noise_)
        '''


if __name__ == "__main__":
    PacingProject = PacingProject()
    #PacingProject.MakeCSVs()       #Run too make a csv of all races in directory with renamed columns and a smaller with all runners that have completed all races
    #PacingProject.ReadSmallTestCsv()
    PacingProject.ReadLargeCsv()
    PacingProject.AddPaces()
    PacingProject.RemoveFaultyData()
    PacingProject.ShowDistributions()
    #PacingProject.PaceClassification()