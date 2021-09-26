# CS760_2021S2_PA4

## Introduction
This is a course project of the University of Auckland CS760, semester 2, 2021

## Topic
**Company Relationship Mining Using Tweets: Competitors in Makeup Industry**

## Team members:
- Felix Wang (xwan975)
- Irabella Lin (zlin326)
- Kelvin Jin (ljin892)
- Zixin Kuang (zkua236)

## Data
### Data scraping
Our original data was scraped from Twitter using Twints. We have the data uploaded to Kaggle.
http://www.kaggle.com/dataset/afd5764f5a01f154fb8bf42576454e22610256dfd65c0897920d6630f95841fd

### Data preprocessing
We used bash code to 
1. merge data from different files
2. delete non-English tweets
3. remove duplicates
4. sort by create time
5. delete all other columns except create time and Tweets

We used python to 
1. keep alphabet and numeric character only

## Tools
### Data scraping
Twint: https://github.com/twintproject/twint
