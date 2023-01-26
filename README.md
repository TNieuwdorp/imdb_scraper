# imdb_scraper
Scrapes the imdb pages of a series, and creates a plot with the episode score. This allows an easy view of the score over time, showing if it gets bad or worse.

Installation is easy through poetry, using python 3.11.

The crawler can be run by setting the imdb url in imdb_scraper.py and then executing the command `scrapy crawl imdb` from `<root>/imdb/`. This outputs a png with the scores such as this one for the show Friends: ![image](https://user-images.githubusercontent.com/9988640/214955093-4038b1d4-ca90-4433-865a-649476779836.png)
